import logging
import os
import pathlib
from dataclasses import dataclass
from math import ceil, floor
from typing import Dict, List, Optional, Tuple
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
from src.misc_helper import brief_list, debug, error, get_logger, info, map_prefix, warn


@dataclass
class AudioInfo:
    samplerate: int
    channels: int
    subtype: str


class WavStatus:
    # TODO cleanup!  there's some repetition here wrt FileHelper!

    def __init__(
        self,
        uri: str,
        audio_base_dir: Optional[str] = None,
        audio_path_map_prefix: str = "",
        audio_path_prefix: str = "",
        s3_client: Optional[BaseClient] = None,
        download_dir: Optional[str] = None,
    ):
        self.uri = map_prefix(audio_path_map_prefix, uri)
        self.parsed_uri = urlparse(self.uri)

        self.audio_base_dir = audio_base_dir
        self.audio_path_prefix = audio_path_prefix
        self.s3_client = s3_client
        self.download_dir: str = download_dir if download_dir else "."

        self.error = None

        self.wav_filename = self._get_wav_filename()
        if self.wav_filename is None:
            self.error = "error getting wav filename"
            return

        ai = _get_audio_info(self.wav_filename)
        if ai is None:
            self.error = "error getting audio info"
            return

        self.audio_info: AudioInfo = ai
        self.sound_file = sf.SoundFile(self.wav_filename)
        self.age = 0  # see _get_wav_status.

    def _get_wav_filename(self) -> Optional[str]:
        debug(f"_get_wav_filename: {self.uri=}")
        if self.parsed_uri.scheme == "s3":
            return self._get_wav_filename_s3()

        path = self.parsed_uri.path
        if path.startswith("/"):
            wav_filename = f"{self.audio_path_prefix}{path}"
        else:
            wav_filename = f"{self.audio_base_dir}/{path}"
        return wav_filename

    def _get_wav_filename_s3(self) -> Optional[str]:
        return _download(self.parsed_uri, self.s3_client, self.download_dir)

    def remove_downloaded_file(self):
        if not pathlib.Path(self.wav_filename).exists():
            return

        if self.s3_client is None or self.parsed_uri.scheme != "s3":
            debug(f"No file download involved for {self.uri=}")
            return

        try:
            os.remove(self.wav_filename)
            debug(f"Removed cached file {self.wav_filename} for {self.uri=}")
        except OSError as e:
            error(f"Error removing file {self.wav_filename}: {e}")


def _download(
    parsed_uri: ParseResult, s3_client: BaseClient, download_dir: str
) -> Optional[str]:
    """
    Downloads the given S3 URI to the given download directory.
    :param parsed_uri: the URI to download
    :return: Downloaded filename or None if error
    """
    bucket, key, simple = get_bucket_key_simple(parsed_uri)
    local_filename = f"{download_dir}/{simple}"
    info(f"Downloading {bucket=} {key=} to {local_filename}")
    try:
        s3_client.download_file(bucket, key, local_filename)
        return local_filename
    except ClientError as e:
        error(f"Error downloading {bucket}/{key}: {e}")
        return None


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

        self.wav_cache: Dict[str, WavStatus] = {}

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

    def get_local_sensitivity_filename(
        self, sensitivity_uri: Optional[str]
    ) -> Optional[str]:
        """
        Returns the local sensitivity filename, which may be a downloaded one
        when the given uri is s3 based.
        """
        if sensitivity_uri is None:
            return None

        parsed_uri = urlparse(sensitivity_uri)
        if parsed_uri.scheme == "s3":
            return _download(parsed_uri, self.s3_client, self.download_dir)

        return parsed_uri.path

    def day_completed(self):
        """
        Since a process is launched only for day, we simply clear the cache.
        """
        # first, close all wav files still open:
        c_ws_files_open = [
            c_ws for c_ws in self.wav_cache.values() if c_ws.sound_file is not None
        ]
        if len(c_ws_files_open) > 0:
            debug(f"day_completed: closing {len(c_ws_files_open)} wav files still open")
            for c_ws in c_ws_files_open:
                debug(f"Closing sound file for cached {c_ws.uri=} {c_ws.age=}")
                c_ws.sound_file.close()

        # remove any downloaded files (cloud case):
        for c_ws in self.wav_cache.values():
            c_ws.remove_downloaded_file()

        self.wav_cache = {}

    def _get_json(self, uri: str) -> Optional[str]:
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == "s3":
            return self._get_json_s3(parsed_uri)
        #  simply assume local file:
        return _get_json_local(parsed_uri.path)

    def _get_json_s3(self, parsed_uri: ParseResult) -> Optional[str]:
        local_filename = _download(parsed_uri, self.s3_client, self.download_dir)
        if local_filename is None:
            return None
        return _get_json_local(local_filename)

    def extract_audio_segment(
        self, at_hour: int, at_minute: int
    ) -> Optional[Tuple[AudioInfo, np.ndarray]]:
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

        audio_info: Optional[AudioInfo] = None

        aggregated_segment: Optional[np.ndarray] = None

        prefix = f"({at_hour:02}h:{at_minute:02}m)"
        for intersection in intersections:
            if intersection.duration_secs == 0:
                warn("No data from intersection")
                continue

            ws = self._get_wav_status(intersection.tme.uri)
            if ws.error is not None:
                return None

            info(f"    {prefix} {intersection.duration_secs} secs from {ws.wav_filename}")

            if audio_info is not None and not _check_audio_info(
                audio_info, ws.audio_info
            ):
                return None  # error!

            audio_info = ws.audio_info

            start_sample = floor(intersection.start_secs * audio_info.samplerate)
            num_samples = ceil(intersection.duration_secs * audio_info.samplerate)

            try:
                new_pos = ws.sound_file.seek(start_sample)
                if new_pos != start_sample:
                    # no-data case, let's just read 0 samples to get an empty array:
                    audio_segment = ws.sound_file.read(0)
                else:
                    audio_segment = ws.sound_file.read(num_samples)
                    if len(audio_segment) < num_samples:
                        # partial-data case.
                        warn(f"!!! partial data: {len(audio_segment)} < {num_samples}")

            except sf.LibsndfileError as e:
                error(f"{e}")
                return None

            if aggregated_segment is None:
                aggregated_segment = audio_segment
            else:
                aggregated_segment = np.concatenate((aggregated_segment, audio_segment))

        if aggregated_segment is not None:
            assert audio_info is not None
            return audio_info, aggregated_segment
        return None

    def _get_wav_status(self, uri: str) -> WavStatus:
        """
        Returns a WavStatus object for the given uri.
        Internally, the 'age' attribute helps to keep the relevant files open
        as long as recently used. Note that traversal of the files indicated in the
        JSON array happens in a monotonically increasing order in time, so we
        can increment the 'age' for all entries in the cache except for the uri
        just requested.

        :param uri:
        :return:
        """
        debug(f"_get_wav_status: {uri=}")
        ws = self.wav_cache.get(uri)
        if ws is None:
            # currently cached ones get a bit older:
            for c_ws in self.wav_cache.values():
                c_ws.age += 1

            debug(f"WavStatus: creating for {uri=}")
            ws = WavStatus(
                uri,
                self.audio_base_dir,
                self.audio_path_map_prefix,
                self.audio_path_prefix,
                self.s3_client,
                self.download_dir,
            )
            self.wav_cache[uri] = ws
        else:
            debug(f"WavStatus: already available for {uri=}")

        # close and remove files in the cache that are not fresh enough in terms
        # of not being recently used
        for c_uri, c_ws in list(self.wav_cache.items()):
            if uri != c_uri and c_ws.age > 2 and c_ws.sound_file is not None:
                debug(f"Closing sound file for cached uri={c_uri} age={c_ws.age}")
                c_ws.sound_file.close()
                c_ws.sound_file = None
                c_ws.remove_downloaded_file()

        if get_logger().isEnabledFor(logging.DEBUG):
            c_wss = self.wav_cache.values()
            open_files = len([c_ws for c_ws in c_wss if c_ws.sound_file])
            ages = [c_ws.age for c_ws in c_wss]
            debug(f"{open_files=}  ages={brief_list(ages)}")

        return ws


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


def _get_audio_info(wav_filename: str) -> Optional[AudioInfo]:
    try:
        sfi = sf.info(wav_filename)
        return AudioInfo(sfi.samplerate, sfi.channels, sfi.subtype)
    except sf.LibsndfileError as e:
        error(f"{e}")
        return None


def _check_audio_info(ai1: AudioInfo, ai2: AudioInfo) -> bool:
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
