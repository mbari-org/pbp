from datetime import datetime
from typing import cast, List, Optional, Tuple

import numpy as np
import pypam.signal as sig

import xarray as xr
from pypam import utils

from src.misc_helper import brief_list, debug, info


class PypamSupport:
    def __init__(self) -> None:
        """
        Creates a helper to perform PyPAM calculations according to given parameters.

        For a day of processing, the overall sequence is:

        `add_missing_segment` can be called before calling `set_parameters`.
        This helps with days with no data at the beginning.

        Call `set_parameters` as soon as you get the first audio segment for a day.

        Then you can call `add_segment` or `add_missing_segment` as appropriate
        for each segment until covering the day.

        Finally, call `process_captured_segments` and `get_aggregated_milli_psd`
        to get the result.

        You can then call `reset` before starting a new day processing.
        """

        # to capture reported segments (missing and otherwise):
        self.captured_segments: List[Tuple[datetime, Optional[np.ndarray]]] = []
        self.num_actual_segments: int = 0

        # The following determined when `set_parameters` is called:

        self.fs: Optional[int] = None
        self.nfft: Optional[int] = None
        self.subset_to: Optional[Tuple[int, int]] = None
        self.bands_limits: List[float] = []
        self.bands_c: List[float] = []
        self.fbands: Optional[np.ndarray] = None
        self.spectra: List[np.ndarray] = []
        self.iso_minutes: List[datetime] = []
        self.effort: List[np.float32] = []  # num secs per minute
        # TODO final effort type still TBD

    def set_parameters(
        self, fs: int, nfft: int = 0, subset_to: Optional[Tuple[int, int]] = None
    ):
        """
        Call this as soon as you get the first audio segment for a day,
        in particular, to set the sampling frequency.

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
        Adds a missing segment to the ongoing processing.
        This method can be called even before `set_parameters` is called.

        :param dt:
            The datetime of the start of the missing segment.
        """
        info(f"  capturing segment: {dt}  (MISSING)")

        self.captured_segments.append((dt, None))

    def add_segment(self, data: np.ndarray, dt: datetime):
        """
        Adds an audio segment to the ongoing processing.

        `set_parameters` must have been called first.

        :param data:
            The audio data.
        :param dt:
            The datetime of the start of the segment.
        """
        assert self.parameters_set()

        info(f"  capturing segment: {dt}")
        self.captured_segments.append((dt, data))
        self.num_actual_segments += 1

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

        # use first actual segment to determine the number of data points
        # for the missing segments:
        actual = next(s for s in self.captured_segments if s[1] is not None)
        assert actual is not None, "unexpected: no actual segment found"
        _, data = actual
        data_len_for_missing = len(data)

        self.spectra = []
        self.iso_minutes = []
        self.effort = []

        # now, process all segments:
        for dt, data in self.captured_segments:
            self.iso_minutes.append(dt)

            if data is None:
                num_secs = 0
                info(f"  adding segment: {dt} (MISSING)")
                data = np.nan(data_len_for_missing)
            else:
                num_secs = len(data) / self.fs
                info(f"  adding segment: {dt} ({num_secs} secs used)")

            signal = sig.Signal(data, fs=self.fs)
            signal.set_band(None)
            self.fbands, spectrum, _ = signal.spectrum(
                scaling="density", nfft=self.nfft, db=False, overlap=0.5, force_calc=True
            )
            self.spectra.append(spectrum)

            self.effort.append(np.float32(num_secs))

    def get_aggregated_milli_psd(
        self,
        sensitivity_da: Optional[xr.DataArray] = None,
        sensitivity_flat_value: Optional[float] = None,
    ) -> xr.DataArray:
        """
        Gets the resulting hybrid millidecade bands for the ongoing processing.

        `process_captured_segments` must have been called first.

        After this call, you must call `reset` if you want to start a new day
        processing with this helper object.

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
            coords={"time": self.iso_minutes, "frequency": self.fbands},
            dims=["time", "frequency"],
        )

        psd_da = self.spectra_to_bands(psd_da)
        debug(f"  {psd_da.frequency_bins=}")
        psd_da = apply_sensitivity(psd_da, sensitivity_da, sensitivity_flat_value)

        # just need single precision:
        psd_da = psd_da.astype(np.float32)
        psd_da["frequency"] = psd_da.frequency_bins.astype(np.float32)
        del psd_da["frequency_bins"]

        milli_psd = psd_da
        milli_psd.name = "psd"

        info(f"Resulting milli_psd={milli_psd}")

        return milli_psd

    def get_effort(self) -> List[np.float32]:
        return self.effort

    def reset(self):
        """
        Resets this helper instance in preparation for a new day.
        """
        self.captured_segments = []
        self.num_actual_segments = 0

        self.fs = None
        self.nfft = None
        self.subset_to = None
        self.bands_limits = []
        self.bands_c = []
        self.fbands = None
        self.spectra = []
        self.iso_minutes = []
        self.effort = []

    def spectra_to_bands(self, psd_da: xr.DataArray) -> xr.DataArray:
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
    # TODO but this is still one pending aspect to finalize.

    if sensitivity_da is not None:
        freq_subset = sensitivity_da.interp(frequency=psd_da.frequency_bins)
        info(f"  Applying sensitivity({len(freq_subset.values)})={freq_subset}")
        psd_da += freq_subset.values
    elif sensitivity_flat_value is not None:
        info(f"  applying {sensitivity_flat_value=}")
        psd_da += sensitivity_flat_value

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
