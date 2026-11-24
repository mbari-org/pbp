from datetime import date as date_type
from typing import List, Optional, Tuple


def check_date(date: Optional[str]) -> List[str]:
    """
    Checks the given date, which is expected in YYYYMMDD format.

    Returns:
        List of error messages, empty if no errors.
    """
    if not date:
        return ["- date not given"]
    if not (date.isdigit() and len(date) == 8):
        return [f"- date must be in YYYYMMDD format, got '{date}'"]
    try:
        date_type(int(date[:4]), int(date[4:6]), int(date[6:8]))
    except ValueError as e:
        return [f"- invalid date '{date}': {e}"]
    return []


def check_hmb_gen_params(
    time_resolution: Optional[int] = None,
    exclude_tone_calibration_seconds: Optional[int] = None,
    max_segments: Optional[int] = None,
    subset_to: Optional[Tuple[int, int]] = None,
) -> List[str]:
    """
    Checks HMB generation parameters that can be validated before any audio
    is read, so the user can be told upfront instead of getting a failed or
    degraded product after processing.

    Returns:
        List of error messages, empty if no errors.
    """
    errors: List[str] = []

    # The spectrum is computed with nfft = sample rate, that is, one second
    # of audio, so a shorter segment cannot produce a spectrum.
    if time_resolution is not None and time_resolution < 1:
        errors.append(
            f"- time resolution must be at least 1 second, got {time_resolution}"
        )

    if (
        exclude_tone_calibration_seconds is not None
        and exclude_tone_calibration_seconds < 0
    ):
        errors.append(
            "- exclude tone calibration seconds must be non-negative,"
            f" got {exclude_tone_calibration_seconds}"
        )

    if max_segments is not None and max_segments < 0:
        errors.append(f"- max segments must be non-negative, got {max_segments}")

    if subset_to is not None:
        lower, upper = subset_to
        if lower < 0 or lower >= upper:
            errors.append(
                f"- subset_to must satisfy 0 <= lower < upper, got ({lower}, {upper})"
            )

    return errors
