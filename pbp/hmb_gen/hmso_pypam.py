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


class SpectrumBander:
    """
    Maps a single spectrum to bands, with results equivalent to
    `pypam.utils.spectra_ds_to_bands` (with `db=False`), but precomputing
    the band assignment so it can be cheaply applied on a per-segment basis.

    As in pypam, each band is the sum of the FFT bins within it, plus a fraction
    of the bins at its limits, divided by the band width.
    """

    def __init__(
        self,
        fbands: np.ndarray,
        bands_limits: List[float],
        fft_bin_width: float,
    ):
        """
        Args:
            fbands: Frequencies of the spectrum bins (as returned by `compute_spectrum`).
            bands_limits: Limits of the desired bands.
            fft_bin_width: FFT bin width in Hz.
        """
        limits = np.asarray(bands_limits, dtype=np.float64)
        num_bins = len(fbands)
        f0 = fbands[0]
        self.num_bands = len(limits) - 1

        indices = np.floor((limits + fft_bin_width / 2) / fft_bin_width).astype(int)
        indices -= int(f0 / fft_bin_width)
        if indices[-1] > num_bins - 1:
            indices[-1] = num_bins - 1

        # bins at the limits only contribute a fraction to the adjacent bands:
        self._lower_indices = indices[:-1]
        self._upper_indices = indices[1:]
        self._lower_factors = (
            self._lower_indices * fft_bin_width + fft_bin_width / 2 - limits[:-1] + f0
        ) / fft_bin_width
        self._upper_factors = (
            limits[1:] - (self._upper_indices * fft_bin_width - fft_bin_width / 2) - f0
        ) / fft_bin_width

        # each other bin fully goes to the band [lower, upper) containing it, if any:
        band_of_bin = np.searchsorted(limits, fbands, side="right") - 1
        inner = (band_of_bin >= 0) & (band_of_bin < self.num_bands)
        inner[indices] = False
        self._inner_bins = np.flatnonzero(inner)
        self._inner_bands = band_of_bin[inner]

        self._bandwidths = limits[1:] - limits[:-1]

    def apply(self, spectrum: np.ndarray) -> np.ndarray:
        """
        Returns the band values for the given spectrum.
        """
        bands = np.bincount(
            self._inner_bands,
            weights=spectrum[self._inner_bins],
            minlength=self.num_bands,
        )
        bands += spectrum[self._lower_indices] * self._lower_factors
        bands += spectrum[self._upper_indices] * self._upper_factors
        return bands / self._bandwidths
