import pathlib
import os
import loguru
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


DEFAULT_QUALITY_FLAG_VALUE = 2


@dataclass
class ProcessDayResult:
    """
    The result returned from `process_day`.
    Contains the list of paths to generated files
    (NetCDF and others depending on given parameters)
    as well as the generated dataset.

    Attributes:
        generated_filenames: List of paths to generated files
        dataset: The generated dataset
    """

    generated_filenames: list[str]
    dataset: xr.Dataset


class ProcessHelper:
    def __init__(
        self,
        log: "loguru.Logger",
        file_helper: FileHelper,
        output_dir: str,
        output_prefix: str,
        gen_netcdf: bool = True,
        compress_netcdf: bool = True,
        add_quality_flag: bool = False,
        global_attrs_uri: Optional[str] = None,
        set_global_attrs: Optional[list[list[str]]] = None,
        variable_attrs_uri: Optional[str] = None,
        exclude_tone_calibration_seconds: Optional[int] = None,
        voltage_multiplier: Optional[float] = None,
        sensitivity_uri: Optional[str] = None,
        sensitivity_flat_value: Optional[float] = None,
        max_segments: int = 0,
        subset_to: Optional[Tuple[int, int]] = None,
    ):
        """
        Initializes the processor.

        Args:
            file_helper: File loader.
            output_dir: Output directory.
            output_prefix: Output filename prefix.
            gen_netcdf (bool): Whether to generate the netCDF file.
            compress_netcdf (bool): Whether to compress the generated NetCDF file.
            add_quality_flag (bool): Whether to add a quality flag variable (with value 2 - "Not evaluated") to the NetCDF file.
            global_attrs_uri (str): URI of a JSON file with global attributes to be added to the NetCDF file.
            set_global_attrs (list[tuple[str, str]]): List of (key, value) pairs to be considered for the global attributes.
            variable_attrs_uri (str): URI of a JSON file with variable attributes to be added to the NetCDF file.
            exclude_tone_calibration_seconds (int): See https://github.com/mbari-org/pbp/issues/82
            voltage_multiplier (float): Factor applied to the loaded signal.
            sensitivity_uri (str, optional): URI of a sensitivity NetCDF file for calibration of results.
                Has precedence over `sensitivity_flat_value`.
            sensitivity_flat_value (float, optional): Flat sensitivity value used for calibration.
            max_segments (int, optional): Maximum number of segments to process for each day. Defaults to 0 (no limit).
            subset_to (tuple[float, float], optional): Frequency limits for the PSD (lower inclusive, upper exclusive).
        """
        self.log = log

        self.log.info(
            "Creating ProcessHelper:"
            + f"\n    output_dir:             {output_dir}"
            + f"\n    output_prefix:          {output_prefix}"
            + f"\n    gen_netcdf:             {gen_netcdf}"
            + f"\n    compress_netcdf:        {compress_netcdf}"
            + f"\n    add_quality_flag:       {add_quality_flag}"
            + f"\n    global_attrs_uri:       {global_attrs_uri}"
            + f"\n    set_global_attrs:       {set_global_attrs}"
            + f"\n    variable_attrs_uri:     {variable_attrs_uri}"
            + (
                f"\n    exclude_tone_calibration_seconds: {exclude_tone_calibration_seconds}"
                if exclude_tone_calibration_seconds is not None
                else ""
            )
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
        self.compress_netcdf = compress_netcdf
        self.add_quality_flag = add_quality_flag

        self.metadata_helper = MetadataHelper(
            self.log,
            self._load_attributes("global", global_attrs_uri, set_global_attrs),
            self._load_attributes("variable", variable_attrs_uri),
        )

        self.max_segments = max_segments
        self.subset_to = subset_to

        self.exclude_tone_calibration_seconds: Optional[
            int
        ] = exclude_tone_calibration_seconds
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
            if os.name == "nt" and filename is not None:
                filename = filename[3:]
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

        Args:
            date (str): Date to process in YYYYMMDD format.

        Returns:
            The result or None if no segments at all were processed for the day.
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

        if self.add_quality_flag:
            data_vars["quality_flag"] = xr.DataArray(
                data=np.full(psd_da.shape, DEFAULT_QUALITY_FLAG_VALUE, dtype=np.int8),
                dims=psd_da.dims,
                coords=psd_da.coords,
                # attrs are assigned below.
            )

        md_helper = self.metadata_helper

        md_helper.add_variable_attributes(psd_da["time"], "time")
        md_helper.add_variable_attributes(data_vars["effort"], "effort")
        md_helper.add_variable_attributes(psd_da["frequency"], "frequency")
        if "sensitivity" in data_vars:
            md_helper.add_variable_attributes(data_vars["sensitivity"], "sensitivity")
        if "quality_flag" in data_vars:
            md_helper.add_variable_attributes(data_vars["quality_flag"], "quality_flag")
        md_helper.add_variable_attributes(data_vars["psd"], "psd")

        ds_result = xr.Dataset(
            data_vars=data_vars,
            attrs=self._get_global_attributes(year, month, day),
        )

        generated_filenames = []
        basename = f"{self.output_dir}/{self.output_prefix}{year:04}{month:02}{day:02}"
        if os.name == "nt":
            basename = (
                f"{self.output_dir}\\{self.output_prefix}{year:04}{month:02}{day:02}"
            )

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
        extraction = file_helper.extract_audio_segment(
            at_hour, at_minute, self.exclude_tone_calibration_seconds
        )
        if extraction is None:
            self.log.warning(f"cannot get audio segment at {at_hour:02}:{at_minute:02}")
            self.pypam_support.add_missing_segment(dt)
            return

        audio_info = extraction.audio_info
        audio_segment = extraction.segment

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
    log: "loguru.Logger",
    ds: xr.Dataset,
    filename: str,
    compress_netcdf: bool = True,
) -> bool:
    """
    Saves the given dataset to a NetCDF file.

    Args:
        log (loguru.Logger): Logger.
        ds (xr.Dataset): Dataset to save.
        filename (str): Output filename.
        compress_netcdf (bool): Whether to compress the NetCDF file.

    Returns:
        True if the dataset was saved successfully, False otherwise.
    """
    log.info(f"  - saving dataset to: {filename}  (compressed: {compress_netcdf})")
    encoding: dict[Any, dict[str, Any]] = {
        "effort": {"_FillValue": None},
        "frequency": {"_FillValue": None},
        "sensitivity": {"_FillValue": None},
    }
    if compress_netcdf:
        for k in ds.data_vars:
            if ds[k].ndim < 2:
                continue
            encoding[k] = {
                "zlib": True,
                "complevel": 3,
                "fletcher32": True,
                "chunksizes": tuple(map(lambda x: x // 2, ds[k].shape)),
            }
    try:
        ds.to_netcdf(filename, format="NETCDF4", engine="h5netcdf", encoding=encoding)
        return True
    except Exception as e:  # pylint: disable=broad-exception-caught
        error = f"Unable to save {filename}: {e}"
        log.error(error)
        print(error)
        return False
