import os
import pathlib
from dataclasses import dataclass
from math import ceil, floor
from typing import Dict, List, Optional, Tuple
from urllib.parse import ParseResult, urlparse

# import loguru
import numpy as np
import soundfile as sf

from botocore.client import BaseClient, ClientError
from google.cloud.exceptions import NotFound as GsNotFound
from google.cloud.storage import Client as GsClient

from pbp.json_support import get_intersecting_entries, JEntry, parse_json_contents
from pbp.misc_helper import brief_list, map_prefix


@dataclass
class AudioInfo:
    samplerate: int
    channels: int
    subtype: str


class SoundStatus:
    # TODO cleanup!  there's some repetition here wrt FileHelper!

    def __init__(
        self,
        log,  # : loguru.Logger,
        uri: str,
        audio_base_dir: Optional[str],
        audio_path_map_prefix: str,
        audio_path_prefix: str,
        download_dir: Optional[str],
        assume_downloaded_files: bool,
        s3_client: Optional[BaseClient] = None,
        gs_client: Optional[GsClient] = None,
    ):
        self.log = log
        self.uri = map_prefix(audio_path_map_prefix, uri)
        self.parsed_uri = urlparse(self.uri)

        self.audio_base_dir = audio_base_dir
        self.audio_path_prefix = audio_path_prefix
        self.s3_client = s3_client
        self.gs_client = gs_client
        self.download_dir: str = download_dir if download_dir else "."
        self.assume_downloaded_files = assume_downloaded_files

        self.error = None

        self.sound_filename = self._get_sound_filename()
        if self.sound_filename is None:
            self.error = "error getting sound filename"
            return

        ai = self._get_audio_info(self.sound_filename)
        if ai is None:
            self.error = "error getting audio info"
            return

        self.audio_info: AudioInfo = ai
        self.sound_file = sf.SoundFile(self.sound_filename)
        self.age = 0  # see _get_sound_status.

    def _get_audio_info(self, sound_filename: str) -> Optional[AudioInfo]:
        try:
            sfi = sf.info(sound_filename)
            return AudioInfo(sfi.samplerate, sfi.channels, sfi.subtype)
        except sf.LibsndfileError as e:
            self.log.error(f"{e}")
            return None

    def _get_sound_filename(self) -> Optional[str]:
        self.log.debug(f"_get_sound_filename: {self.uri=}")
        if self.parsed_uri.scheme in ("s3", "gs"):
            return _download(
                self.log,
                self.parsed_uri,
                self.download_dir,
                self.assume_downloaded_files,
                self.s3_client,
                self.gs_client,
            )

        # otherwise assuming local file, so we only inspect the `path` attribute:
        path = self.parsed_uri.path
        if path.startswith("/"):
            sound_filename = f"{self.audio_path_prefix}{path}"
        elif self.audio_base_dir is not None:
            sound_filename = f"{self.audio_base_dir}/{path}"
        else:
            sound_filename = path
        return sound_filename

    def remove_downloaded_file(self):
        if not pathlib.Path(self.sound_filename).exists():
            return

        if (
            self.s3_client is None and self.gs_client is None
        ) or self.parsed_uri.scheme not in ("s3", "gs"):
            self.log.debug(f"No file download involved for {self.uri=}")
            return

        try:
            os.remove(self.sound_filename)
            self.log.debug(f"Removed cached file {self.sound_filename} for {self.uri=}")
        except OSError as e:
            self.log.error(f"Error removing file {self.sound_filename}: {e}")


def _download(
    log,  # : loguru.Logger,
    parsed_uri: ParseResult,
    download_dir: str,
    assume_downloaded_files: bool = False,
    s3_client: Optional[BaseClient] = None,
    gs_client: Optional[GsClient] = None,
) -> Optional[str]:
    """
    Downloads the given URI to the given download directory.

    NOTE: `assume_downloaded_files` can be set to True to skip downloading files
    that already exist in the download directory.

    One of `s3_client` or `gs_client` must be given.

    :return: Downloaded filename or None if error
    """

    pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)

    bucket, key, simple = get_bucket_key_simple(parsed_uri)
    local_filename = f"{download_dir}/{simple}"

    if os.path.isfile(local_filename) and assume_downloaded_files:
        log.info(f"ASSUMING ALREADY DOWNLOADED: {bucket=} {key=} to {local_filename}")
        return local_filename

    scheme = parsed_uri.scheme
    log.info(f"Downloading {scheme=} {bucket=} {key=} to {local_filename}")

    if scheme == "s3":
        assert s3_client is not None
        try:
            s3_client.download_file(bucket, key, local_filename)
            return local_filename
        except ClientError as e:
            log.error(f"Error downloading {scheme=} {bucket}/{key}: {e}")
            return None

    if scheme == "gs":
        assert gs_client is not None
        gs_bucket = gs_client.bucket(bucket)
        blob = gs_bucket.blob(key)
        try:
            blob.download_to_filename(local_filename)
            return local_filename
        except GsNotFound as e:
            log.error(f"Error downloading {scheme=} {bucket}/{key}: {e}")
            return None

    return None


class FileHelper:
    """
    Helps loading audio segments.
    """

    def __init__(
        self,
        log,  # : loguru.Logger,
        json_base_dir: str,
        audio_base_dir: Optional[str] = None,
        audio_path_map_prefix: str = "",
        audio_path_prefix: str = "",
        segment_size_in_mins: int = 1,
        s3_client: Optional[BaseClient] = None,
        gs_client: Optional[GsClient] = None,
        download_dir: Optional[str] = None,
        assume_downloaded_files: bool = False,
        retain_downloaded_files: bool = False,
    ):
        """

        :param log:
          Logger
        :param audio_base_dir:
          If given, it will be used as base directory for any relative (not starting with a slash)
          `path` attribute in the json entries.
        :param audio_path_map_prefix:
          Prefix mapping to get actual audio uri to be used.
          Example: `s3://pacific-sound-256khz-2022~file:///PAM_Archive/2022`
        :param audio_path_prefix:
          Ad hoc path prefix for sound file locations, e.g. "/Volumes"
        :param segment_size_in_mins:
            The size of each audio segment to extract, in minutes. By default, 1.
        :param s3_client:
            If given, it will be used to handle `s3:` based uris.
        :param gs_client:
            If given, it will be used to handle `gs:` based uris.
        :param download_dir:
            Save downloaded S3 files here if given, otherwise, save in current directory.
        :param assume_downloaded_files:
            If True, skip downloading files that already exist in the download directory.
        :param retain_downloaded_files:
            If True, remove downloaded files after use.
        """
        self.log = log

        self.log.info(
            "Creating FileHelper:"
            + f"\n    json_base_dir:           {json_base_dir}"
            + (
                f"\n    audio_base_dir:          {audio_base_dir}"
                if audio_base_dir
                else ""
            )
            + (
                f"\n    audio_path_map_prefix:   '{audio_path_map_prefix}'"
                if audio_path_map_prefix
                else ""
            )
            + (
                f"\n    audio_path_prefix:       '{audio_path_prefix}'"
                if audio_path_prefix
                else ""
            )
            + f"\n    segment_size_in_mins:    {segment_size_in_mins}"
            + f"\n    s3_client:               {'(given)' if s3_client else 'None'}"
            + f"\n    gs_client:               {'(given)' if gs_client else 'None'}"
            + f"\n    download_dir:            {download_dir}"
            + f"\n    assume_downloaded_files: {assume_downloaded_files}"
            + f"\n    retain_downloaded_files: {retain_downloaded_files}"
            + "\n"
        )
        self.json_base_dir = json_base_dir
        self.audio_base_dir = audio_base_dir
        self.audio_path_map_prefix = audio_path_map_prefix
        self.audio_path_prefix = audio_path_prefix
        self.segment_size_in_mins = segment_size_in_mins
        self.s3_client = s3_client
        self.gs_client = gs_client
        self.download_dir: str = download_dir if download_dir else "."
        self.assume_downloaded_files = assume_downloaded_files
        self.retain_downloaded_files = retain_downloaded_files

        self.sound_cache: Dict[str, SoundStatus] = {}

        # the following set by select_day:
        self.year: Optional[int] = None
        self.month: Optional[int] = None
        self.day: Optional[int] = None
        self.json_entries: Optional[List[JEntry]] = None

    def select_day(self, year: int, month: int, day: int) -> bool:
        """
        Selects the given day for subsequent processing of relevant audio segments.

        :param year:
        :param month:
        :param day:
        :return:  True only if selection was successful
        """

        self.log.info(f"Selecting day: {year:04}{month:02}{day:02}")

        json_uri = f"{self.json_base_dir}/{year:04}/{year:04}{month:02}{day:02}.json"
        json_contents = self._get_json(json_uri)
        if json_contents is None:
            self.log.error(f"{json_uri}: file not found\n")
            return False

        self.year = year
        self.month = month
        self.day = day
        self.json_entries = list(parse_json_contents(json_contents))
        return True

    def get_local_filename(self, uri: Optional[str]) -> Optional[str]:
        """
        Returns the local filename for the given URI, which will be that of
        the downloaded file when the given uri is cloud based.
        """
        if uri is None:
            return None

        parsed_uri = urlparse(uri)
        if parsed_uri.scheme in ("s3", "gs"):
            return _download(
                self.log,
                parsed_uri,
                self.download_dir,
                self.assume_downloaded_files,
                self.s3_client,
                self.gs_client,
            )

        return parsed_uri.path

    def day_completed(self):
        """
        Since a process is launched only for day, we simply clear the cache.
        """
        # first, close all sound files still open:
        sound_files_open = [
            c_ss for c_ss in self.sound_cache.values() if c_ss.sound_file is not None
        ]
        if len(sound_files_open) > 0:
            self.log.debug(
                f"day_completed: closing {len(sound_files_open)} sound files still open"
            )
            for c_ss in sound_files_open:
                self.log.debug(f"Closing sound file for cached {c_ss.uri=} {c_ss.age=}")
                c_ss.sound_file.close()

        # remove any downloaded files (cloud case):
        if not self.retain_downloaded_files:
            for c_ss in self.sound_cache.values():
                c_ss.remove_downloaded_file()

        self.sound_cache = {}

    def _get_json(self, uri: str) -> Optional[str]:
        parsed_uri = urlparse(uri)
        if parsed_uri.scheme == "s3":
            return self._get_json_s3(parsed_uri)
        #  simply assume local file:
        return self._get_json_local(parsed_uri.path)

    def _get_json_s3(self, parsed_uri: ParseResult) -> Optional[str]:
        local_filename = _download(
            self.log,
            parsed_uri,
            self.download_dir,
            self.assume_downloaded_files,
            self.s3_client,
            self.gs_client,
        )
        if local_filename is None:
            return None
        return self._get_json_local(local_filename)

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

        intersections = get_intersecting_entries(
            self.log,
            self.json_entries,
            self.year,
            self.month,
            self.day,
            at_hour,
            at_minute,
            segment_size_in_mins=self.segment_size_in_mins,
        )

        audio_info: Optional[AudioInfo] = None

        aggregated_segment: Optional[np.ndarray] = None

        prefix = f"({at_hour:02}h:{at_minute:02}m)"
        for intersection in intersections:
            if intersection.duration_secs == 0:
                self.log.warning("No data from intersection")
                continue

            ss = self._get_sound_status(intersection.entry.uri)
            if ss.error is not None:
                return None

            self.log.debug(
                f"    {prefix} {intersection.duration_secs} secs from {ss.sound_filename}"
            )

            if audio_info is not None and not self._check_audio_info(
                audio_info, ss.audio_info
            ):
                return None  # error!

            audio_info = ss.audio_info

            start_sample = floor(intersection.start_secs * audio_info.samplerate)
            num_samples = ceil(intersection.duration_secs * audio_info.samplerate)

            try:
                new_pos = ss.sound_file.seek(start_sample)
                if new_pos != start_sample:
                    # no-data case, let's just read 0 samples to get an empty array:
                    audio_segment = ss.sound_file.read(0)
                else:
                    audio_segment = ss.sound_file.read(num_samples)
                    if len(audio_segment) < num_samples:
                        # partial-data case.
                        self.log.warning(
                            f"!!! partial data: {len(audio_segment)} < {num_samples}"
                        )

            except sf.LibsndfileError as e:
                self.log.error(f"{e}")
                return None

            if aggregated_segment is None:
                aggregated_segment = audio_segment
            else:
                aggregated_segment = np.concatenate((aggregated_segment, audio_segment))

        if aggregated_segment is not None:
            assert audio_info is not None
            return audio_info, aggregated_segment
        return None

    def _check_audio_info(self, ai1: AudioInfo, ai2: AudioInfo) -> bool:
        if ai1.samplerate != ai2.samplerate:
            self.log.error(
                f"UNEXPECTED: sample rate mismatch: {ai1.samplerate} vs {ai2.samplerate}"
            )
            return False
        if ai1.channels != ai2.channels:
            self.log.error(
                f"UNEXPECTED: channel count mismatch: {ai1.channels} vs {ai2.channels}"
            )
            return False
        if ai1.subtype != ai2.subtype:
            self.log.error(
                f"UNEXPECTED: subtype mismatch: {ai1.subtype} vs {ai2.subtype}"
            )
            return False
        return True

    def _get_sound_status(self, uri: str) -> SoundStatus:
        """
        Returns a SoundStatus object for the given uri.
        Internally, the 'age' attribute helps to keep the relevant files open
        as long as recently used. Note that traversal of the files indicated in the
        JSON array happens in a monotonically increasing order in time, so we
        can increment the 'age' for all entries in the cache except for the uri
        just requested.

        :param uri:
        :return:
        """
        self.log.debug(f"_get_sound_status: {uri=}")
        ss = self.sound_cache.get(uri)
        if ss is None:
            # currently cached ones get a bit older:
            for c_ss in self.sound_cache.values():
                c_ss.age += 1

            self.log.debug(f"SoundStatus: creating for {uri=}")
            ss = SoundStatus(
                log=self.log,
                uri=uri,
                audio_base_dir=self.audio_base_dir,
                audio_path_map_prefix=self.audio_path_map_prefix,
                audio_path_prefix=self.audio_path_prefix,
                download_dir=self.download_dir,
                assume_downloaded_files=self.assume_downloaded_files,
                s3_client=self.s3_client,
                gs_client=self.gs_client,
            )
            self.sound_cache[uri] = ss
        else:
            self.log.debug(f"SoundStatus: already available for {uri=}")

        # close and remove files in the cache that are not fresh enough in terms
        # of not being recently used
        for c_uri, c_ss in list(self.sound_cache.items()):
            if uri != c_uri and c_ss.age > 2 and c_ss.sound_file is not None:
                self.log.debug(
                    f"Closing sound file for cached uri={c_uri} age={c_ss.age}"
                )
                c_ss.sound_file.close()
                c_ss.sound_file = None
                if not self.retain_downloaded_files:
                    c_ss.remove_downloaded_file()

        def log_msg():
            c_sss = self.sound_cache.values()
            open_files = len([c_ss for c_ss in c_sss if c_ss.sound_file])
            ages = [c_ss.age for c_ss in c_sss]
            return f"{open_files=}  ages={brief_list(ages)}"

        self.log.opt(lazy=True).debug("_get_sound_status: {}", log_msg)

        return ss

    def _get_json_local(self, filename: str) -> Optional[str]:
        try:
            with open(filename, "r", encoding="UTF-8") as f:
                return f.read()
        except IOError as e:
            self.log.error(f"Error reading {filename}: {e}")
            return None


def get_bucket_key_simple(parsed_uri: ParseResult) -> Tuple[str, str, str]:
    bucket = parsed_uri.netloc
    key = parsed_uri.path.lstrip("/")
    simple = key.split("/")[-1] if "/" in key else key
    assert "/" not in simple, f"Unexpected simple_filename: '{simple}'"
    return bucket, key, simple
