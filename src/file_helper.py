import os
from math import ceil, floor
from typing import Generator, List, Optional

import numpy as np
import soundfile as sf

from src.json_support import (
    get_intersecting_entries,
    parse_json_lines_file,
    TME,
    TMEIntersection,
)
from src.misc_helper import gen_hour_minute_times


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
          If given, this will be the base directory to use when the JSON `path` attribute is relative
          (not starting with a slash).
        :param segment_size_in_mins:
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
        Select the given day for subsequent processing of relevant audio segments.
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
        print(f"day selected: {year:04}{month:02}{day:02}")
        return True

    def gen_audio_segments(self) -> Generator[np.ndarray, None, None]:
        """
        Return audio segments of the given size for the selected day.
        """
        assert self.json_entries is not None

        print(f"gen_audio_segments: segment_size_in_mins={self.segment_size_in_mins}")

        for at_hour, at_minute in gen_hour_minute_times(self.segment_size_in_mins):
            segment = self.load_audio_segment(at_hour, at_minute)
            if segment is not None:
                yield segment
            else:
                print(f"ERROR: cannot get audio segment at {at_hour:02}:{at_minute:02}")
                return

    def load_audio_segment(self, at_hour: int, at_minute: int) -> Optional[np.ndarray]:
        """
        Returns the next audio segment at the given time by loading and intersecting the relevant
        audio files.
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

        aggregated_segment: np.ndarray = np.ndarray([])

        segment_size_in_secs = self.segment_size_in_mins * 60

        for intersection in intersections:
            ad_hoc_prefix = ""  # "/Volumes"
            wav_filename = (
                f"{ad_hoc_prefix}{intersection.tme.path}"
                if intersection.tme.path.startswith("/")
                else f"{self.audio_base_dir}/{intersection.tme.path}"
            )
            print(f"{wav_filename}:")
            sample_rate = get_sample_rate(wav_filename)

            with sf.SoundFile(wav_filename) as f:
                start_sample = floor(intersection.start_secs * sample_rate)
                num_samples = ceil(segment_size_in_secs * sample_rate)

                print(f"  loading {num_samples:,} samples starting at {start_sample:,}")

                f.seek(start_sample)
                audio_segment = f.read(num_samples)
                aggregated_segment = np.concatenate((aggregated_segment, audio_segment))

        return aggregated_segment


def get_sample_rate(wav_filename: str) -> Optional[int]:
    """
    Returns the sample rate of the given WAV file.
    """
    try:
        _, sample_rate = sf.read(wav_filename, start=0, frames=0)
        return sample_rate
    except sf.LibsndfileError as e:
        print(f"ERROR: {e}")
        return None
