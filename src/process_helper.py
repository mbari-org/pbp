import collections
import json
import pathlib
from datetime import datetime, timezone

from typing import Any, List, Optional, OrderedDict, Tuple

import numpy as np
import xarray as xr

from src import save_dataset_to_csv, save_dataset_to_netcdf

from src.file_helper import FileHelper
from src.metadata import MetadataHelper
from src.misc_helper import debug, error, gen_hour_minute_times, info, parse_date, warn
from src.pypam_support import ProcessResult, PypamSupport


class ProcessHelper:
    def __init__(
        self,
        file_helper: FileHelper,
        output_dir: str,
        output_prefix: str,
        gen_csv: bool,
        global_attrs_uri: Optional[str] = None,
        variable_attrs_uri: Optional[str] = None,
        voltage_multiplier: Optional[float] = None,
        sensitivity_uri: Optional[str] = None,
        sensitivity_flat_value: Optional[float] = None,
        max_segments: int = 0,
        subset_to: Optional[Tuple[int, int]] = None,
    ):
        """

        :param file_helper:
        :param output_dir:
        :param output_prefix:
        :param gen_csv:
        :param global_attrs_uri:
        :param variable_attrs_uri:
        :param voltage_multiplier:
        :param sensitivity_uri:
        :param sensitivity_flat_value:
        :param max_segments:
        :param subset_to:
            Tuple of (lower, upper) frequency limits to use for the PSD,
            lower inclusive, upper exclusive.
        """

        self.file_helper = file_helper
        self.output_dir = output_dir
        self.output_prefix = output_prefix
        self.gen_csv = gen_csv

        self.metadata_helper = MetadataHelper(
            self._load_attributes("global", global_attrs_uri),
            self._load_attributes("variable", variable_attrs_uri),
        )

        self.max_segments = max_segments
        self.subset_to = subset_to

        self.voltage_multiplier: Optional[float] = voltage_multiplier

        self.sensitivity_da: Optional[xr.DataArray] = None
        self.sensitivity_flat_value: Optional[float] = sensitivity_flat_value

        if sensitivity_uri is not None:
            s_local_filename = file_helper.get_local_filename(sensitivity_uri)
            if s_local_filename is not None:
                sensitivity_ds = xr.open_dataset(s_local_filename)
                info(f"Will use loaded sensitivity from {s_local_filename=}")
                self.sensitivity_da = sensitivity_ds.sensitivity
                debug(f"{self.sensitivity_da=}")
            else:
                error(
                    f"Unable to resolve sensitivity_uri: '{sensitivity_uri}'. Ignoring it."
                )

        if self.sensitivity_da is None and self.sensitivity_flat_value is not None:
            info(f"Will use given flat sensitivity value: {sensitivity_flat_value}")

        self.pypam_support = PypamSupport()

        pathlib.Path(output_dir).mkdir(exist_ok=True)

    def _load_attributes(
        self, what: str, attrs_uri: Optional[str]
    ) -> Optional[OrderedDict[str, Any]]:
        if attrs_uri:
            info(f"Loading {what} attributes from {attrs_uri=}")
            filename = self.file_helper.get_local_filename(attrs_uri)
            if filename is not None:
                with open(filename, "r", encoding="UTF-8") as f:
                    return json.load(f, object_pairs_hook=collections.OrderedDict)
            else:
                error(f"Unable to resolve '{attrs_uri=}'. Ignoring it.")
        else:
            info(f"No '{what}' attributes URI given.")
        return None

    def process_day(self, date: str) -> Optional[str]:
        """
        Generates NetCDF file with the result of processing all segments of the given day.

        :param date:
            Date to process in YYYYMMDD format.
        :return:
            The path of the generated NetCDF file, or None if no segments were processed
            for the day.
        """
        year, month, day = parse_date(date)
        if not self.file_helper.select_day(year, month, day):
            return None

        at_hour_and_minutes: List[Tuple[int, int]] = list(
            gen_hour_minute_times(self.file_helper.segment_size_in_mins)
        )

        if self.max_segments > 0:
            at_hour_and_minutes = at_hour_and_minutes[: self.max_segments]
            info(f"NOTE: Limiting to {len(at_hour_and_minutes)} segments ...")

        self.process_hours_minutes(at_hour_and_minutes)

        result: Optional[ProcessResult] = self.pypam_support.process_captured_segments(
            sensitivity_da=self.sensitivity_da,
            sensitivity_flat_value=self.sensitivity_flat_value,
        )

        if result is None:
            warn(f"No segments processed, nothing to aggregate for day {date}.")
            return None

        psd_da = result.psd_da

        # rename 'frequency_bins' dimension to 'frequency':
        psd_da = psd_da.swap_dims(frequency_bins="frequency")

        data_vars = {
            "psd": psd_da,
            "effort": result.effort_da,
        }

        if self.sensitivity_da is not None:
            freq_subset = self.sensitivity_da.interp(frequency=psd_da.frequency)
            data_vars["sensitivity"] = freq_subset

        elif self.sensitivity_flat_value is not None:
            # better way to capture a scalar?
            data_vars["sensitivity"] = xr.DataArray(
                data=[self.sensitivity_flat_value],
                dims=["1"],
            ).astype(np.float32)

        md_helper = self.metadata_helper

        md_helper.add_variable_attributes(psd_da["time"], "time")
        md_helper.add_variable_attributes(data_vars["effort"], "effort")
        md_helper.add_variable_attributes(psd_da["frequency"], "frequency")
        if "sensitivity" in data_vars:
            md_helper.add_variable_attributes(data_vars["sensitivity"], "sensitivity")
        md_helper.add_variable_attributes(data_vars["psd"], "psd")

        md_helper.set_global_attribute(
            "date_created", datetime.utcnow().strftime("%Y-%m-%d")
        )

        ds_result = xr.Dataset(
            data_vars=data_vars,
            attrs=md_helper.get_global_attributes(),
        )

        basename = f"{self.output_dir}/{self.output_prefix}{year:04}{month:02}{day:02}"
        nc_filename = f"{basename}.nc"
        save_dataset_to_netcdf(ds_result, nc_filename)
        if self.gen_csv:
            save_dataset_to_csv(ds_result, f"{basename}.csv")

        self.file_helper.day_completed()

        return nc_filename

    def process_hours_minutes(self, hour_and_minutes: List[Tuple[int, int]]):
        info(f"Processing {len(hour_and_minutes)} segments ...")
        for at_hour, at_minute in hour_and_minutes:
            self.process_segment_at_hour_minute(at_hour, at_minute)

    def process_segment_at_hour_minute(self, at_hour: int, at_minute: int):
        file_helper = self.file_helper
        year, month, day = file_helper.year, file_helper.month, file_helper.day
        assert year is not None and month is not None and day is not None

        dt = datetime(year, month, day, at_hour, at_minute, tzinfo=timezone.utc)

        info(f"Segment at {at_hour:02}h:{at_minute:02}m ...")
        info(f"  - extracting {file_helper.segment_size_in_mins * 60}-sec segment:")
        extraction = file_helper.extract_audio_segment(at_hour, at_minute)
        if extraction is None:
            warn(f"cannot get audio segment at {at_hour:02}:{at_minute:02}")
            self.pypam_support.add_missing_segment(dt)
            return

        audio_info, audio_segment = extraction

        if self.pypam_support.parameters_set():
            if self.pypam_support.fs != audio_info.samplerate:
                info(
                    f"ERROR: samplerate changed from {self.pypam_support.fs} to {audio_info.samplerate}"
                )
                return
        else:
            info("Got audio parameters")
            self.pypam_support.set_parameters(
                audio_info.samplerate,
                subset_to=self.subset_to,
            )

        if self.voltage_multiplier is not None:
            audio_segment *= self.voltage_multiplier

        self.pypam_support.add_segment(dt, audio_segment)
