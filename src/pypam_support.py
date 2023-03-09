import numpy as np
import pypam.signal as sig

import xarray
from pypam import utils

# Status: Preliminary
# Initially based on pypam's signal_oriented.py example.

# Approximate "flat" sensitivity of the hydrophone
APPROX_FLAT_SENSITIVITY = 178


def pypam_process(fs: int, data: np.ndarray) -> xarray.DataArray:
    print(f"  pypam_process: fs={fs} data.shape = {data.shape}")

    # Set the nfft to 1 second
    nfft = fs

    signal = sig.Signal(data, fs=fs)
    signal.set_band(None)
    fbands, spectra, _ = signal.spectrum(
        scaling="density", nfft=nfft, db=False, overlap=0.5, force_calc=True
    )

    # Convert the spectra to a datarray
    psd_da = xarray.DataArray(
        data=[spectra],
        coords={"id": np.arange(1), "frequency": fbands},
        dims=["id", "frequency"],
    )

    # Get the millidecade bands
    bands_limits, bands_c = utils.get_hybrid_millidecade_limits(
        band=[0, fs / 2], nfft=nfft
    )
    milli_psd = utils.spectra_ds_to_bands(
        psd_da, bands_limits, bands_c, fft_bin_width=fs / nfft, db=False
    )
    milli_psd = 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY

    return milli_psd
