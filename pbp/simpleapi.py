from pbp.process_helper import ProcessHelper, ProcessDayResult
from pbp.file_helper import FileHelper
from pbp.logging_helper import create_logger
from typing import Optional
from botocore.client import BaseClient
from pbp.plotting import plot_dataset_summary
from pbp import get_pbp_version

from google.cloud.storage import Client as GsClient

import xarray as xr
import pandas as pd
import matplotlib.pyplot as plt


class HmbGen:
    """
    A high-level interface intended to simplify the usage of the package for common scenarios.
    This uses other API elements that can also be used directly for more control on the
    settings or more advanced scenarios.

    Here is a basic, schematic example of how to use this class:
    ```python
    # Create instance:
    hmb_gen = HmbGen()

    # Indicate parameters as needed:
    hmb_gen.set_json_base_dir("json")
    hmb_gen.set_global_attrs_uri("gs://bucket/globalAttributes.yaml")
    hmb_gen.set_variable_attrs_uri("gs://bucket/variableAttributes.yaml")
    hmb_gen.set_subset_to((0, 100))
    hmb_gen.set_download_dir("download")
    hmb_gen.set_output_dir("output")
    hmb_gen.set_output_prefix("hmb_")
    hmb_gen.set_add_quality_flag(True)
    hmb_gen.set_gs_client(gs_client)

    # Before processing, perform basic check of the parameters:
    errors = hmb_gen.check_parameters()
    if errors:
        print(f"Errors: {errors}")
    else:
        result = hmb_gen.process_date("20220101")
        if result:
            print(f"Result: {result}")
        hmb_gen.plot_date(
            "20220101",
            lat_lon_for_solpos=(37.7749, -122.4194),
            title="HMB",
            ylim=(0, 100),
            cmlim=(0, 100),
            dpi=300,
            show=True,
        )
    ```
    """

    def __init__(self) -> None:
        """
        Create a new object for HMB generation.
        On the created instance, call the various `set_*` methods to set the parameters,
        `check_parameters()` to verify the parameters, and
        then call `process_date()` to execute the process for a given date.

        See source code for more details on the default parameter values.
        """
        self._json_base_dir: str = ""
        self._global_attrs_uri: str = ""
        self._variable_attrs_uri: str = ""
        self._exclude_tone_calibration_seconds: Optional[int] = None
        self._voltage_multiplier: float = 1.0
        self._sensitivity: float | str = 1.0
        self._subset_to: Optional[tuple[int, int]] = None
        self._download_dir: str = ""
        self._output_dir: str = ""
        self._output_prefix: str = ""
        self._compress_netcdf: bool = True
        self._add_quality_flag: bool = False

        self._assume_downloaded_files: bool = False
        self._retain_downloaded_files: bool = False
        self._print_downloading_lines: bool = False

        # Other attributes
        self._s3_client: Optional[BaseClient] = None
        self._gs_client: Optional[GsClient] = None

        self._hmb_gen: Optional[_HmbGen] = None

    def set_json_base_dir(self, json_base_dir: str) -> None:
        """
        Set the base directory where JSON files are located.

        Args:
            json_base_dir (str): The base directory where JSON files are located.
        """
        self._json_base_dir = json_base_dir

    def set_global_attrs_uri(self, global_attrs_uri: str) -> None:
        """
        Set the URI for global attributes.

        Args:
            global_attrs_uri (str): The URI for global attributes.
        """
        self._global_attrs_uri = global_attrs_uri

    def set_variable_attrs_uri(self, variable_attrs_uri: str) -> None:
        """
        Set the URI for variable attributes.

        Args:
            variable_attrs_uri (str): The URI for variable attributes.
        """
        self._variable_attrs_uri = variable_attrs_uri

    def set_exclude_tone_calibration_seconds(
        self, exclude_tone_calibration_seconds: int
    ) -> None:
        """
        Set the number of seconds to exclude from each input audio file.
        The resulting 'effort' data array is affected accordingly.

        See https://github.com/mbari-org/pbp/issues/82

        Args:
            exclude_tone_calibration_seconds (int): The number of seconds to exclude from each input audio file.
        """
        self._exclude_tone_calibration_seconds = exclude_tone_calibration_seconds

    def set_voltage_multiplier(self, voltage_multiplier: float) -> None:
        """
        If voltage range is not from -1 to 1, then use this method
        to specify 1/2 peak-to-peak voltage.

        Args:
            voltage_multiplier (float): The voltage multiplier.
        """
        self._voltage_multiplier = voltage_multiplier

    def set_sensitivity(self, sensitivity: float | str) -> None:
        """
        Set sensitivity for calibration of result.

        The argument can be a flat value (a float), or URI of sensitivity file.

        - For flat value, the value should be positive.
        - For URI, the values should be negative.

        Args:
            sensitivity (float | str): Sensitivity flat value (a float), or URI of sensitivity file.
        """
        self._sensitivity = sensitivity

    def set_subset_to(self, subset_to: tuple[int, int]) -> None:
        """
        Set the frequency subset to use for the PSD.

        Args:
            subset_to (tuple[int, int]): Tuple of (lower, upper), with lower inclusive, upper exclusive.
        """
        self._subset_to = subset_to

    def set_download_dir(self, download_dir: str) -> None:
        """
        Set the download directory.

        Args:
            download_dir (str): The download directory.
        """
        self._download_dir = download_dir

    def set_output_dir(self, output_dir: str) -> None:
        """
        Set the output directory.

        Args:
            output_dir (str): The output directory.
        """
        self._output_dir = output_dir

    def set_output_prefix(self, output_prefix: str) -> None:
        """
        Set the output prefix.

        Args:
            output_prefix (str): The output prefix.
        """
        self._output_prefix = output_prefix

    def set_compress_netcdf(self, compress_netcdf: bool) -> None:
        """
        Set whether to compress the NetCDF file.
        This is done by default.

        Args:
            compress_netcdf (bool): Whether to compress the NetCDF file.
        """
        self._compress_netcdf = compress_netcdf

    def set_add_quality_flag(self, add_quality_flag: bool) -> None:
        """
        Set whether to add quality flag variable (with value fixed to 2 - "Not evaluated") to the NetCDF file.
        This is not done by default.

        Args:
            add_quality_flag (bool): Whether to add quality flag variable.
        """
        self._add_quality_flag = add_quality_flag

    def set_assume_downloaded_files(self, value: bool) -> None:
        """
        Set whether to skip downloading files that already exist in the download directory.
        This is not done by default.

        Args:
            value:
                If True, skip downloading files that already exist in the download directory.
        """
        self._assume_downloaded_files = value

    def set_retain_downloaded_files(self, value: bool) -> None:
        """
        Set whether to retain downloaded files after use.
        This is not done by default.

        Args:
            value:
                If True, do not remove downloaded files after use.
        """
        self._retain_downloaded_files = value

    def set_print_downloading_lines(self, value: bool) -> None:
        """
        Set whether to print "downloading <uri>" lines to console.
        This is not done by default.

        Args:
            value:
                If True, print "downloading <uri>" lines to console.
        """
        self._print_downloading_lines = value

    def set_s3_client(self, s3_client: BaseClient) -> None:
        """
        Set the S3 client.

        Args:
            s3_client (BaseClient): The S3 client.
        """
        if self._gs_client:
            raise ValueError("A GS client has already been set.")
        self._s3_client = s3_client

    def set_gs_client(self, gs_client: GsClient) -> None:
        """
        Set the GS client.

        Args:
            gs_client (GsClient): The GS client.
        """
        if self._s3_client:
            raise ValueError("A S3 client has already been set.")
        self._gs_client = gs_client

    def check_parameters(self) -> str | None:
        """
        Performs a basic check of the parameters,
        especially verifying that the required ones are given.
        Call this before performing any processing.

        Returns:
            None if no errors, otherwise a string with the errors.
        """
        errors = []

        if not self._json_base_dir:
            errors.append("- json_base_dir not set")

        if not self._global_attrs_uri:
            errors.append("- global_attrs_uri not set")

        if not self._variable_attrs_uri:
            errors.append("- variable_attrs_uri not set")

        if not self._download_dir:
            errors.append("- download_dir not set")

        if not self._output_dir:
            errors.append("- output_dir not set")

        if not self._subset_to:
            errors.append("- subset_to not set")

        if not self._sensitivity:
            errors.append("- sensitivity not set.")
        elif not isinstance(self._sensitivity, (float, int, str)):
            errors.append("- sensitivity must be a number or a string")

        if not isinstance(self._subset_to, tuple):
            errors.append("- subset_to must be a tuple")
        else:
            if len(list(self._subset_to)) != 2:
                errors.append("- subset_to must be a tuple of length 2")
            if not isinstance(self._subset_to[0], int) or not isinstance(
                self._subset_to[1], int
            ):
                errors.append("- subset_to must contain integers")

        if not self._s3_client and not self._gs_client:
            errors.append("- No S3 or GS client has been set")

        if len(errors) > 0:
            return "\n".join(errors)

        # make mypy happy
        assert isinstance(self._subset_to, tuple)

        self._hmb_gen = _HmbGen(
            json_base_dir=self._json_base_dir,
            global_attrs_uri=self._global_attrs_uri,
            variable_attrs_uri=self._variable_attrs_uri,
            exclude_tone_calibration_seconds=self._exclude_tone_calibration_seconds,
            voltage_multiplier=self._voltage_multiplier,
            sensitivity=self._sensitivity,
            subset_to=self._subset_to,
            download_dir=self._download_dir,
            output_dir=self._output_dir,
            output_prefix=self._output_prefix,
            compress_netcdf=self._compress_netcdf,
            add_quality_flag=self._add_quality_flag,
            assume_downloaded_files=self._assume_downloaded_files,
            retain_downloaded_files=self._retain_downloaded_files,
            print_downloading_lines=self._print_downloading_lines,
            s3_client=self._s3_client,
            gs_client=self._gs_client,
        )
        return None

    def process_date(self, date: str) -> ProcessDayResult | str:
        """
        Generates NetCDF file with the result of processing all segments of the given day.

        Args:
            date (str): Date to process in YYYYMMDD format.

        Returns:
            ProcessDayResult if segments were processed, otherwise a string with an error.
        """
        if not self._hmb_gen:
            return "Missing or invalid parameters. Call check_parameters() first."

        result = self._hmb_gen.process_date(date)
        return result or f"No segments processed for {date}."

    def plot_date(
        self,
        date: str,
        lat_lon_for_solpos: tuple[float, float],
        title: str,
        ylim: tuple[int, int],
        cmlim: tuple[int, int],
        dpi: int,
        show: bool = False,
    ) -> None:
        """
        Generate a summary plot for the given date.
        Make sure the NetCDF file for the given date has been generated first.
        The output will be saved as a JPEG file with name derived from the input date
        resulting in a sibling file to the NetCDF file.

        Args:
            date (str): Date to plot in `YYYYMMDD` format.
            lat_lon_for_solpos (tuple[float, float]): Latitude and longitude for solar position calculation.
            title (str, optional): Title for the plot.
            ylim (tuple[float, float], optional): Limits for the y-axis.
            cmlim (tuple[float, float], optional): Limits passed to `pcolormesh`.
            dpi (int, optional): DPI to use for the plot.
            show (bool, optional): Whether to also show the plot. Defaults to `False`, meaning only the JPEG file is generated.
        """
        if not self._hmb_gen:
            raise ValueError(
                "Missing or invalid parameters. Call check_parameters() first."
            )

        return self._hmb_gen.plot_date(
            date,
            lat_lon_for_solpos,
            title,
            ylim,
            cmlim,
            dpi,
            show,
        )


def _version() -> str:
    return f"pbp v{get_pbp_version()}: "


class _HmbGen:
    def __init__(
        self,
        json_base_dir: str,
        global_attrs_uri: str,
        variable_attrs_uri: str,
        exclude_tone_calibration_seconds: Optional[int],
        voltage_multiplier: float,
        sensitivity: float | str,
        subset_to: tuple[int, int],
        download_dir: str,
        output_dir: str,
        output_prefix: str,
        compress_netcdf: bool,
        add_quality_flag: bool,
        assume_downloaded_files: bool,
        retain_downloaded_files: bool,
        print_downloading_lines: bool,
        s3_client: Optional[BaseClient],
        gs_client: Optional[GsClient],
    ) -> None:
        self.json_base_dir = json_base_dir
        self.global_attrs_uri = global_attrs_uri
        self.variable_attrs_uri = variable_attrs_uri
        self.exclude_tone_calibration_seconds = exclude_tone_calibration_seconds
        self.voltage_multiplier = voltage_multiplier
        self.subset_to = subset_to

        self.sensitivity_uri: Optional[str] = None
        self.sensitivity_flat_value: Optional[float] = None
        if isinstance(sensitivity, str):
            self.sensitivity_uri = sensitivity
        else:
            self.sensitivity_flat_value = sensitivity

        self.download_dir = download_dir
        self.output_dir = output_dir
        self.output_prefix = output_prefix
        self.compress_netcdf = compress_netcdf
        self.add_quality_flag = add_quality_flag

        self.assume_downloaded_files = assume_downloaded_files
        self.retain_downloaded_files = retain_downloaded_files
        self.print_downloading_lines = print_downloading_lines

        # Other attributes
        self.s3_client = s3_client
        self.gs_client = gs_client

        # -----------------------------------------------------
        # Reset plotting overrides set in pypam
        # (these cause the PBP plot_dataset_summary function to fail
        # https://github.com/mbari-org/pbp/issues/21#issuecomment-2261642486)
        plt.rcParams.update({"text.usetex": False})
        pd.plotting.deregister_matplotlib_converters()

    def process_date(self, date: str) -> Optional[ProcessDayResult]:
        nc_filename = f"{self.output_dir}/{self.output_prefix}{date}.nc"

        print(f"{_version()}: Processing {date} to generate {nc_filename}...")

        log_filename = nc_filename.replace(".nc", ".log")
        log = create_logger(
            log_filename_and_level=(log_filename, "INFO"),
            console_level=None,
        )

        file_helper = FileHelper(
            log=log,
            json_base_dir=self.json_base_dir,
            s3_client=self.s3_client,
            gs_client=self.gs_client,
            download_dir=self.download_dir,
            assume_downloaded_files=self.assume_downloaded_files,
            retain_downloaded_files=self.retain_downloaded_files,
            print_downloading_lines=self.print_downloading_lines,
        )

        process_helper = ProcessHelper(
            log=log,
            file_helper=file_helper,
            output_dir=self.output_dir,
            output_prefix=self.output_prefix,
            compress_netcdf=self.compress_netcdf,
            add_quality_flag=self.add_quality_flag,
            global_attrs_uri=self.global_attrs_uri,
            variable_attrs_uri=self.variable_attrs_uri,
            exclude_tone_calibration_seconds=self.exclude_tone_calibration_seconds,
            voltage_multiplier=self.voltage_multiplier,
            sensitivity_uri=self.sensitivity_uri,
            sensitivity_flat_value=self.sensitivity_flat_value,
            subset_to=self.subset_to,
        )

        # now, get the HMB result:
        print(f"::: Started processing {date=}")
        result = process_helper.process_day(date)
        print(f":::   Ended processing {date=} =>  {nc_filename=}")
        return result

    def plot_date(
        self,
        date: str,
        lat_lon_for_solpos: tuple[float, float],
        title: str,
        ylim: tuple[int, int],
        cmlim: tuple[int, int],
        dpi: int,
        show: bool = False,
    ) -> None:
        nc_filename = f"{self.output_dir}/{self.output_prefix}{date}.nc"
        jpeg_filename = nc_filename.replace(".nc", ".jpg")

        ds = xr.open_dataset(nc_filename, engine="h5netcdf")
        plot_dataset_summary(
            ds,
            lat_lon_for_solpos=lat_lon_for_solpos,
            title=title,
            ylim=ylim,
            cmlim=cmlim,
            dpi=dpi,
            jpeg_filename=jpeg_filename,
            show=show,
        )
