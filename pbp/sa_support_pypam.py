"""
PyPAM-based SaSupport implementation.
"""

from typing import Optional, Tuple, List
import numpy as np
import xarray as xr

from pbp.sa_support import SaSupport
from pypam import utils
import pypam.signal as pypam_signal


class SaSupportPyPamImpl(SaSupport):
    def get_hybrid_millidecade_limits(
        self, band: List[float]
    ) -> Tuple[List[float], List[float]]:
        return utils.get_hybrid_millidecade_limits(band, self.nfft, self.fs)

    def compute_spectrum(
        self,
        signal: np.ndarray,
        scaling: str = "density",
        overlap: float = 0,
        window_name: str = "hann",
        db: bool = True,
        band: Optional[Tuple[float, float]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        pypam_sig = pypam_signal.Signal(signal, fs=self.fs)
        pypam_sig.set_band(None)
        fbands, spectrum, _ = pypam_sig.spectrum(
            scaling=scaling, nfft=self.nfft, db=db, overlap=overlap, force_calc=True
        )
        return fbands, spectrum

    def spectra_ds_to_bands(
        self,
        psd: xr.DataArray,
        bands_limits: List[float],
        bands_c: List[float],
        fft_bin_width: float,
        freq_coord: str = "frequency",
        db: bool = True,
    ) -> xr.DataArray:
        return utils.spectra_ds_to_bands(
            psd, bands_limits, bands_c, fft_bin_width, freq_coord, db
        )
