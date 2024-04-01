# pypam-based-processing, Apache License 2.0
# Filename: json_generator/wavfile.py
# Description:  wav file metadata reader. Supports SoundTrap and icListen wav files

from logging import exception, warning, debug
from pathlib import Path
from typing import Optional

import numpy as np
from six.moves.urllib.request import urlopen
import io
import re
import soundfile as sf
import pandas as pd
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET
from pbp.json_generator.utils import parse_s3_or_gcp_url


class AudioFile:
    def __init__(self, path_or_url: str, start: datetime):
        """
        Abstract class for reading wav file metadata
        :param path_or_url:
            The path or url to the wav file
        :param start:
            The start time of the wav file
        """
        self.start = start
        self.path_or_url = path_or_url
        self.end: Optional[datetime] = None
        self.duration_secs = -1
        self.fs = -1
        self.frames = -1
        self.channels = -1
        self.subtype = ""
        self.exception = np.NAN

    def has_exception(self):
        return True if len(self.exception) > 0 else False

    def to_df(self):
        # if the self.path_or_url is a url, then add to the data frame with the appropriate prefix
        if "s3://" in self.path_or_url or "gs://" in self.path_or_url:
            df = pd.DataFrame(
                {
                    "uri": self.path_or_url,
                    "start": self.start,
                    "end": self.end,
                    "fs": self.fs,
                    "duration_secs": self.duration_secs,
                    "channels": self.channels,
                    "subtype": self.subtype,
                    "exception": self.exception,
                },
                index=[self.start],
            )
        else:
            df = pd.DataFrame(
                {
                    "url": "file://" + self.path_or_url,
                    "start": self.start,
                    "end": self.end,
                    "fs": self.fs,
                    "duration_secs": self.duration_secs,
                    "channels": self.channels,
                    "subtype": self.subtype,
                    "exception": self.exception,
                },
                index=[self.start],
            )
        return df

    def get_max_freq(self):
        return self.fs / 2


class SoundTrapWavFile(AudioFile):
    def __init__(self, path_or_url: str, xml_file: str, start: datetime):
        """
        SoundTrapWavFile uses the metadata from the xml files, not the wav file itself
        :param path_or_url:
            The path or uri of the wav file
        :param xml_file:
            The uri of the xml file that contains the metadata
        :param path_or_url:

        :param start:
        """
        super().__init__(path_or_url, start)
        tree = ET.parse(xml_file)
        root = tree.getroot()
        wav_start_dt = None
        wav_stop_dt = None
        sample_count = None

        # Iterate over the XML elements grabbing the needed metadata values
        for element in root.iter("WavFileHandler"):
            # Get the value of the id attribute
            value = element.get("SamplingStartTimeUTC")
            if value:
                wav_start_dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

            value = element.get("SamplingStopTimeUTC")
            if value:
                wav_stop_dt = datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")

            value = element.get("SampleCount")
            if value:
                sample_count = int(value)

        # Error checking
        if not wav_start_dt or not wav_stop_dt or not sample_count:
            raise ValueError(f"Error reading {xml_file}. Missing metadata")

        self.path_or_url = path_or_url
        self.start = wav_start_dt
        self.end = wav_stop_dt
        self.duration_secs = sample_count / 48000
        self.fs = 48000
        self.frames = sample_count
        self.channels = 1
        self.subtype = "SoundTrap"
        self.exception = np.NAN  # no exceptions for SoundTrap  files


class IcListenWavFile(AudioFile):
    """IcListenWavFile uses the metadata from the wav file itself,
    but only grabs the needed metadata from the header in S3"""

    def __init__(self, path_or_url: str, start: datetime):
        super().__init__(path_or_url, start)
        self.path_or_url = path_or_url
        self.start = start
        self.duration_secs = -1
        self.fs = -1
        self.frames = -1
        self.channels = -1
        self.subtype = ""
        self.exception = np.NAN
        self.path_or_url = path_or_url
        bytes_per_sec = (
            3 * 256e3
        )  # 3 bytes per sample at 24-bit resolution and 256 kHz sampling rate

        try:
            # if the in_file is a s3 url, then read the metadata from the s3 url
            if re.match(r"^s3://", path_or_url):
                p = Path(path_or_url)
                bucket, key = p.parts[1], "/".join(p.parts[2:])
                url = f"http://{bucket}.s3.amazonaws.com/{key}"

                # read the first 20,000 bytes of the file to get the metadata
                info = sf.info(io.BytesIO(urlopen(url).read(20_000)), verbose=True)
                # get the duration from the extra_info data field which stores the duration in total bytes
                fields = info.extra_info.split()
                idx = fields.index("data")
                self.duration_secs = float(fields[idx + 2]) / bytes_per_sec
                # get the size in bytes of the data+RIFF header
                idx = fields.index("RIFF")
                riff_size = int(fields[idx + 2]) + 8
                # get the content length from the http header
                content_length = int(urlopen(url).info()["Content-Length"])
                # if the content length is less than the size of the data+RIFF header, then the file is truncated but
                # still may be usable
                if content_length < riff_size:
                    self.exception = f"Truncated file {path_or_url}. Content length {content_length} < RIFF size {riff_size}"
                    # calculate the duration which is the size of the content length minus the size of the RIFF
                    # header which is 44 bytes. Round the duration to the nearest second since the recording is
                    # always in 1 second increments
                    self.duration_secs = round(content_length - 44) / bytes_per_sec
                    warning(self.exception)
            else:
                info = sf.info(path_or_url)
                self.duration_secs = info.duration

            self.end = self.start + timedelta(
                microseconds=int(info.frames * 1e6 / info.samplerate)
            )
            self.fs = info.samplerate
            self.frames = info.frames
            self.channels = info.channels
            self.subtype = info.subtype if info.subtype else ""
        except Exception as ex:
            exception(f"Corrupt file {path_or_url}. {ex}")


class FlacFile(AudioFile):
    """FlacFile uses the metadata from the flac file itself,
    but only grabs the needed metadata from the header in gs or local file system."""

    def __init__(self, path_or_url: str, start: datetime):
        super().__init__(path_or_url, start)
        self.path_or_url = path_or_url
        self.start = start
        self.end: Optional[datetime] = None
        self.duration_secs = -1
        self.fs = -1
        self.frames = -1
        self.channels = -1
        self.subtype = ""
        self.exception = np.NAN
        self.path_or_url = path_or_url

        try:
            # if the in_file is a gs url, then read the metadata
            bucket, prefix, scheme = parse_s3_or_gcp_url(path_or_url)
            if scheme == "gs":
                url = f"http://storage.googleapis.com/{bucket}/{prefix}"

                info = sf.info(io.BytesIO(urlopen(url).read(20_000)), verbose=True)

                # get the duration from the extra_info data field which stores the duration in total bytes
                fields = info.extra_info.split(":")
                debug("\n".join(fields))
                sample_rate = int(fields[3].split("\n")[0])
                channels = int(fields[2].split("\n")[0])
                length_microseconds = int(info.frames * 1e6 / info.samplerate)
                # get the file name from the url
                file_name = url.split("/")[-1]

                # files are in the format NRS11_20191231_230836.flac'
                # extract the timestamp from the file name
                f = Path(file_name).stem.split("_")
                # If the last two digits of the timestamp are 60, subtract 1 seconds
                if f[2][-2:] == "60":
                    f = f[1] + f[2]
                    # Make the last two digits 59
                    f = f[:-2] + "59"
                else:
                    f = f[1] + f[2]
                # convert the timestamp to a datetime object
                timestamp = datetime.strptime(f, "%Y%m%d%H%M%S")
                self.start = timestamp
                self.end = self.start + timedelta(microseconds=length_microseconds)
                self.duration_secs = int(length_microseconds / 1e6)
                self.channels = channels
                self.subtype = "flac"
                self.fs = sample_rate
                self.frames = info.frames if info.frames else 0
            if scheme == "file" or scheme == "":
                info = sf.info(path_or_url)
                length_microseconds = int(info.frames * 1e6 / info.samplerate)
                self.duration_secs = int(length_microseconds / 1e6)
                self.end = self.start + timedelta(microseconds=length_microseconds)
                self.fs = info.samplerate
                self.frames = info.frames
                self.channels = info.channels
                self.subtype = info.subtype if info.subtype else ""
        except Exception as ex:
            exception(f"Corrupt file {path_or_url}. {ex}")
