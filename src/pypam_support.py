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

    def pypam_process(self, data: np.ndarray) -> xarray.DataArray:
        print(f"  pypam_process: data.shape = {data.shape}")

        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        fbands, spectra, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )

        # Convert the spectra to a datarray
        psd_da = xarray.DataArray(
            data=[spectra],
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
