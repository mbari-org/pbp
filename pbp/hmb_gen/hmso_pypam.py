from typing import Tuple, List
import numpy as np
import xarray as xr

from pypam import utils
import pypam.signal as pypam_signal


class HmsoPypam:
    """
    Core hybrid millidecade spectra operations using PyPAM.
    """

    def __init__(self, fs: int, nfft: int):
        self.fs = fs
        self.nfft = nfft
        self.fft_bin_width = fs / nfft

    def get_hybrid_millidecade_limits(
        self, band: List[float]
    ) -> Tuple[List[float], List[float]]:
        return utils.get_hybrid_millidecade_limits(band, self.nfft, self.fs)

    def compute_spectrum(
        self,
        signal: np.ndarray,
        scaling: str = "density",
        overlap: float = 0.5,
        db: bool = False,
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
        freq_coord: str = "frequency",
        db: bool = False,
    ) -> xr.DataArray:
        return utils.spectra_ds_to_bands(
            psd, bands_limits, bands_c, self.fft_bin_width, freq_coord, db
        )
