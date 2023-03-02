import os
from math import ceil, floor
from typing import List, Optional

import numpy as np
import soundfile as sf

from src.json_support import (
    get_intersecting_entries,
    parse_json_lines_file,
    TME,
    TMEIntersection,
)


class FileHelper:
    """
    Helps loading audio segments.
    """

    def __init__(
        self,
        json_base_dir: str,
        audio_base_dir: Optional[str] = None,
        segment_size_in_mins: int = 1,
    ):
        """

        :param json_base_dir:
          Directory containing the YYYYMMDD.json json-lines files
        :param audio_base_dir:
          If given, it will be used as base directory for any relative (not starting with a slash)
          `path` attribute in the json entries.
        :param segment_size_in_mins:
            The size of each audio segment to extract, in minutes. By default, 1.
        """
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir
        self.segment_size_in_mins = segment_size_in_mins

        # the following set by select_day:
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.day: Optional[int] = None
        self.json_filename: Optional[str] = None
        self.json_entries: Optional[List[TME]] = None

    def select_day(self, year: int, month: int, day: int) -> bool:
        """
        Selects the given day for subsequent processing of relevant audio segments.

        :param year:
        :param month:
        :param day:
        :return:  True only if selection was successful
        """

        json_filename = f"{self.json_base_dir}/{year:04}{month:02}{day:02}.json"
        if not os.path.isfile(json_filename):
            print(f"ERROR: {self.json_filename}: file not found\n")
            return False

        self.year = year
        self.month = month
        self.day = day
        self.json_filename = json_filename
        self.json_entries = list(parse_json_lines_file(self.json_filename))
        print(f"Day selected: {year:04}{month:02}{day:02}")
        return True

    def extract_audio_segment(self, at_hour: int, at_minute: int) -> Optional[np.ndarray]:
        """
        Extracts the audio segment at the given start time.
        For this it loads and aggregates the relevant audio segments.
        """

        intersections: List[TMEIntersection] = get_intersecting_entries(
            self.json_entries,
            self.segment_size_in_mins,
            self.year,
            self.month,
            self.day,
            at_hour,
            at_minute,
        )

        aggregated_segment: Optional[np.ndarray] = None

        segment_size_in_secs = self.segment_size_in_mins * 60

        for intersection in intersections:
            ad_hoc_prefix = (
                "/Volumes"  # like "/Volumes", for some preliminary testing -- TODO remove
            )
            wav_filename = (
                f"{ad_hoc_prefix}{intersection.tme.path}"
                if intersection.tme.path.startswith("/")
                else f"{self.audio_base_dir}/{intersection.tme.path}"
            )
            print(f"  from {wav_filename}:")
            sample_rate = _get_sample_rate(wav_filename)

            with sf.SoundFile(wav_filename) as f:
                start_sample = floor(intersection.start_secs * sample_rate)
                num_samples = ceil(segment_size_in_secs * sample_rate)

                # print(f"  loading {num_samples:,} samples starting at {start_sample:,}")

                try:
                    f.seek(start_sample)
                    audio_segment = f.read(num_samples)
                except sf.LibsndfileError as e:
                    print(f"ERROR: {e}")
                    return None

                if aggregated_segment is None:
                    aggregated_segment = audio_segment
                else:
                    aggregated_segment = np.concatenate(
                        (aggregated_segment, audio_segment)
                    )

        return aggregated_segment


def _get_sample_rate(wav_filename: str) -> Optional[int]:
    """
    Returns the sample rate of the given WAV file.
    """
    try:
        _, sample_rate = sf.read(wav_filename, start=0, frames=0)
        return sample_rate
    except sf.LibsndfileError as e:
        print(f"ERROR: {e}")
        return None
