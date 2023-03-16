from math import ceil, floor
from typing import List, Optional, Tuple
from urllib.parse import ParseResult, urlparse

import numpy as np
import soundfile as sf
from botocore.client import BaseClient, ClientError

from src.json_support import (
    get_intersecting_entries,
    parse_json_contents,
    TME,
    TMEIntersection,
)
from src.misc_helper import debug, error, info, map_prefix, warn


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
        s3_client: Optional[BaseClient] = None,
        download_dir: Optional[str] = None,
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
        :param s3_client:
            If given, it will be used to handle `s3:` based uris.
        :param download_dir:
            Save downloaded S3 files here if given, otherwise, save in current directory.
        """
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir
        self.audio_path_map_prefix = audio_path_map_prefix
        self.audio_path_prefix = audio_path_prefix
        self.segment_size_in_mins = segment_size_in_mins
        self.s3_client = s3_client
        self.download_dir: str = download_dir if download_dir else "."

        # the following set by select_day:
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.day: Optional[int] = None
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

        json_uri = f"{self.json_base_dir}/{year:04}/{year:04}{month:02}{day:02}.json"
        json_contents = self._get_json(json_uri)
        if json_contents is None:
            error(f"{json_uri}: file not found\n")
            return False

        self.year = year
        self.month = month
        self.day = day
        self.json_entries = list(parse_json_contents(json_contents))
        return True

    def _get_json(self, uri: str) -> Optional[str]:
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == "s3":
            return self._get_json_s3(parsed_uri)
        #  simply assume local file:
        return _get_json_local(parsed_uri.path)

    def _get_json_s3(self, parsed_uri: ParseResult) -> Optional[str]:
        local_filename = self._download(parsed_uri)
        if local_filename is None:
            return None
        return _get_json_local(local_filename)

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
            if intersection.duration_secs == 0:
                warn("No data from intersection")
                continue

            wav_filename = self._get_wav_filename(intersection.tme.uri)
            if wav_filename is None:
                return None  # error!

            info(f"    {prefix} {intersection.duration_secs} secs from {wav_filename}")

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
                            warn(
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

    def _get_wav_filename(self, uri: str) -> Optional[str]:
        debug(f"_get_wav_filename: uri={uri}")
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == "s3":
            return self._get_wav_filename_s3(parsed_uri)

        uri = map_prefix(self.audio_path_map_prefix, uri)
        path = urlparse(uri).path
        if path.startswith("/"):
            wav_filename = f"{self.audio_path_prefix}{path}"
        else:
            wav_filename = f"{self.audio_base_dir}/{path}"
        return wav_filename

    def _get_wav_filename_s3(self, parsed_uri: ParseResult) -> Optional[str]:
        return self._download(parsed_uri)

    def _download(self, parsed_uri: ParseResult) -> Optional[str]:
        assert self.s3_client is not None

        bucket, key, simple = get_bucket_key_simple(parsed_uri)
        local_filename = f"{self.download_dir}/{simple}"
        info(f"Downloading bucket={bucket} key={key} to {local_filename}")
        try:
            self.s3_client.download_file(bucket, key, local_filename)
            return local_filename
        except ClientError as e:
            error(f"Error downloading {bucket}/{key}: {e}")
            return None


def get_bucket_key_simple(parsed_uri: ParseResult) -> Tuple[str, str, str]:
    bucket = parsed_uri.netloc
    key = parsed_uri.path.lstrip("/")
    simple = key.split("/")[-1] if "/" in key else key
    assert "/" not in simple, f"Unexpected simple_filename: '{simple}'"
    return bucket, key, simple


def _get_json_local(filename: str) -> Optional[str]:
    try:
        with open(filename, "r", encoding="UTF-8") as f:
            return f.read()
    except IOError as e:
        error(f"Error reading {filename}: {e}")
        return None


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
