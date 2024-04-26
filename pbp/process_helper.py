import pathlib
from dataclasses import dataclass
from datetime import datetime, timezone

from typing import Any, List, Optional, OrderedDict, Tuple

import numpy as np
import xarray as xr

from pbp import get_pbp_version, get_pypam_version
from pbp.file_helper import FileHelper
from pbp.metadata import MetadataHelper, parse_attributes, replace_snippets
from pbp.misc_helper import gen_hour_minute_times, parse_date
from pbp.pypam_support import ProcessResult, PypamSupport


@dataclass
class ProcessDayResult:
    """
    The result returned from `process_day`.

    Contains the list of paths to generated files
    (NetCDF and others depending on given parameters)
    as well as the generated dataset.
    """

    generated_filenames: list[str]
    dataset: xr.Dataset


class ProcessHelper:
    def __init__(
        self,
        log,  # : loguru.Logger,
        file_helper: FileHelper,
        output_dir: str,
        output_prefix: str,
        gen_netcdf: bool = True,
        global_attrs_uri: Optional[str] = None,
        set_global_attrs: Optional[list[list[str]]] = None,
        variable_attrs_uri: Optional[str] = None,
        voltage_multiplier: Optional[float] = None,
        sensitivity_uri: Optional[str] = None,
        sensitivity_flat_value: Optional[float] = None,
        max_segments: int = 0,
        subset_to: Optional[Tuple[int, int]] = None,
    ):
        """

        :param file_helper:
            File loader.
        :param output_dir:
            Output directory.
        :param output_prefix:
            Output filename prefix.
        :param gen_netcdf:
            True to generate the netCDF file.
        :param global_attrs_uri:
            URI of JSON file with global attributes to be added to the NetCDF file.
        :param set_global_attrs:
            List of [key, value] pairs to be considered for the global attributes.
        :param variable_attrs_uri:
            URI of JSON file with variable attributes to be added to the NetCDF file.
        :param voltage_multiplier:
            Applied on the loaded signal.
        :param sensitivity_uri:
            URI of sensitivity NetCDF for calibration of result.
            Has precedence over `sensitivity_flat_value`.
        :param sensitivity_flat_value:
            Flat sensitivity value to be used for calibration.
        :param max_segments:
            Maximum number of segments to process for each day.
            By default, 0 (no limit).
        :param subset_to:
            Tuple of (lower, upper) frequency limits to use for the PSD,
            lower inclusive, upper exclusive.
        """
        self.log = log

        self.log.info(
            "Creating ProcessHelper:"
            + f"\n    output_dir:             {output_dir}"
            + f"\n    output_prefix:          {output_prefix}"
            + f"\n    gen_netcdf:             {gen_netcdf}"
            + f"\n    global_attrs_uri:       {global_attrs_uri}"
            + f"\n    set_global_attrs:       {set_global_attrs}"
            + f"\n    variable_attrs_uri:     {variable_attrs_uri}"
            + f"\n    voltage_multiplier:     {voltage_multiplier}"
            + f"\n    sensitivity_uri:        {sensitivity_uri}"
            + f"\n    sensitivity_flat_value: {sensitivity_flat_value}"
            + (
                f"\n    max_segments:           {max_segments}"
                if max_segments > 0
                else ""
            )
            + f"\n    subset_to:              {subset_to}"
            + "\n"
        )
        self.file_helper = file_helper
        self.output_dir = output_dir
        self.output_prefix = output_prefix
        self.gen_netcdf = gen_netcdf

        self.metadata_helper = MetadataHelper(
            self.log,
            self._load_attributes("global", global_attrs_uri, set_global_attrs),
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
                self.log.info(f"Will use loaded sensitivity from {s_local_filename=}")
                self.sensitivity_da = sensitivity_ds.sensitivity
                self.log.debug(f"{self.sensitivity_da=}")
            else:
                self.log.error(
                    f"Unable to resolve sensitivity_uri: '{sensitivity_uri}'. Ignoring it."
                )

        if self.sensitivity_da is None and self.sensitivity_flat_value is not None:
            self.log.info(
                f"Will use given flat sensitivity value: {sensitivity_flat_value}"
            )

        self.pypam_support = PypamSupport(self.log)

        pathlib.Path(output_dir).mkdir(exist_ok=True)

    def _load_attributes(
        self,
        what: str,
        attrs_uri: Optional[str],
        set_attrs: Optional[list[list[str]]] = None,
    ) -> Optional[OrderedDict[str, Any]]:
        if attrs_uri:
            self.log.info(f"Loading {what} attributes from {attrs_uri=}")
            filename = self.file_helper.get_local_filename(attrs_uri)
            if filename is not None:
                with open(filename, "r", encoding="UTF-8") as f:
                    res = parse_attributes(f.read(), pathlib.Path(filename).suffix)
                    for k, v in set_attrs or []:
                        res[k] = v
                    return res
            else:
                self.log.error(f"Unable to resolve '{attrs_uri=}'. Ignoring it.")
        else:
            self.log.info(f"No '{what}' attributes URI given.")
        return None

    def process_day(self, date: str) -> Optional[ProcessDayResult]:
        """
        Generates NetCDF file with the result of processing all segments of the given day.

        :param date:
            Date to process in YYYYMMDD format.
        :return:
            ProcessDayResult, or None if no segments at all were processed for the day.
        """
        year, month, day = parse_date(date)
        if not self.file_helper.select_day(year, month, day):
            return None

        at_hour_and_minutes: List[Tuple[int, int]] = list(
            gen_hour_minute_times(self.file_helper.segment_size_in_mins)
        )

        if self.max_segments > 0:
            at_hour_and_minutes = at_hour_and_minutes[: self.max_segments]
            self.log.info(f"NOTE: Limiting to {len(at_hour_and_minutes)} segments ...")

        self.process_hours_minutes(at_hour_and_minutes)

        result: Optional[ProcessResult] = self.pypam_support.process_captured_segments(
            sensitivity_da=self.sensitivity_da,
        )

        if result is None:
            self.log.warning(
                f"No segments processed, nothing to aggregate for day {date}."
            )
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

        ds_result = xr.Dataset(
            data_vars=data_vars,
            attrs=self._get_global_attributes(year, month, day),
        )

        generated_filenames = []
        basename = f"{self.output_dir}/{self.output_prefix}{year:04}{month:02}{day:02}"

        if self.gen_netcdf:
            nc_filename = f"{basename}.nc"
            save_dataset_to_netcdf(self.log, ds_result, nc_filename)
            generated_filenames.append(nc_filename)

        self.file_helper.day_completed()

        return ProcessDayResult(generated_filenames, ds_result)

    def process_hours_minutes(self, hour_and_minutes: List[Tuple[int, int]]):
        self.log.info(f"Processing {len(hour_and_minutes)} segments ...")
        for at_hour, at_minute in hour_and_minutes:
            self.process_segment_at_hour_minute(at_hour, at_minute)

    def process_segment_at_hour_minute(self, at_hour: int, at_minute: int):
        file_helper = self.file_helper
        year, month, day = file_helper.year, file_helper.month, file_helper.day
        assert year is not None and month is not None and day is not None

        dt = datetime(year, month, day, at_hour, at_minute, tzinfo=timezone.utc)

        self.log.debug(
            f"Segment at {at_hour:02}h:{at_minute:02}m ...\n"
            + f"  - extracting {file_helper.segment_size_in_mins * 60}-sec segment:"
        )
        extraction = file_helper.extract_audio_segment(at_hour, at_minute)
        if extraction is None:
            self.log.warning(f"cannot get audio segment at {at_hour:02}:{at_minute:02}")
            self.pypam_support.add_missing_segment(dt)
            return

        audio_info, audio_segment = extraction

        if self.pypam_support.parameters_set:
            if self.pypam_support.fs != audio_info.samplerate:
                self.log.info(
                    f"ERROR: samplerate changed from {self.pypam_support.fs} to {audio_info.samplerate}"
                )
                return
        else:
            self.log.info("Got audio parameters")
            self.pypam_support.set_parameters(
                audio_info.samplerate,
                subset_to=self.subset_to,
            )

        if self.voltage_multiplier is not None:
            audio_segment *= self.voltage_multiplier

        if self.sensitivity_flat_value is not None:
            # convert signal to uPa
            audio_segment = audio_segment * 10 ** (self.sensitivity_flat_value / 20)

        self.pypam_support.add_segment(dt, audio_segment)

    def _get_global_attributes(self, year: int, month: int, day: int):
        coverage_date = f"{year:04}-{month:02}-{day:02}"
        global_attrs = {
            "time_coverage_start": f"{coverage_date} 00:00:00Z",
            "time_coverage_end": f"{coverage_date} 23:59:00Z",
            "date_created": datetime.utcnow().strftime("%Y-%m-%d"),
        }
        md_helper = self.metadata_helper
        md_helper.set_some_global_attributes(global_attrs)
        snippets = {
            "{{PBP_version}}": get_pbp_version(),
            "{{PyPAM_version}}": get_pypam_version(),
        }
        global_attrs = md_helper.get_global_attributes()
        # for each, key, have the {{key}} snippet for replacement
        # in case it is used in any values:
        for k, v in global_attrs.items():
            snippets["{{" + k + "}}"] = v
        return replace_snippets(global_attrs, snippets)


def save_dataset_to_netcdf(
    log,  #: loguru.Logger,
    ds: xr.Dataset,
    filename: str,
) -> bool:
    log.info(f"  - saving dataset to: {filename}")
    try:
        ds.to_netcdf(
            filename,
            engine="h5netcdf",
            encoding={
                "effort": {"_FillValue": None},
                "frequency": {"_FillValue": None},
                "sensitivity": {"_FillValue": None},
            },
        )
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        error = f"Unable to save {filename}: {e}"
        log.error(error)
        print(error)
        return False
