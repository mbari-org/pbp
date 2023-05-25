from datetime import datetime
from typing import cast, List, Optional, Tuple

import numpy as np
import pypam.signal as sig

import xarray as xr
from pypam import utils

from src.misc_helper import brief_list, debug, info


class PypamSupport:
    def __init__(
        self, fs: int, nfft: int = 0, subset_to: Optional[Tuple[int, int]] = None
    ):
        """
        :param fs:
        :param nfft:
        :param subset_to:
        """
        self.fs = fs
        self.nfft = nfft if nfft > 0 else self.fs

        self.subset_to = subset_to
        band = [0, self.fs / 2]  # for now.

        debug(f"PypamSupport: {subset_to=} {band=}")

        self.bands_limits, self.bands_c = utils.get_hybrid_millidecade_limits(
            band=band, nfft=self.nfft
        )

        self.fbands: Optional[np.ndarray] = None
        self.spectra: List[np.ndarray] = []
        self.iso_minutes: List[datetime] = []
        self.num_secs_per_minute: List[int] = []

    def add_segment(self, data: np.ndarray, dt: datetime):
        num_secs = int(len(data) / self.fs)
        info(f"  adding segment: {dt} ({num_secs} secs used)")

        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        self.fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        self.spectra.append(spectrum)
        self.iso_minutes.append(dt)
        self.num_secs_per_minute.append(num_secs)

    def get_aggregated_milli_psd(
        self,
        sensitivity_da: Optional[xr.DataArray] = None,
        sensitivity_flat_value: Optional[float] = None,
    ) -> xr.DataArray:
        """
        Gets the resulting hybrid millidecade bands.
        Calibration is done if either `sensitivity_da` or `sensitivity_flat_value` is given.
        `sensitivity_da` has priority over `sensitivity_flat_value`.
        No calibration is done if neither is given.

        :param sensitivity_da:
            If given, it will be used to calibrate the result.
        :param sensitivity_flat_value:
            If given, and sensitivity_da not given, it will be used to calibrate the result.
        :return:
        """
        # Convert the spectra to a datarray
        psd_da = xr.DataArray(
            data=self.spectra,
            coords={"time": self.iso_minutes, "frequency": self.fbands},
            dims=["time", "frequency"],
        )

        psd_da = self.spectra_to_bands(psd_da)
        debug(f"  {psd_da.frequency_bins=}")
        psd_da = apply_sensitivity(psd_da, sensitivity_da, sensitivity_flat_value)

        # just need single precision:
        psd_da = psd_da.astype(np.float32)
        psd_da["frequency"] = psd_da.frequency_bins.astype(np.float32)
        del psd_da["frequency_bins"]

        milli_psd = psd_da
        milli_psd.name = "psd"

        info(f"Resulting milli_psd={milli_psd}")

        self.iso_minutes = []
        self.num_secs_per_minute = []
        return milli_psd

    def get_effort(self) -> List[int]:
        return self.num_secs_per_minute

    def get_milli_psd(
        self,
        data: np.ndarray,
        iso_minute: str,
        sensitivity_da: Optional[xr.DataArray] = None,
    ) -> xr.DataArray:
        """
        Convenience to get the millidecade bands for a single segment of data
        """
        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        # Convert the spectrum to a datarray
        psd_da = xr.DataArray(
            data=[spectrum],
            coords={"time": [iso_minute], "frequency": fbands},
            dims=["time", "frequency"],
        )

        psd_da = self.spectra_to_bands(psd_da)
        psd_da = apply_sensitivity(psd_da, sensitivity_da)

        milli_psd = psd_da
        milli_psd.name = "psd"
        return milli_psd

    def spectra_to_bands(self, psd_da: xr.DataArray) -> xr.DataArray:
        bands_limits, bands_c = self.bands_limits, self.bands_c
        if self.subset_to is not None:
            bands_limits, bands_c = adjust_limits(bands_limits, bands_c, self.subset_to)

        def print_array(name: str, arr: np.ndarray):
            info(f"{name} ({len(arr)}) = {brief_list(arr)}")

        print_array("       bands_c", bands_c)
        print_array("  bands_limits", bands_limits)

        psd_da = utils.spectra_ds_to_bands(
            psd_da,
            bands_limits,
            bands_c,
            fft_bin_width=self.fs / self.nfft,
            db=False,
        )

        psd_da = psd_da.drop_vars(["lower_frequency", "upper_frequency"])
        return psd_da


def apply_sensitivity(
    psd_da: xr.DataArray,
    sensitivity_da: Optional[xr.DataArray],
    sensitivity_flat_value: Optional[float] = None,
) -> xr.DataArray:
    psd_da = cast(xr.DataArray, 10 * np.log10(psd_da))

    # NOTE: per slack discussion today 2023-05-23,
    # apply _addition_ of the given sensitivity
    # (previously, subtraction)
    # TODO but this is still one pending aspect to finalize.

    if sensitivity_da is not None:
        freq_subset = sensitivity_da.interp(frequency=psd_da.frequency_bins)
        info(f"  Applying sensitivity({len(freq_subset.values)})={freq_subset}")
        psd_da += freq_subset.values
    elif sensitivity_flat_value is not None:
        info(f"  applying {sensitivity_flat_value=}")
        psd_da += sensitivity_flat_value

    return psd_da


def adjust_limits(
    bands_limits: List[float], bands_c: List[float], subset_to: Tuple[int, int]
) -> Tuple[List[float], List[float]]:
    start_hz, end_hz = subset_to
    info(f"Subsetting to [{start_hz:,}, {end_hz:,})Hz")

    start_index = 0
    while start_index < len(bands_c) and bands_c[start_index] < start_hz:
        start_index += 1
    end_index = start_index
    while end_index < len(bands_c) and bands_c[end_index] < end_hz:
        end_index += 1
    bands_c = bands_c[start_index:end_index]
    new_bands_c_len = len(bands_c)
    bands_limits = bands_limits[start_index : start_index + new_bands_c_len + 1]

    return bands_limits, bands_c
