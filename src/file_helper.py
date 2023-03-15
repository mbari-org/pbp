import os
from math import ceil, floor
from typing import List, Optional, Tuple
from urllib.parse import urlparse

import numpy as np
import soundfile as sf

from src.json_support import (
    get_intersecting_entries,
    parse_json_file,
    TME,
    TMEIntersection,
)
from src.misc_helper import error, info, map_prefix, warn


class FileHelper:
    """
    Helps loading audio segments.
    """

    def __init__(
        self,
        json_base_dir: str,
        audio_base_dir: Optional[str] = None,
        audio_path_map_prefix: str = "",
        audio_path_prefix: str = "",
        segment_size_in_mins: int = 1,
    ):
        """

        :param json_base_dir:
          Directory containing the `YYYYMMDD.json` json files
        :param audio_base_dir:
          If given, it will be used as base directory for any relative (not starting with a slash)
          `path` attribute in the json entries.
        :param audio_path_map_prefix:
          Prefix mapping to get actual audio uri to be used.
          Example: `s3://pacific-sound-256khz-2022~file:///PAM_Archive/2022`
        :param audio_path_prefix:
          Ad hoc path prefix for wav locations, e.g. "/Volumes"
        :param segment_size_in_mins:
            The size of each audio segment to extract, in minutes. By default, 1.
        """
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir
        self.audio_path_map_prefix = audio_path_map_prefix
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

        info(f"Selecting day: {year:04}{month:02}{day:02}")

        json_filename = f"{self.json_base_dir}/{year:04}{month:02}{day:02}.json"
        if not os.path.isfile(json_filename):
            error(f"{json_filename}: file not found\n")
            return False

        self.year = year
        self.month = month
        self.day = day
        self.json_filename = json_filename
        self.json_entries = list(parse_json_file(self.json_filename))
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
            wav_filename = self._get_wav_filename(intersection.tme.uri)
            info(f"    {prefix} {intersection.duration_secs} secs from {wav_filename}")

            if intersection.duration_secs == 0:
                warn("No data from intersection")
                continue

            ai = _get_audio_info(wav_filename)
            if (
                ai is None
                or audio_info is not None
                and not _check_audio_info(audio_info, ai)
            ):
                return None  # error!

            audio_info = ai

            start_sample = floor(intersection.start_secs * audio_info.samplerate)
            num_samples = ceil(intersection.duration_secs * audio_info.samplerate)

            with sf.SoundFile(wav_filename) as f:
                # info(f"  loading {num_samples:,} samples starting at {start_sample:,}")

                try:
                    new_pos = f.seek(start_sample)
                    if new_pos != start_sample:
                        # no-data case, let's just read 0 samples to get an empty array:
                        audio_segment = f.read(0)
                    else:
                        audio_segment = f.read(num_samples)
                        if len(audio_segment) < num_samples:
                            # partial-data case.
                            info(
                                f"!!! partial data: {len(audio_segment)} < {num_samples}"
                            )

                except sf.LibsndfileError as e:
                    error(f"{e}")
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

    def _get_wav_filename(self, uri: str) -> str:
        # TODO note, we still assume local files.
        uri = map_prefix(self.audio_path_map_prefix, uri)
        path = urlparse(uri).path
        if path.startswith("/"):
            wav_filename = f"{self.audio_path_prefix}{path}"
        else:
            wav_filename = f"{self.audio_base_dir}/{path}"
        return wav_filename


def _get_audio_info(wav_filename: str) -> Optional[sf._SoundFileInfo]:
    try:
        return sf.info(wav_filename)
    except sf.LibsndfileError as e:
        error(f"{e}")
        return None


def _check_audio_info(ai1: sf._SoundFileInfo, ai2: sf._SoundFileInfo) -> bool:
    if ai1.samplerate != ai2.samplerate:
        error(f"UNEXPECTED: sample rate mismatch: {ai1.samplerate} vs {ai2.samplerate}")
        return False
    if ai1.channels != ai2.channels:
        error(f"UNEXPECTED: channel count mismatch: {ai1.channels} vs {ai2.channels}")
        return False
    if ai1.subtype != ai2.subtype:
        error(f"UNEXPECTED: subtype mismatch: {ai1.subtype} vs {ai2.subtype}")
        return False
    return True
