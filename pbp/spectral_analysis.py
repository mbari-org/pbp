"""
Spectral Analysis Module
========================

This module contains spectral analysis functions extracted from PyPAM for
generating hybrid millidecade power spectral density (PSD) products.

Key functions:
- get_hybrid_millidecade_limits: Calculate frequency band limits for hybrid millidecade analysis
- spectra_ds_to_bands: Aggregate spectral data into frequency bands
- compute_spectrum: Compute power spectral density using Welch's method

This is a focused extraction of the specific PyPAM functionality needed for
hybrid millidecade PSD generation, without the overhead of the full PyPAM package.
"""

from typing import Optional, Tuple, List
import numpy as np
import pandas as pd
import scipy.signal as sig
import xarray as xr


def get_hybrid_millidecade_limits(
    band: List[float], nfft: int, fs: Optional[float] = None
) -> Tuple[List[float], List[float]]:
    """
    Calculate frequency band limits for hybrid millidecade analysis.

    This is a convenience function that calls _get_bands_limits with parameters
    specific to hybrid millidecade analysis (base=10, bands_per_division=1000).

    Parameters
    ----------
    band : list of float
        [min_freq, max_freq] frequency range to analyze
    nfft : int
        Number of FFT points
    fs : float, optional
        Sampling frequency. If None, assumed to be 2 * max_freq

    Returns
    -------
    tuple
        (bands_limits, bands_c) where bands_limits are the band edges and
        bands_c are the band center frequencies
    """
    if fs is None:
        fs = band[1] * 2
    return _get_bands_limits(
        band, nfft, base=10, bands_per_division=1000, hybrid_mode=True, fs=fs
    )


def compute_spectrum(
    signal: np.ndarray,
    fs: float,
    nfft: int = 512,
    scaling: str = "density",
    overlap: float = 0,
    window_name: str = "hann",
    db: bool = True,
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
    fs : float
        Sampling frequency in Hz
    nfft : int
        Length of the FFT window in samples. Should be a power of 2.
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
    noverlap = int(nfft * overlap)

    # Zero-pad if signal is shorter than nfft
    if nfft > signal.size:
        padded_signal = np.zeros(nfft)
        padded_signal[: signal.size] = signal
        signal = padded_signal

    # Get window and compute spectrum
    window = sig.get_window(window_name, nfft)
    freq, psd = sig.welch(
        signal,
        fs=fs,
        window=window,
        nfft=nfft,
        scaling=scaling,
        noverlap=noverlap,
        detrend=False,
    )

    # Apply frequency band filtering if specified
    if band is not None and band[0] is not None:
        low_freq_idx = np.argmax(freq >= band[0])
        psd = psd[low_freq_idx:]
        freq = freq[low_freq_idx:]

    # Convert to dB if requested
    if db:
        psd = _to_db(psd, ref=1.0, square=False)

    return freq, psd


def spectra_ds_to_bands(
    psd: xr.DataArray,
    bands_limits: List[float],
    bands_c: List[float],
    fft_bin_width: float,
    freq_coord: str = "frequency",
    db: bool = True,
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
    # Calculate FFT frequency indices for band limits
    fft_freq_indices = (
        np.floor((np.array(bands_limits) + (fft_bin_width / 2)) / fft_bin_width)
    ).astype(int)
    original_first_fft_index = int(psd[freq_coord].values[0] / fft_bin_width)
    fft_freq_indices -= original_first_fft_index

    # Ensure indices don't exceed array bounds
    max_index = len(psd[freq_coord]) - 1
    fft_freq_indices = np.clip(fft_freq_indices, 0, max_index)

    # Create DataFrame with band information
    limits_df = pd.DataFrame(
        data={
            "lower_indexes": fft_freq_indices[:-1],
            "upper_indexes": fft_freq_indices[1:],
            "lower_freq": bands_limits[:-1],
            "upper_freq": bands_limits[1:],
        }
    )

    # Calculate proportional factors for partial bin allocation
    limits_df["lower_factor"] = (
        limits_df["lower_indexes"] * fft_bin_width
        + fft_bin_width / 2
        - limits_df["lower_freq"]
        + psd[freq_coord].values[0]
    )
    limits_df["upper_factor"] = (
        limits_df["upper_freq"]
        - (limits_df["upper_indexes"] * fft_bin_width - fft_bin_width / 2)
        - psd[freq_coord].values[0]
    )

    # Apply proportional factors to border bins
    psd_limits_lower = (
        psd.isel(**{freq_coord: limits_df["lower_indexes"].values})
        * limits_df["lower_factor"].values
        / fft_bin_width
    )
    psd_limits_upper = (
        psd.isel(**{freq_coord: limits_df["upper_indexes"].values})
        * limits_df["upper_factor"].values
        / fft_bin_width
    )

    # Remove border bins from main data and group into bands
    psd_without_borders = psd.drop_isel(**{freq_coord: fft_freq_indices})
    new_coord_name = freq_coord + "_bins"

    if len(psd_without_borders[freq_coord]) == 0:
        # Handle case where all data is in border bins
        psd_bands = xr.zeros_like(psd)
        psd_bands = psd_bands.assign_coords({new_coord_name: (freq_coord, bands_c)})
        psd_bands = psd_bands.swap_dims({freq_coord: new_coord_name}).drop_vars(
            freq_coord
        )
    else:
        # Group remaining bins into bands
        psd_bands = psd_without_borders.groupby_bins(
            freq_coord, bins=bands_limits, labels=bands_c, right=False
        ).sum()
        psd_bands = psd_bands.fillna(0)

    # Add back the proportionally allocated border contributions
    psd_bands = psd_bands + psd_limits_lower.values + psd_limits_upper.values

    # Add frequency limit coordinates
    psd_bands = psd_bands.assign_coords(
        {"lower_frequency": (new_coord_name, limits_df["lower_freq"])}
    )
    psd_bands = psd_bands.assign_coords(
        {"upper_frequency": (new_coord_name, limits_df["upper_freq"])}
    )

    # Normalize by bandwidth to get spectral density
    bandwidths = psd_bands.upper_frequency - psd_bands.lower_frequency
    psd_bands = psd_bands / bandwidths

    # Convert to dB if requested
    if db:
        psd_bands = psd_bands * 0 + 10 * np.log10(psd_bands)

    # Preserve original attributes
    psd_bands.attrs.update(psd.attrs)
    return psd_bands


def _get_center_freq(
    base: float, bands_per_division: int, n: int, first_out_band_centre_freq: float
) -> float:
    """
    Calculate center frequency for a given band number.

    Parameters
    ----------
    base : float
        Base for logarithmic spacing (typically 10)
    bands_per_division : int
        Number of bands per division (1000 for millidecade)
    n : int
        Band number
    first_out_band_centre_freq : float
        Center frequency of the first output band

    Returns
    -------
    float
        Center frequency for band n
    """
    if (bands_per_division == 10) or ((bands_per_division % 2) == 1):
        center_freq = first_out_band_centre_freq * base ** ((n - 1) / bands_per_division)
    else:
        b = bands_per_division * 0.3
        G = 10.0 ** (3.0 / 10.0)
        center_freq = base * G ** ((2 * (n - 1) + 1) / (2 * b))

    return center_freq


def _get_bands_limits(
    band: List[float],
    nfft: int,
    base: float,
    bands_per_division: int,
    hybrid_mode: bool,
    fs: Optional[float] = None,
) -> Tuple[List[float], List[float]]:
    """
    Calculate frequency band limits for spectral analysis.

    Parameters
    ----------
    band : list of float
        [min_freq, max_freq] frequency range
    nfft : int
        Number of FFT points
    base : float
        Base for logarithmic spacing (typically 10)
    bands_per_division : int
        Number of bands per division (1000 for millidecade)
    hybrid_mode : bool
        Whether to use hybrid linear/logarithmic spacing
    fs : float, optional
        Sampling frequency. If None, assumed to be 2 * max_freq

    Returns
    -------
    tuple
        (bands_limits, bands_c) where bands_limits are the band edges and
        bands_c are the band center frequencies
    """
    first_bin_centre = 0
    low_side_multiplier = base ** (-1 / (2 * bands_per_division))
    high_side_multiplier = base ** (1 / (2 * bands_per_division))

    if fs is None:
        fs = band[1] * 2
    fft_bin_width = fs / nfft

    # Start the frequencies list
    bands_limits = []
    bands_c = []

    # count the number of bands:
    band_count = 0
    center_freq = 0.0
    if hybrid_mode:
        bin_width = 0.0
        while bin_width < fft_bin_width:
            band_count = band_count + 1
            center_freq = _get_center_freq(base, bands_per_division, band_count, band[0])
            bin_width = (
                high_side_multiplier * center_freq - low_side_multiplier * center_freq
            )

        # now keep counting until the difference between the log spaced
        # center frequency and new frequency is greater than .025
        center_freq = _get_center_freq(base, bands_per_division, band_count, band[0])
        linear_bin_count = round(center_freq / fft_bin_width - first_bin_centre)
        dc = abs(linear_bin_count * fft_bin_width - center_freq) + 0.1
        while abs(linear_bin_count * fft_bin_width - center_freq) < dc:
            # Compute next one
            dc = abs(linear_bin_count * fft_bin_width - center_freq)
            band_count = band_count + 1
            linear_bin_count = linear_bin_count + 1
            center_freq = _get_center_freq(base, bands_per_division, band_count, band[0])

        linear_bin_count = linear_bin_count - 1
        band_count = band_count - 1

        if (fft_bin_width * linear_bin_count) > band[1]:
            linear_bin_count = int(fs / 2 / fft_bin_width + 1)

        for i in np.arange(linear_bin_count):
            # Add the frequencies
            fc = first_bin_centre + i * fft_bin_width
            if fc >= band[0]:
                bands_c.append(fc)
                bands_limits.append(fc - fft_bin_width / 2)

    # count the log space frequencies
    ls_freq = center_freq * high_side_multiplier
    while ls_freq < band[1]:
        fc = _get_center_freq(base, bands_per_division, band_count, band[0])
        ls_freq = fc * high_side_multiplier
        if fc >= band[0]:
            bands_c.append(fc)
            bands_limits.append(fc * low_side_multiplier)
        band_count += 1
    # Add the upper limit (bands_limits's length will be +1 compared to bands_c)
    if ls_freq > band[1]:
        ls_freq = band[1]
        if fc > band[1]:
            bands_c[-1] = band[1]
    bands_limits.append(ls_freq)
    return bands_limits, bands_c


def _to_db(wave: np.ndarray, ref: float = 1.0, square: bool = False) -> np.ndarray:
    """
    Convert linear values to decibel scale.

    Parameters
    ----------
    wave : np.ndarray
        Signal values in linear scale
    ref : float
        Reference value for dB conversion
    square : bool
        Set to True if the signal should be squared before conversion

    Returns
    -------
    np.ndarray
        Signal values in dB scale
    """
    if square:
        db = 10 * np.log10(wave**2 / ref**2)
    else:
        db = 10 * np.log10(wave / ref**2)
    return db
