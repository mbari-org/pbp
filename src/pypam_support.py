from typing import cast, List, Optional, Tuple

import numpy as np
import pypam.signal as sig

import xarray as xr
from pypam import utils

from src.misc_helper import brief_list, info

# Approximate "flat" sensitivity of the hydrophone
APPROX_FLAT_SENSITIVITY = 178


class PypamSupport:
    def __init__(
        self, fs: int, nfft: int = 0, subset_to: Optional[Tuple[int, int]] = None
    ):
        """
        :param fs:
        :param nfft:
        :param subset_to: Actually, `band` but different name while pypam is fixed
        """
        self.fs = fs
        self.nfft = nfft if nfft > 0 else self.fs

        self.subset_to = subset_to
        band = [0, self.fs / 2]  # for now.
        info(f"PypamSupport: subset_to={subset_to}  band={band}")

        self.bands_limits, self.bands_c = utils.get_hybrid_millidecade_limits(
            band=band, nfft=self.nfft
        )

        self.fbands: Optional[np.ndarray] = None
        self.spectra: List[np.ndarray] = []
        self.iso_minutes: List[str] = []
        self.num_secs_per_minute: List[int] = []

    def add_segment(self, data: np.ndarray, iso_minute: str):
        num_secs = int(len(data) / self.fs)
        info(f"  adding segment: {iso_minute} ({num_secs} secs used)")

        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        self.fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        self.spectra.append(spectrum)
        self.iso_minutes.append(iso_minute)
        self.num_secs_per_minute.append(num_secs)

    def get_aggregated_milli_psd(self) -> xr.DataArray:
        # Convert the spectra to a datarray
        psd_da = xr.DataArray(
            data=self.spectra,
            coords={"iso_minute": self.iso_minutes, "frequency": self.fbands},
            dims=["iso_minute", "frequency"],
        )
        milli_psd = self.subset_result(psd_da)
        milli_psd = cast(xr.DataArray, 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY)
        milli_psd.name = "psd"

        # ----------------------------------------
        # Toward capturing "effort" variable:
        #
        # With: milli_psd.attrs["effort"] = self.num_secs_per_minute
        # getting this when loading the resulting netcdf (via xarray.open_dataset):
        #    In [41]: droot.info()
        #    xarray.Dataset {
        #    dimensions:
        #    	frequency_bins = 2788 ;
        #    	iso_minute = 2 ;
        #
        #    variables:
        #    	float64 frequency_bins(frequency_bins) ;
        #    	float64 lower_frequency(frequency_bins) ;
        #    	float64 upper_frequency(frequency_bins) ;
        #    	float64 psd(iso_minute, frequency_bins) ;
        #    		psd:effort = [60 60] ;
        #    	object iso_minute(iso_minute) ;
        #
        #    // global attributes:
        #    }
        #
        # With: milli_psd["iso_minute"].attrs["effort"] = self.num_secs_per_minute
        # getting this when loading the resulting netcdf (via xarray.open_dataset):
        #    In [43]: d.info()
        #    xarray.Dataset {
        #    dimensions:
        #    	frequency_bins = 2788 ;
        #    	iso_minute = 2 ;
        #
        #    variables:
        #    	float64 frequency_bins(frequency_bins) ;
        #    	float64 lower_frequency(frequency_bins) ;
        #    	float64 upper_frequency(frequency_bins) ;
        #    	float64 psd(iso_minute, frequency_bins) ;
        #    	object iso_minute(iso_minute) ;
        #    		iso_minute:effort = [60 60] ;
        #
        #    // global attributes:
        #    }

        # So, let's use the latter for now:
        milli_psd["iso_minute"].attrs["effort"] = self.num_secs_per_minute

        info(f"Resulting milli_psd={milli_psd}")

        self.iso_minutes = []
        self.num_secs_per_minute = []
        return milli_psd

    def get_milli_psd(self, data: np.ndarray, iso_minute: str) -> xr.DataArray:
        """
        Convenience to get the millidecade bands for a single segment of data
        """
        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        # Convert the spectrum to a datarray
        psd_da = xr.DataArray(
            data=[spectrum],
            coords={"iso_minute": [iso_minute], "frequency": fbands},
            dims=["iso_minute", "frequency"],
        )

        milli_psd = self.subset_result(psd_da)
        milli_psd = cast(xr.DataArray, 10 * np.log10(milli_psd) + APPROX_FLAT_SENSITIVITY)
        milli_psd.name = "psd"
        return milli_psd

    def subset_result(self, da: xr.DataArray) -> xr.DataArray:
        if self.subset_to is None:
            return da

        info(f"subsetting to {self.subset_to}")
        bands_c = self.bands_c
        bands_limits = self.bands_limits

        start_hz, end_hz = self.subset_to
        start_index = 0
        while bands_c[start_index] < start_hz:
            start_index += 1
        end_index = start_index
        while bands_c[end_index - 1] < end_hz:
            end_index += 1
        bands_c = bands_c[start_index:end_index]
        new_bands_c_len = len(bands_c)
        bands_limits = bands_limits[start_index : start_index + new_bands_c_len + 1]

        def print_array(name: str, arr: np.ndarray):
            info(f"{name} ({len(arr)}) = {brief_list(arr)}")

        print_array("       bands_c", bands_c)
        print_array("  bands_limits", bands_limits)

        return utils.spectra_ds_to_bands(
            da,
            bands_limits,
            bands_c,
            fft_bin_width=self.fs / self.nfft,
            db=False,
        )
