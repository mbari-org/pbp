"""
SaSupport direct implementation
"""

from typing import Optional, Tuple, List
import numpy as np
import xarray as xr

from pbp.sa_support import SaSupport
from pbp.spectral_analysis import (
    get_hybrid_millidecade_limits,
    spectra_ds_to_bands,
    compute_spectrum,
)


class SaSupportImpl(SaSupport):
    def get_hybrid_millidecade_limits(
        self, band: List[float]
    ) -> Tuple[List[float], List[float]]:
        return get_hybrid_millidecade_limits(band, self.nfft, self.fs)

    def compute_spectrum(
        self,
        signal: np.ndarray,
        scaling: str = "density",
        overlap: float = 0,
        window_name: str = "hann",
        db: bool = True,
        band: Optional[Tuple[float, float]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        return compute_spectrum(
            signal, self.fs, self.nfft, scaling, overlap, window_name, db, band
        )

    def spectra_ds_to_bands(
        self,
        psd: xr.DataArray,
        bands_limits: List[float],
        bands_c: List[float],
        fft_bin_width: float,
        freq_coord: str = "frequency",
        db: bool = True,
    ) -> xr.DataArray:
        return spectra_ds_to_bands(
            psd, bands_limits, bands_c, fft_bin_width, freq_coord, db
        )
