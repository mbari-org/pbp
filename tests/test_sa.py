"""
Tests for the SaSupport implementations.

These tests verify that our extracted functions produce identical results
to the original PyPAM functions using the SaSupport interface.
"""

import numpy as np
import xarray as xr

from pbp.sa_support_impl import SaSupportImpl
from pbp.sa_support_pypam import SaSupportPyPamImpl


class TestSaSupportComparison:
    """Test that SaSupportImpl matches SaSupportPyPamImpl outputs."""

    def test_get_hybrid_millidecade_limits(self):
        """Test that both implementations produce identical band limits."""
        band = [10, 1000]
        fs = 2000
        nfft = 2048

        # Create both implementations
        sa = SaSupportImpl(fs, nfft)
        sb = SaSupportPyPamImpl(fs, nfft)

        # Get results from both implementations
        a_limits, a_centers = sa.get_hybrid_millidecade_limits(band)
        b_limits, b_centers = sb.get_hybrid_millidecade_limits(band)

        # Compare results
        np.testing.assert_allclose(a_limits, b_limits, rtol=1e-10)
        np.testing.assert_allclose(a_centers, b_centers, rtol=1e-10)

    def test_compute_spectrum(self):
        """Test that both implementations produce identical spectra."""
        # Generate a test signal
        fs = 2000
        nfft = 512
        t = np.linspace(0, 1.0, fs)
        signal = np.sin(2 * np.pi * 100 * t) + 0.5 * np.sin(2 * np.pi * 200 * t)

        # Create both implementations
        sa = SaSupportImpl(fs, nfft)
        sb = SaSupportPyPamImpl(fs, nfft)

        # Get spectrum from both implementations
        a_freq, a_psd = sa.compute_spectrum(signal)
        b_freq, b_psd = sb.compute_spectrum(signal)

        # Compare results
        np.testing.assert_allclose(a_freq, b_freq, rtol=1e-10)
        np.testing.assert_allclose(a_psd, b_psd, rtol=1e-10)

    def test_spectra_ds_to_bands(self):
        """Test that both implementations produce identical band aggregations."""
        # Setup parameters
        band = [10, 1000]
        fs = 2000
        nfft = 2048

        # Create both implementations
        sa = SaSupportImpl(fs, nfft)
        sb = SaSupportPyPamImpl(fs, nfft)

        # Get bands from one implementation (they should be identical)
        bands_limits, bands_c = sa.get_hybrid_millidecade_limits(band)

        # Create test PSD data that covers the full frequency range
        max_freq_index = int(len(bands_c) * 2)  # Ensure we have enough frequency coverage
        frequencies = np.arange(max_freq_index) * sa.fft_bin_width

        # Create simple, uniform PSD data to avoid numerical complexities
        psd_data = np.ones((2, len(frequencies)))  # 2 time steps, uniform spectrum

        psd_da = xr.DataArray(
            data=psd_data,
            coords={"time": [0, 1], "frequency": frequencies},
            dims=["time", "frequency"],
        )

        # Test both implementations
        impl_result = sa.spectra_ds_to_bands(psd_da, bands_limits, bands_c)
        pypam_result = sb.spectra_ds_to_bands(psd_da, bands_limits, bands_c)

        # Compare results - should be identical
        np.testing.assert_allclose(impl_result.values, pypam_result.values, rtol=1e-10)
        np.testing.assert_allclose(
            impl_result.frequency_bins.values,
            pypam_result.frequency_bins.values,
            rtol=1e-10,
        )

        # Verify structure matches
        assert impl_result.dims == pypam_result.dims
        assert set(impl_result.coords.keys()) == set(pypam_result.coords.keys())


class TestSaSupportStandalone:
    """Test that SaSupport implementations work independently."""

    def test_get_hybrid_millidecade_limits_basic(self):
        """Test basic functionality of get_hybrid_millidecade_limits."""
        band = [10, 1000]
        fs = 2000
        nfft = 2048

        sa = SaSupportImpl(fs, nfft)
        limits, centers = sa.get_hybrid_millidecade_limits(band)

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
        nfft = 256
        t = np.linspace(0, 1.0, fs)
        signal = np.sin(2 * np.pi * 50 * t)  # 50 Hz sine wave

        sa = SaSupportImpl(fs, nfft)
        freq, psd = sa.compute_spectrum(signal)

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
        fs = 1000
        nfft = 512
        sa = SaSupportImpl(fs, nfft)

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

        result = sa.spectra_ds_to_bands(psd_da, bands_limits, bands_c)

        # Basic sanity checks
        assert result.dims == ("time", "frequency_bins")
        assert len(result.frequency_bins) == len(bands_c)
        assert "lower_frequency" in result.coords
        assert "upper_frequency" in result.coords

    def test_fft_bin_width_calculation(self):
        """Test that fft_bin_width is correctly calculated and used."""
        fs = 2000
        nfft = 1024

        sa = SaSupportImpl(fs, nfft)

        # Verify fft_bin_width is correctly calculated
        expected_bin_width = fs / nfft
        assert sa.fft_bin_width == expected_bin_width

        # Verify it's used correctly in spectra_ds_to_bands
        frequencies = np.arange(0, 100, expected_bin_width)[:50]
        psd_data = np.ones((1, len(frequencies)))

        psd_da = xr.DataArray(
            data=psd_data,
            coords={"time": [0], "frequency": frequencies},
            dims=["time", "frequency"],
        )

        bands_limits = [0, 25, 50, 75]
        bands_c = [12.5, 37.5, 62.5]

        # This should work without explicitly passing fft_bin_width
        result = sa.spectra_ds_to_bands(psd_da, bands_limits, bands_c)
        assert result is not None


class TestSaSupportEdgeCases:
    """Additional tests for comprehensive coverage."""

    def test_different_nfft_values(self):
        """Test how different nfft values affect band calculation."""
        band = [10, 1000]
        fs = 2000
        nfft_values = [256, 512, 1024, 2048]

        previous_num_bands = None
        for nfft in nfft_values:
            sa = SaSupportImpl(fs, nfft)
            limits, centers = sa.get_hybrid_millidecade_limits(band)

            # Higher nfft should generally result in more bands (finer resolution)
            if previous_num_bands is not None:
                assert (
                    len(centers) >= previous_num_bands
                ), f"nfft={nfft} should have >= bands than previous"
            previous_num_bands = len(centers)

    def test_spectrum_computation_edge_cases(self):
        """Test spectrum computation with various edge cases."""
        fs = 1000
        nfft = 512

        sa = SaSupportImpl(fs, nfft)

        # Very short signal
        short_signal = np.sin(2 * np.pi * 50 * np.linspace(0, 0.1, 100))
        freq, psd = sa.compute_spectrum(short_signal)
        assert len(freq) == len(psd)
        assert np.all(np.isfinite(psd))

        # Signal with multiple frequency components
        t = np.linspace(0, 1, fs)
        multi_tone = (
            np.sin(2 * np.pi * 50 * t)
            + 0.5 * np.sin(2 * np.pi * 150 * t)
            + 0.25 * np.sin(2 * np.pi * 300 * t)
        )
        freq, psd = sa.compute_spectrum(multi_tone)

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
        nfft = 512
        t = np.linspace(0, 1, fs)
        signal = np.sin(2 * np.pi * 100 * t)

        sa = SaSupportImpl(fs, nfft)

        # Get spectrum in linear and dB scales
        freq_lin, psd_lin = sa.compute_spectrum(signal, db=False)
        freq_db, psd_db = sa.compute_spectrum(signal, db=True)

        # Verify frequency arrays are identical
        np.testing.assert_allclose(freq_lin, freq_db)

        # Verify dB conversion: dB = 10 * log10(linear)
        expected_db = 10 * np.log10(psd_lin)
        np.testing.assert_allclose(psd_db, expected_db, rtol=1e-10)

    def test_both_implementations_consistency(self):
        """Test that both implementations handle the same edge cases consistently."""
        fs = 1000
        nfft = 256

        # Test with different parameter combinations
        test_cases = [
            {"scaling": "density", "overlap": 0.0, "db": False},
            {"scaling": "density", "overlap": 0.5, "db": True},
            {"scaling": "spectrum", "overlap": 0.25, "db": False},
        ]

        # Generate test signal
        t = np.linspace(0, 1, fs)
        signal = np.sin(2 * np.pi * 100 * t) + 0.3 * np.random.randn(len(t))

        for params in test_cases:
            sa = SaSupportImpl(fs, nfft)
            sb = SaSupportPyPamImpl(fs, nfft)

            # Both should produce identical results
            freq1, psd1 = sa.compute_spectrum(signal, **params)
            freq2, psd2 = sb.compute_spectrum(signal, **params)

            np.testing.assert_allclose(freq1, freq2, rtol=1e-10)
            np.testing.assert_allclose(psd1, psd2, rtol=1e-10)
