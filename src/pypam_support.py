from typing import cast, List, Optional, Tuple

import numpy as np
import pypam.signal as sig

import xarray as xr
from pypam import utils

# Approximate "flat" sensitivity of the hydrophone
APPROX_FLAT_SENSITIVITY = 178


class PypamSupport:
    def __init__(
        self, fs: int, nfft: int = 0, subset_to: Optional[Tuple[int, int]] = None
    ):
        """
        :param fs:
        :param nfft:
        :param subset_to: Actually, `band` but different name while pypam is fixed
        """
        self.fs = fs
        self.nfft = nfft if nfft > 0 else self.fs

        self.subset_to = subset_to
        band = [0, self.fs / 2]  # for now.
        print(f"PypamSupport: subset_to={subset_to}  band={band}")

        self.bands_limits, self.bands_c = utils.get_hybrid_millidecade_limits(
            band=band, nfft=self.nfft
        )

        self.fbands: Optional[np.ndarray] = None
        self.spectra: List[np.ndarray] = []
        self.iso_minutes: List[str] = []

    def add_segment(self, data: np.ndarray, iso_minute: str):
        print(f"  add_segment: data.shape = {data.shape}")

        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        self.fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        self.spectra.append(spectrum)
        self.iso_minutes.append(iso_minute)

    def get_aggregated_milli_psd(self) -> xr.DataArray:
        # Convert the spectra to a datarray
        psd_da = xr.DataArray(
            data=self.spectra,
            coords={"iso_minute": self.iso_minutes, "frequency": self.fbands},
            dims=["iso_minute", "frequency"],
        )
        milli_psd = self.subset_result(psd_da)
        milli_psd = cast(xr.DataArray, 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY)
        milli_psd.name = "psd"

        self.iso_minutes = []
        return milli_psd

    def get_milli_psd(self, data: np.ndarray, iso_minute: str) -> xr.DataArray:
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
            coords={"iso_minute": [iso_minute], "frequency": fbands},
            dims=["iso_minute", "frequency"],
        )

        milli_psd = self.subset_result(psd_da)
        milli_psd = cast(xr.DataArray, 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY)
        milli_psd.name = "psd"
        return milli_psd

    def subset_result(self, da: xr.DataArray) -> xr.DataArray:
        if self.subset_to is None:
            return da

        print(f"\nsubsetting to {self.subset_to}")
        bands_c = self.bands_c
        bands_limits = self.bands_limits

        start_hz, end_hz = self.subset_to
        start_index = 0
        while bands_c[start_index] < start_hz:
            start_index += 1
        end_index = start_index
        while bands_c[end_index - 1] < end_hz:
            end_index += 1
        bands_c = bands_c[start_index:end_index]
        new_bands_c_len = len(bands_c)
        bands_limits = bands_limits[start_index : start_index + new_bands_c_len + 1]

        def print_array(name: str, arr: np.ndarray):
            print(f"{name} ({len(arr)}) = {arr[:3]} ... {arr[-5:]}")

        print_array("       bands_c", bands_c)
        print_array("  bands_limits", bands_limits)

        return utils.spectra_ds_to_bands(
            da,
            bands_limits,
            bands_c,
            fft_bin_width=self.fs / self.nfft,
            db=False,
        )
