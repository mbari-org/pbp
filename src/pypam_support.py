from dataclasses import dataclass
from datetime import datetime
from typing import cast, List, Optional, Tuple

import numpy as np
import pypam.signal as sig

import xarray as xr
from pypam import utils

from src.misc_helper import brief_list, debug, info


@dataclass
class CapturedSegment:
    dt: datetime
    num_secs: float
    spectrum: Optional[np.ndarray]


class PypamSupport:
    def __init__(self) -> None:
        """
        Creates a helper to process audio segments for a given day,
        resulting in the aggregated hybrid millidecade PSD product.

        The created instance should be used only for a day of processing.

        The overall call sequence is:

        `add_missing_segment` can be called before calling `set_parameters`.
        This allows capturing initial segments with no data for the day.

        Call `set_parameters` as soon as you get the first audio segment for a day.
        Such segment is used to determine the sampling frequency.

        Then you can call `add_segment` or `add_missing_segment` as appropriate
        for each subsequent segment until covering the day.

        When all segments have been captured, call `process_captured_segments`
        and then `get_effort` and `get_aggregated_milli_psd` to get the effort
        and result.
        """

        # to capture reported segments (missing and otherwise):
        self.captured_segments: List[CapturedSegment] = []
        self.num_actual_segments: int = 0

        # The following determined when `set_parameters` is called:

        self.fs: Optional[int] = None
        self.nfft: Optional[int] = None
        self.subset_to: Optional[Tuple[int, int]] = None
        self.bands_limits: List[float] = []
        self.bands_c: List[float] = []
        self.fbands: Optional[np.ndarray] = None
        self.spectra: List[np.ndarray] = []
        self.times: List[datetime] = []
        self.effort: List[np.float32] = []  # num secs per minute

    def set_parameters(
        self, fs: int, nfft: int = 0, subset_to: Optional[Tuple[int, int]] = None
    ):
        """
        Call this as soon as you get the first audio segment for a day,
        in particular, to set the sampling frequency used for subsequent calculations.

        :param fs:
            Sampling frequency.
        :param nfft:
            Number of samples to use for the FFT. If 0, it will be set to `fs`.
        :param subset_to:
            If not None, the product for a day will get the resulting PSD
            subset to `[lower, upper)`, in terms of central frequency.
        """
        assert fs > 0
        self.fs = fs
        self.nfft = nfft if nfft > 0 else self.fs

        self.subset_to = subset_to
        band = [0, self.fs / 2]  # for now.

        debug(f"PypamSupport: {subset_to=} {band=}")

        self.bands_limits, self.bands_c = utils.get_hybrid_millidecade_limits(
            band=band, nfft=self.nfft
        )

    def parameters_set(self) -> bool:
        """
        Returns True if `set_parameters` has been called.
        """
        return self.fs is not None

    def add_missing_segment(self, dt: datetime):
        """
        Adds a missing segment to the ongoing aggregation.
        This method can be called even before `set_parameters` is called.

        :param dt:
            The datetime of the start of the missing segment.
        """
        self.captured_segments.append(CapturedSegment(dt, 0, None))
        info(f"  captured segment: {dt}  (NO DATA)")

    def add_segment(self, data: np.ndarray, dt: datetime):
        """
        Adds an audio segment to the ongoing aggregation.

        `set_parameters` must have been called first.

        :param data:
            The audio data.
        :param dt:
            The datetime of the start of the segment.
        """
        assert self.parameters_set()
        assert self.fs is not None

        num_secs = len(data) / self.fs
        self.fbands, spectrum = self._get_spectrum(data)
        self.captured_segments.append(CapturedSegment(dt, num_secs, spectrum))
        self.num_actual_segments += 1
        info(f"  captured segment: {dt}")

    def get_num_actual_segments(self) -> int:
        """
        Gets the number of actual (non-missing) segments so far.
        """
        return self.num_actual_segments

    def process_captured_segments(self):
        """
        Processes the captured segments.
        At least one actual segment must have been captured.
        """
        assert self.get_num_actual_segments() > 0

        # Use any actual segment to determine NaN spectrum for the missing segments:
        actual = next(s for s in self.captured_segments if s.spectrum is not None)
        assert actual is not None, "unexpected: no actual segment found"
        nan_spectrum = np.full(len(actual.spectrum), np.nan)

        # gather resulting variables:
        self.times = []
        self.effort = []
        self.spectra = []
        for cs in self.captured_segments:
            self.times.append(cs.dt)
            self.effort.append(np.float32(cs.num_secs))

            spectrum = nan_spectrum if cs.spectrum is None else cs.spectrum
            info(f"  spectrum for: {cs.dt} ({cs.num_secs} secs used)")
            self.spectra.append(spectrum)

    def _get_spectrum(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        signal = sig.Signal(data, fs=self.fs)
        signal.set_band(None)
        fbands, spectrum, _ = signal.spectrum(
            scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
        )
        return fbands, spectrum

    def get_effort(self) -> List[np.float32]:
        """
        Gets the resulting effort.
        `process_captured_segments` must have been called first.
        """
        assert self.get_num_actual_segments() > 0
        assert len(self.spectra) > 0
        return self.effort

    def get_aggregated_milli_psd(
        self,
        sensitivity_da: Optional[xr.DataArray] = None,
        sensitivity_flat_value: Optional[float] = None,
    ) -> xr.DataArray:
        """
        Gets the resulting hybrid millidecade bands for all captured segments.

        `process_captured_segments` must have been called first.

        Calibration is done if either `sensitivity_da` or `sensitivity_flat_value` is given.
        `sensitivity_da` has priority over `sensitivity_flat_value`.
        No calibration is done if neither is given.

        :param sensitivity_da:
            If given, it will be used to calibrate the result.
        :param sensitivity_flat_value:
            If given, and sensitivity_da not given, it will be used to calibrate the result.
        :return:
        """
        assert self.get_num_actual_segments() > 0
        assert len(self.spectra) > 0

        # Convert the spectra to a datarray
        psd_da = xr.DataArray(
            data=self.spectra,
            coords={"time": self.times, "frequency": self.fbands},
            dims=["time", "frequency"],
        )

        psd_da = self._spectra_to_bands(psd_da)
        debug(f"  {psd_da.frequency_bins=}")
        psd_da = apply_sensitivity(psd_da, sensitivity_da, sensitivity_flat_value)

        # just need single precision:
        psd_da = psd_da.astype(np.float32)
        psd_da["frequency"] = psd_da.frequency_bins.astype(np.float32)
        del psd_da["frequency_bins"]

        # TODO get dimensions in order "time" then "frequency"
        # psd_da = psd_da.transpose("time", "frequency_bins")

        milli_psd = psd_da
        milli_psd.name = "psd"

        info(f"Resulting milli_psd={milli_psd}")

        return milli_psd

    def _spectra_to_bands(self, psd_da: xr.DataArray) -> xr.DataArray:
        assert self.fs is not None
        assert self.nfft is not None

        bands_limits, bands_c = self.bands_limits, self.bands_c
        if self.subset_to is not None:
            bands_limits, bands_c = adjust_limits(bands_limits, bands_c, self.subset_to)

        def print_array(name: str, arr: List[float]):
            info(f"{name} ({len(arr)}) = {brief_list(arr)}")

        print_array("       bands_c", bands_c)
        print_array("  bands_limits", bands_limits)

        psd_da = utils.spectra_ds_to_bands(
            psd_da,
            bands_limits,
            bands_c,
            fft_bin_width=self.fs / self.nfft,
            db=False,
        )

        psd_da = psd_da.drop_vars(["lower_frequency", "upper_frequency"])
        return psd_da


def apply_sensitivity(
    psd_da: xr.DataArray,
    sensitivity_da: Optional[xr.DataArray],
    sensitivity_flat_value: Optional[float] = None,
) -> xr.DataArray:
    psd_da = cast(xr.DataArray, 10 * np.log10(psd_da))

    # NOTE: per slack discussion today 2023-05-23,
    # apply _addition_ of the given sensitivity
    # (previously, subtraction)
    # 2023-06-12: Back to subtraction (as we're focusing on MARS data at the moment)
    # TODO but this is still one pending aspect to finalize.

    if sensitivity_da is not None:
        freq_subset = sensitivity_da.interp(frequency=psd_da.frequency_bins)
        info(f"  Applying sensitivity({len(freq_subset.values)})={freq_subset}")
        psd_da -= freq_subset.values
    elif sensitivity_flat_value is not None:
        info(f"  Applying {sensitivity_flat_value=}")
        psd_da -= sensitivity_flat_value

    return psd_da


def adjust_limits(
    bands_limits: List[float], bands_c: List[float], subset_to: Tuple[int, int]
) -> Tuple[List[float], List[float]]:
    start_hz, end_hz = subset_to
    info(f"Subsetting to [{start_hz:,}, {end_hz:,})Hz")

    start_index = 0
    while start_index < len(bands_c) and bands_c[start_index] < start_hz:
        start_index += 1
    end_index = start_index
    while end_index < len(bands_c) and bands_c[end_index] < end_hz:
        end_index += 1
    bands_c = bands_c[start_index:end_index]
    new_bands_c_len = len(bands_c)
    bands_limits = bands_limits[start_index : start_index + new_bands_c_len + 1]

    return bands_limits, bands_c
