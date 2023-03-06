import numpy as np
import pypam.signal as sig

import xarray
from pypam import utils

# Status: Preliminary
# Initially based on pypam's signal_oriented.py example.


def pypam_process(fs: int, data: np.ndarray) -> xarray.DataArray:
    print(f"  pypam_process: fs={fs} data.shape = {data.shape}")

    # Set the nfft to 1 second
    nfft = fs

    s = sig.Signal(data, fs=fs)
    s.set_band(None)
    fbands, spectra, _ = s.spectrum(
        scaling="spectrum", nfft=nfft, db=False, overlap=0, force_calc=True
    )
    # NOTE: db=False above because True would make pypam use a fixed ref=1.0, which is not what we want.
    # Convert to dB:
    spectra = 10 * np.log10(spectra) + 178

    # Convert the spectra to a datarray
    psd_da = xarray.DataArray(
        [spectra],
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

    print(f"  bands_limits = {len(bands_limits)}")
    print(f"  bands_c = {len(bands_c)}")
    milli_psd_str = f"{milli_psd}".replace("\n", "\n    ")
    print(f"  milli_psd = {milli_psd_str}")

    # milli_psd.mean('id').plot()
    # plt.show()

    return milli_psd
