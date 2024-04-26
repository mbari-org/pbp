from dataclasses import dataclass
from datetime import datetime
from typing import cast, List, Optional, Tuple

import numpy as np
import pypam.signal as sig

import xarray as xr
from pypam import utils

from pbp.misc_helper import brief_list


@dataclass
class ProcessResult:
    """
    The result of processing a day of audio segments when at least one actual segment
    has been captured.
    """

    psd_da: xr.DataArray
    effort_da: xr.DataArray


@dataclass
class _CapturedSegment:
    dt: datetime
    num_secs: float
    spectrum: Optional[np.ndarray]


class PypamSupport:
    def __init__(
        self,
        log,  #: loguru.Logger
    ) -> None:
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
        to get the result.
        """
        self.log = log

        # to capture reported segments (missing and otherwise):
        self._captured_segments: List[_CapturedSegment] = []
        self._num_actual_segments: int = 0

        # Determined from any actual segment:
        self._fbands: Optional[np.ndarray] = None

        # The following determined when `set_parameters` is called:

        self.fs: Optional[int] = None
        self._nfft: Optional[int] = None
        self._subset_to: Optional[Tuple[int, int]] = None
        self._bands_limits: List[float] = []
        self._bands_c: List[float] = []

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
        self._nfft = nfft if nfft > 0 else self.fs

        self._subset_to = subset_to
        band = [0, self.fs / 2]  # for now.

        self.log.debug(f"PypamSupport: {subset_to=} {band=}")

        self._bands_limits, self._bands_c = utils.get_hybrid_millidecade_limits(
            band=band, nfft=self._nfft
        )

    @property
    def parameters_set(self) -> bool:
        """
        True if `set_parameters` has already been called.
        """
        return self.fs is not None

    def add_missing_segment(self, dt: datetime):
        """
        Adds a missing segment to the ongoing aggregation.
        This method can be called even before `set_parameters` is called.

        :param dt:
            The datetime of the start of the missing segment.
        """
        self._captured_segments.append(_CapturedSegment(dt, 0, None))
        self.log.debug(f"  captured segment: {dt}  (NO DATA)")

    def add_segment(self, dt: datetime, data: np.ndarray):
        """
        Adds an audio segment to the ongoing aggregation.

        `set_parameters` must have been called first.

        :param dt:
            The datetime of the start of the segment.
        :param data:
            The audio data.
        """
        assert self.parameters_set
        assert self.fs is not None
        assert self._nfft is not None

        self._fbands, spectrum = _get_spectrum(data, self.fs, self._nfft)
        num_secs = len(data) / self.fs
        self._captured_segments.append(_CapturedSegment(dt, num_secs, spectrum))
        self._num_actual_segments += 1
        self.log.debug(f"  captured segment: {dt}")

    def process_captured_segments(
        self,
        sensitivity_da: Optional[xr.DataArray] = None,
    ) -> Optional[ProcessResult]:
        """
        Gets the resulting hybrid millidecade bands for all captured segments.
        At least one actual segment must have been captured, otherwise None is returned.

        :param sensitivity_da:
            If given, it will be used to calibrate the result.
        :return:
            Result if at least an actual segment was captured, None otherwise.
        """
        if self._num_actual_segments == 0:
            return None

        # Use any actual segment to determine NaN spectrum for the missing segments:
        actual = next(s for s in self._captured_segments if s.spectrum is not None)
        assert actual is not None, "unexpected: no actual segment found"
        assert actual.spectrum is not None, "unexpected: no actual.spectrum"
        nan_spectrum = np.full(len(actual.spectrum), np.nan)

        # gather resulting variables:
        times: List[np.int64] = []
        effort: List[np.float32] = []
        spectra: List[np.ndarray] = []
        for cs in self._captured_segments:
            times.append(np.int64(cs.dt.timestamp()))
            effort.append(np.float32(cs.num_secs))

            spectrum = nan_spectrum if cs.spectrum is None else cs.spectrum
            self.log.debug(f"  spectrum for: {cs.dt} (effort={cs.num_secs})")
            spectra.append(spectrum)

        self.log.info("Aggregating results ...")
        psd_da = self._get_aggregated_milli_psd(
            times=times,
            spectra=spectra,
            sensitivity_da=sensitivity_da,
        )

        effort_da = xr.DataArray(
            data=effort,
            dims=["time"],
            coords={"time": psd_da.time},
        )
        return ProcessResult(psd_da, effort_da)

    def _get_aggregated_milli_psd(
        self,
        times: List[np.int64],
        spectra: List[np.ndarray],
        sensitivity_da: Optional[xr.DataArray] = None,
    ) -> xr.DataArray:
        # Convert the spectra to a DataArray
        psd_da = xr.DataArray(
            data=spectra,
            coords={"time": times, "frequency": self._fbands},
            dims=["time", "frequency"],
        )

        psd_da = self._spectra_to_bands(psd_da)
        self.log.debug(f"  {psd_da.frequency_bins=}")
        psd_da = self._apply_sensitivity_if_given(psd_da, sensitivity_da)

        # just need single precision:
        psd_da = psd_da.astype(np.float32)
        psd_da["frequency"] = psd_da.frequency_bins.astype(np.float32)
        del psd_da["frequency_bins"]

        milli_psd = psd_da
        milli_psd.name = "psd"

        self.log.info(f"Resulting milli_psd={milli_psd}")

        return milli_psd

    def _apply_sensitivity_if_given(
        self,
        psd_da: xr.DataArray,
        sensitivity_da: Optional[xr.DataArray],
    ) -> xr.DataArray:
        psd_da = cast(xr.DataArray, 10 * np.log10(psd_da))

        # NOTE: per slack discussion today 2023-05-23,
        # apply _addition_ of the given sensitivity
        # (previously, subtraction)
        # 2023-06-12: Back to subtraction (as we're focusing on MARS data at the moment)
        # TODO but this is still one pending aspect to finalize.
        # 2023-08-03: sensitivity_flat_value is handled upstream now.

        if sensitivity_da is not None:
            freq_subset = sensitivity_da.interp(frequency=psd_da.frequency_bins)
            self.log.info(
                f"  Applying sensitivity({len(freq_subset.values)})={freq_subset}"
            )
            psd_da -= freq_subset.values

        return psd_da

    def _spectra_to_bands(self, psd_da: xr.DataArray) -> xr.DataArray:
        assert self.fs is not None
        assert self._nfft is not None

        bands_limits, bands_c = self._bands_limits, self._bands_c
        if self._subset_to is not None:
            bands_limits, bands_c = self._adjust_limits(
                bands_limits, bands_c, self._subset_to
            )

        def print_array(name: str, arr: List[float]):
            self.log.info(f"{name} ({len(arr)}) = {brief_list(arr)}")

        print_array("       bands_c", bands_c)
        print_array("  bands_limits", bands_limits)

        psd_da = utils.spectra_ds_to_bands(
            psd_da,
            bands_limits,
            bands_c,
            fft_bin_width=self.fs / self._nfft,
            db=False,
        )

        psd_da = psd_da.drop_vars(["lower_frequency", "upper_frequency"])
        return psd_da

    def _adjust_limits(
        self, bands_limits: List[float], bands_c: List[float], subset_to: Tuple[int, int]
    ) -> Tuple[List[float], List[float]]:
        start_hz, end_hz = subset_to
        self.log.info(f"Subsetting to [{start_hz:,}, {end_hz:,})Hz")

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


def _get_spectrum(data: np.ndarray, fs: int, nfft: int) -> Tuple[np.ndarray, np.ndarray]:
    signal = sig.Signal(data, fs=fs)
    signal.set_band(None)
    fbands, spectrum, _ = signal.spectrum(
        scaling="density", nfft=nfft, db=False, overlap=0.5, force_calc=True
    )
    return fbands, spectrum
