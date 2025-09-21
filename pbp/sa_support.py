"""
Spectral Analysis Support
=========================
"""

from typing import Optional, Tuple, List
from abc import abstractmethod
import numpy as np
import xarray as xr
import os


class SaSupport:
    def __init__(self, fs: int, nfft: int):
        """
        Initialize SaSupport with sampling frequency and FFT parameters.

        Args:
            fs: Sampling frequency in Hz
            nfft: Number of FFT points
        """
        self.fs = fs
        self.nfft = nfft

    @abstractmethod
    def get_hybrid_millidecade_limits(
        self, band: List[float]
    ) -> Tuple[List[float], List[float]]:
        """
        Calculate frequency band limits for hybrid millidecade analysis.

        This is a convenience function that calls _get_bands_limits with parameters
        specific to hybrid millidecade analysis (base=10, bands_per_division=1000).

        Parameters
        ----------
        band : list of float
            [min_freq, max_freq] frequency range to analyze

        Returns
        -------
        tuple
            (bands_limits, bands_c) where bands_limits are the band edges and
            bands_c are the band center frequencies
        """

    @abstractmethod
    def compute_spectrum(
        self,
        signal: np.ndarray,
        scaling: str = "density",
        overlap: float = 0.5,
        window_name: str = "hann",
        db: bool = False,
        band: Optional[Tuple[float, float]] = None,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Compute power spectral density using Welch's method.

        This function extracts the core spectrum computation logic from PyPAM's Signal class,
        providing a direct interface to scipy.signal.welch with optional frequency band filtering.

        Parameters
        ----------
        signal : np.ndarray
            Input audio signal
        scaling : str
            Scaling type: 'density' for power spectral density or 'spectrum' for power spectrum
        overlap : float
            Overlap fraction between 0 and 1
        window_name : str
            Window function name (passed to scipy.signal.get_window)
        db : bool
            If True, return values in dB scale
        band : tuple of float, optional
            (min_freq, max_freq) to filter the output frequency range

        Returns
        -------
        tuple
            (frequencies, psd) where frequencies is the frequency array and psd is the
            power spectral density
        """

    @abstractmethod
    def spectra_ds_to_bands(
        self,
        psd: xr.DataArray,
        bands_limits: List[float],
        bands_c: List[float],
        fft_bin_width: float,
        freq_coord: str = "frequency",
        db: bool = False,
    ) -> xr.DataArray:
        """
        Group spectral data into frequency bands with proportional allocation.

        This function aggregates power spectral density data into specified frequency bands.
        If a band limit is not aligned with the PSD frequency bins, the affected bins are
        proportionally divided between adjacent bands.

        Parameters
        ----------
        psd : xr.DataArray
            Power spectral density data with frequency dimension
        bands_limits : list of float
            Frequency limits defining the band edges
        bands_c : list of float
            Center frequencies of the bands (used for output coordinate naming)
        fft_bin_width : float
            Width of each FFT frequency bin in Hz
        freq_coord : str
            Name of the frequency coordinate in the input DataArray
        db : bool
            If True, return values in dB scale

        Returns
        -------
        xr.DataArray
            Aggregated PSD data with frequency_bins dimension instead of frequency
        """


def get_sa_support(fs: int, nfft: int) -> SaSupport:
    """
    Factory function to get an instance of SaSupport.

    Args:
        fs: Sampling frequency in Hz
        nfft: Number of FFT points

    Returns
    -------
    SaSupport
        An instance of a class implementing the SaSupport interface.
    """
    use_own_functions = os.getenv("PBP_USE_SPECTRAL_FUNCTIONS") == "1"
    if use_own_functions:
        from pbp.sa_support_impl import SaSupportImpl

        return SaSupportImpl(fs, nfft)

    else:
        from pbp.sa_support_pypam import SaSupportPyPamImpl

        return SaSupportPyPamImpl(fs, nfft)
