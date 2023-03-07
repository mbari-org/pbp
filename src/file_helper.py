import os
from math import ceil, floor
from typing import List, Optional, Tuple

import numpy as np
import soundfile as sf

from src.json_support import (
    get_intersecting_entries,
    parse_json_file,
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
        audio_path_prefix: str = "",
        segment_size_in_mins: int = 1,
    ):
        """

        :param json_base_dir:
          Directory containing the `YYYYMMDD.json` json files
        :param audio_base_dir:
          If given, it will be used as base directory for any relative (not starting with a slash)
          `path` attribute in the json entries.
        :param audio_path_prefix:
          Ad hoc path prefix for wav locations, e.g. "/Volumes"
        :param segment_size_in_mins:
            The size of each audio segment to extract, in minutes. By default, 1.
        """
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir
        self.audio_path_prefix = audio_path_prefix
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
        self.json_entries = list(parse_json_file(self.json_filename))
        print(f"Day selected: {year:04}{month:02}{day:02}")
        return True

    def extract_audio_segment(
        self, at_hour: int, at_minute: int
    ) -> Optional[Tuple[sf._SoundFileInfo, np.ndarray]]:
        """
        Extracts the audio segment at the given start time.
        For this it loads and aggregates the relevant audio segments.

        :return:  A tuple (audio_info, audio_segment) or None
        """

        assert self.json_entries is not None
        assert self.year is not None
        assert self.month is not None
        assert self.day is not None

        intersections: List[TMEIntersection] = get_intersecting_entries(
            self.json_entries,
            self.segment_size_in_mins,
            self.year,
            self.month,
            self.day,
            at_hour,
            at_minute,
        )

        audio_info: Optional[sf._SoundFileInfo] = None

        aggregated_segment: Optional[np.ndarray] = None

        prefix = f"({at_hour:02}h:{at_minute:02}m)"
        for intersection in intersections:
            if intersection.tme.path.startswith("/"):
                wav_filename = f"{self.audio_path_prefix}{intersection.tme.path}"
            else:
                wav_filename = f"{self.audio_base_dir}/{intersection.tme.path}"
            print(f"    {prefix} {intersection.duration_secs} secs from {wav_filename}")

            ai = _get_audio_info(wav_filename)
            if (
                ai is None
                or audio_info is not None
                and not _check_audio_info(audio_info, ai)
            ):
                return None
            audio_info = ai

            start_sample = floor(intersection.start_secs * audio_info.samplerate)
            num_samples = ceil(intersection.duration_secs * audio_info.samplerate)

            with sf.SoundFile(wav_filename) as f:
                # print(f"  loading {num_samples:,} samples starting at {start_sample:,}")

                try:
                    new_pos = f.seek(start_sample)
                    if new_pos != start_sample:
                        print(
                            f"ERROR: expected to seek to {start_sample:,} but got {new_pos:,}"
                        )
                        return None
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

        if aggregated_segment is not None:
            return audio_info, aggregated_segment
        return None


def _get_audio_info(wav_filename: str) -> Optional[sf._SoundFileInfo]:
    try:
        return sf.info(wav_filename)
    except sf.LibsndfileError as e:
        print(f"ERROR: {e}")
        return None


def _check_audio_info(ai1: sf._SoundFileInfo, ai2: sf._SoundFileInfo) -> bool:
    if ai1.samplerate != ai2.samplerate:
        print(f"UNEXPECTED: sample rate mismatch: {ai1.samplerate} vs {ai2.samplerate}")
        return False
    if ai1.channels != ai2.channels:
        print(f"UNEXPECTED: channel count mismatch: {ai1.channels} vs {ai2.channels}")
        return False
    if ai1.subtype != ai2.subtype:
        print(f"UNEXPECTED: subtype mismatch: {ai1.subtype} vs {ai2.subtype}")
        return False
    return True
