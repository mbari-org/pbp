import os
from math import ceil, floor
from typing import Generator, Optional, Tuple

import numpy as np
import soundfile as sf

from src.json_support import parse_json_lines_file


def done(at_hour: int, at_minute: int, at_seconds: int) -> bool:
    return at_hour == 23 and at_minute == 59 and at_seconds >= 60


class FileHelper:
    """
    Helps loading audio segments.
    """

    def __init__(
        self,
        json_base_dir: str,
        audio_base_dir: Optional[str] = None,
        segment_size_in_secs: int = 60,
    ):
        """

        :param json_base_dir:
          Directory containing the YYYYMMDD.json json-lines files
        :param audio_base_dir:
          If given, this will be the base directory to use when the JSON `path` attribute is relative
          (not starting with a slash).
        """
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir
        self.segment_size_in_secs = segment_size_in_secs

        # the following set by select_day:
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.day: Optional[int] = None
        self.json_filename: Optional[str] = None

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
        print(f"day selected: {year:04}{month:02}{day:02}")
        return True

    def gen_audio_segments(self) -> Generator[np.ndarray, None, None]:
        """
        Generate audio segments of the given size for the selected day.
        """
        assert self.json_filename is not None

        print(f"gen_audio_segments: segment_size_in_secs={self.segment_size_in_secs}")

        at_hour, at_minute, at_seconds = 0, 0, 0

        # ad_hoc_prefix = "/Volumes"
        ad_hoc_prefix = ""

        num = 0
        json_entries = parse_json_lines_file(self.json_filename)
        for tme in json_entries:
            wav_filename = (
                f"{ad_hoc_prefix}{tme.path}"
                if tme.path.startswith("/")
                else f"{self.audio_base_dir}/{tme.path}"
            )

            print(f"{wav_filename}:")

            sample_rate = get_sample_rate(wav_filename)
            if sample_rate is None:
                return

            with sf.SoundFile(wav_filename) as f:
                start_time_secs = (at_hour * 60 + at_minute) * 60 + at_seconds
                start_sample = floor(start_time_secs * sample_rate)
                num_samples = ceil(self.segment_size_in_secs * sample_rate)

                print(f"  loading {num_samples:,} samples starting at {start_sample:,}")

                f.seek(start_sample)
                audio_segment = f.read(num_samples)
                yield audio_segment

                at_hour, at_minute, at_seconds = self.next_segment(
                    at_hour, at_minute, at_seconds
                )

                if done(at_hour, at_minute, at_seconds):
                    break

                num += 1  # only for tetsing
                if num >= 2:
                    break

        if done(at_hour, at_minute, at_seconds):
            print("DONE.")
        else:
            print(f"Could only process until {at_hour:02}:{at_minute:02}:{at_seconds:02}")

    def next_segment(
        self, at_hour: int, at_minute: int, at_seconds: int
    ) -> Tuple[int, int, int]:
        """
        Returns the next segment time.
        """
        at_seconds += self.segment_size_in_secs
        if at_seconds >= 60:
            at_seconds = 0
            at_minute += 1
        if at_minute >= 60:
            at_minute = 0
            at_hour += 1
        return at_hour, at_minute, at_seconds


def get_sample_rate(wav_filename: str) -> Optional[int]:
    """
    Returns the sample rate of the given WAV file.
    """
    try:
        _, sample_rate = sf.read(wav_filename, start=0, frames=0)
        # print(f"  sample_rate = {sample_rate}")
        return sample_rate
    except sf.LibsndfileError as e:
        print(f"ERROR: {e}")
        return None
