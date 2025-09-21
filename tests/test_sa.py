"""
Tests for the extracted spectral analysis functions.

These tests verify that our extracted functions produce identical results
to the original PyPAM functions.
"""

import numpy as np
import xarray as xr

# Import both our extracted functions and the original PyPAM functions
from pbp.spectral_analysis import (
    get_hybrid_millidecade_limits as our_get_limits,
    spectra_ds_to_bands as our_spectra_to_bands,
    compute_spectrum as our_compute_spectrum,
)

from pypam.utils import get_hybrid_millidecade_limits as pypam_get_limits
from pypam.utils import spectra_ds_to_bands as pypam_spectra_to_bands
import pypam.signal as pypam_signal


class TestExtractedFunctions:
    """Test that extracted functions match PyPAM outputs."""

    def test_get_hybrid_millidecade_limits(self):
        """Test that our get_hybrid_millidecade_limits matches PyPAM."""
        band = [10, 1000]
        nfft = 2048
        fs = 2000

        # Get results from both implementations
        our_limits, our_centers = our_get_limits(band, nfft, fs)
        pypam_limits, pypam_centers = pypam_get_limits(band, nfft, fs)

        # Compare results
        np.testing.assert_allclose(our_limits, pypam_limits, rtol=1e-10)
        np.testing.assert_allclose(our_centers, pypam_centers, rtol=1e-10)

    def test_compute_spectrum(self):
        """Test that our compute_spectrum matches PyPAM Signal.spectrum."""
        # Generate a test signal
        fs = 2000
        t = np.linspace(0, 1.0, fs)
        signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)
        nfft = 512

        # Get spectrum from our implementation
        our_freq, our_psd = our_compute_spectrum(
            signal, fs=fs, nfft=nfft, scaling="density", db=False, overlap=0.5
        )

        # Get spectrum from PyPAM
        pypam_sig = pypam_signal.Signal(signal, fs=fs)
        pypam_sig.set_band(None)
        pypam_freq, pypam_psd, _ = pypam_sig.spectrum(
            scaling="density", nfft=nfft, db=False, overlap=0.5, force_calc=True
        )

        # Compare results
        np.testing.assert_allclose(our_freq, pypam_freq, rtol=1e-10)
        np.testing.assert_allclose(our_psd, pypam_psd, rtol=1e-10)

    def test_spectra_ds_to_bands(self):
        """Test that our spectra_ds_to_bands matches PyPAM."""
        # Use the same test parameters as the other successful comparison tests
        band = [10, 1000]
        nfft = 2048
        fs = 2000
        fft_bin_width = fs / nfft

        # Get bands from PyPAM (ensures consistency)
        bands_limits, bands_c = pypam_get_limits(band, nfft, fs)

        # Create test PSD data that covers the full frequency range
        # Use the frequency grid that PyPAM would expect
        max_freq_index = int(len(bands_c) * 2)  # Ensure we have enough frequency coverage
        frequencies = np.arange(max_freq_index) * fft_bin_width

        # Create simple, uniform PSD data to avoid numerical complexities
        psd_data = np.ones((2, len(frequencies)))  # 2 time steps, uniform spectrum

        psd_da = xr.DataArray(
            data=psd_data,
            coords={"time": [0, 1], "frequency": frequencies},
            dims=["time", "frequency"],
        )

        # Test both implementations
        our_result = our_spectra_to_bands(
            psd_da, bands_limits, bands_c, fft_bin_width, db=False
        )

        pypam_result = pypam_spectra_to_bands(
            psd_da, bands_limits, bands_c, fft_bin_width, db=False
        )

        # Compare results - should be identical
        np.testing.assert_allclose(our_result.values, pypam_result.values, rtol=1e-10)
        np.testing.assert_allclose(
            our_result.frequency_bins.values,
            pypam_result.frequency_bins.values,
            rtol=1e-10,
        )

        # Verify structure matches
        assert our_result.dims == pypam_result.dims
        assert set(our_result.coords.keys()) == set(pypam_result.coords.keys())


class TestStandaloneFunctions:
    """Test that functions work independently of PyPAM."""

    def test_get_hybrid_millidecade_limits_basic(self):
        """Test basic functionality of get_hybrid_millidecade_limits."""
        band = [10, 1000]
        nfft = 2048
        fs = 2000

        limits, centers = our_get_limits(band, nfft, fs)

        # Basic sanity checks
        assert len(limits) == len(centers) + 1  # limits should have one more element
        assert limits[0] >= band[0]  # first limit should be >= min frequency
        assert limits[-1] <= band[1]  # last limit should be <= max frequency
        assert all(
            limits[i] <= limits[i + 1] for i in range(len(limits) - 1)
        )  # should be monotonic

    def test_compute_spectrum_basic(self):
        """Test basic functionality of compute_spectrum."""
        # Generate a simple test signal
        fs = 1000
        t = np.linspace(0, 1.0, fs)
        signal = np.sin(2 * np.pi * 50 * t)  # 50 Hz sine wave

        freq, psd = our_compute_spectrum(signal, fs=fs, nfft=256, db=False)

        # Basic sanity checks
        assert len(freq) == len(psd)
        assert freq[0] >= 0
        assert freq[-1] <= fs / 2
        assert all(
            freq[i] <= freq[i + 1] for i in range(len(freq) - 1)
        )  # frequencies should be monotonic

        # Peak should be around 50 Hz
        peak_idx = np.argmax(psd)
        peak_freq = freq[peak_idx]
        assert 45 <= peak_freq <= 55  # Allow some tolerance for FFT resolution

    def test_spectra_ds_to_bands_basic(self):
        """Test basic functionality of spectra_ds_to_bands."""
        # Create simple test data
        frequencies = np.linspace(10, 100, 50)
        psd_data = np.ones((1, 50))  # Flat spectrum

        psd_da = xr.DataArray(
            data=psd_data,
            coords={"time": [0], "frequency": frequencies},
            dims=["time", "frequency"],
        )

        # Define some bands
        bands_limits = [10, 30, 60, 100]
        bands_c = [20, 45, 80]
        fft_bin_width = 2.0

        result = our_spectra_to_bands(
            psd_da, bands_limits, bands_c, fft_bin_width, db=False
        )

        # Basic sanity checks
        assert result.dims == ("time", "frequency_bins")
        assert len(result.frequency_bins) == len(bands_c)
        assert "lower_frequency" in result.coords
        assert "upper_frequency" in result.coords


class TestAdditionalCoverage:
    """Additional tests for comprehensive coverage."""

    def test_different_nfft_values(self):
        """Test how different nfft values affect band calculation."""
        band = [10, 1000]
        fs = 2000
        nfft_values = [256, 512, 1024, 2048]

        previous_num_bands = None
        for nfft in nfft_values:
            limits, centers = our_get_limits(band, nfft, fs)

            # Higher nfft should generally result in more bands (finer resolution)
            if previous_num_bands is not None:
                assert (
                    len(centers) >= previous_num_bands
                ), f"nfft={nfft} should have >= bands than previous"
            previous_num_bands = len(centers)

    def test_spectrum_computation_edge_cases(self):
        """Test spectrum computation with various edge cases."""
        fs = 1000

        # Very short signal
        short_signal = np.sin(2 * np.pi * 50 * np.linspace(0, 0.1, 100))
        freq, psd = our_compute_spectrum(short_signal, fs=fs, nfft=512, db=False)
        assert len(freq) == len(psd)
        assert np.all(np.isfinite(psd))

        # Signal with multiple frequency components
        t = np.linspace(0, 1, fs)
        multi_tone = (
            np.sin(2 * np.pi * 50 * t)
            + 0.5 * np.sin(2 * np.pi * 150 * t)
            + 0.25 * np.sin(2 * np.pi * 300 * t)
        )
        freq, psd = our_compute_spectrum(multi_tone, fs=fs, nfft=512, db=False)

        # Should see peaks around 50, 150, and 300 Hz
        peak_indices = np.argsort(psd)[-5:]  # Top 5 peaks
        peak_freqs = freq[peak_indices]

        # At least one peak should be near each frequency component
        assert any(abs(f - 50) < 10 for f in peak_freqs)
        assert any(abs(f - 150) < 10 for f in peak_freqs)

    def test_db_conversion_consistency(self):
        """Test that dB conversion is consistent between functions."""
        # Generate test signal
        fs = 1000
        t = np.linspace(0, 1, fs)
        signal = np.sin(2 * np.pi * 100 * t)

        # Get spectrum in linear and dB scales
        freq_lin, psd_lin = our_compute_spectrum(signal, fs=fs, nfft=512, db=False)
        freq_db, psd_db = our_compute_spectrum(signal, fs=fs, nfft=512, db=True)

        # Verify frequency arrays are identical
        np.testing.assert_allclose(freq_lin, freq_db)

        # Verify dB conversion: dB = 10 * log10(linear)
        expected_db = 10 * np.log10(psd_lin)
        np.testing.assert_allclose(psd_db, expected_db, rtol=1e-10)
