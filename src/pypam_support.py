from typing import List, Optional

import numpy as np
import pypam.signal as sig

import xarray
from pypam import utils

# Approximate "flat" sensitivity of the hydrophone
APPROX_FLAT_SENSITIVITY = 178


class PypamSupport:
    def __init__(self, fs: int, nfft: int = 0):
        self.fs = fs
        self.nfft = nfft if nfft > 0 else self.fs
        self.bands_limits, self.bands_c = utils.get_hybrid_millidecade_limits(
            band=[0, self.fs / 2], nfft=self.nfft
        )

        self.fbands: Optional[np.ndarray] = None
        self.spectra: List[np.ndarray] = []

    def add_segment(self, data: np.ndarray):
        print(f"  add_segment: data.shape = {data.shape}")

        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        self.fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        self.spectra.append(spectrum)

    def get_aggregated_milli_psd(self) -> xarray.DataArray:
        # Convert the spectra to a datarray
        psd_da = xarray.DataArray(
            data=self.spectra,
            coords={"id": np.arange(len(self.spectra)), "frequency": self.fbands},
            dims=["id", "frequency"],
        )

        milli_psd = utils.spectra_ds_to_bands(
            psd_da,
            self.bands_limits,
            self.bands_c,
            fft_bin_width=self.fs / self.nfft,
            db=False,
        )
        milli_psd = 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY

        return milli_psd

    def get_milli_psd(self, data: np.ndarray) -> xarray.DataArray:
        """
        Convenience to get the millidecade bands for a single segment of data
        """
        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        # Convert the spectrum to a datarray
        psd_da = xarray.DataArray(
            data=[spectrum],
            coords={"id": np.arange(1), "frequency": fbands},
            dims=["id", "frequency"],
        )

        milli_psd = utils.spectra_ds_to_bands(
            psd_da,
            self.bands_limits,
            self.bands_c,
            fft_bin_width=self.fs / self.nfft,
            db=False,
        )
        milli_psd = 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY

        return milli_psd
