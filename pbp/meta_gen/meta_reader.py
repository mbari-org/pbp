# pbp, Apache License 2.0
# Filename: meta_gen/meta_reader.py
# Description: Utilities for efficiently reading audio metadata either locally or from a remote source.
# Wraps the metadata into classes for easy access and transformation into a pandas dataframe.
# Supports SoundTrap, NRS and icListen audio files

from pathlib import Path
from typing import Optional

from six.moves.urllib.request import urlopen
import io
import re
import soundfile as sf
import pandas as pd
from datetime import datetime, timedelta
from pbp.meta_gen.utils import parse_s3_or_gcp_url


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
        self.duration_secs = 0.0
        self.fs = -1
        self.frames = -1
        self.channels = -1
        self.subtype = ""
        self.exception = ""

    def has_exception(self):
        return True if len(self.exception) > 0 else False

    def to_df(self):
        # if the self.path_or_url is a url, then add to the data frame with the appropriate prefixes
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
                    "uri": "file://" + self.path_or_url,
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


class GenericWavFile(AudioFile):
    """GenericWavFile uses the metadata from the wav file itself,
    but only grabs the needed metadata from the header in S3"""

    def __init__(self, log, path_or_url: str, start: datetime):
        super().__init__(path_or_url, start)
        self.log = log
        self.path_or_url = path_or_url
        self.start = start
        self.duration_secs = 0
        self.fs = -1
        self.frames = -1
        self.channels = -1
        self.subtype = ""
        self.exception = ""
        self.path_or_url = path_or_url
        # bytes_per_sec = (
        #     3 * 256e3
        # )  # 3 bytes per sample at 24-bit resolution and 256 kHz sampling rate

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
                idx_data = fields.index("data")
                idx_bytes = fields.index("Bytes/sec")
                bytes_per_sec = float(fields[idx_bytes + 2])
                self.duration_secs = float(fields[idx_data + 2]) / bytes_per_sec
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
                    self.log.warning(self.exception)
            else:
                info = sf.info(path_or_url)
                self.duration_secs = info.duration

            self.end = self.start + timedelta(microseconds=int(self.duration_secs * 1e6))
            self.fs = info.samplerate
            self.frames = info.frames
            self.channels = info.channels
            self.subtype = info.subtype if info.subtype else ""
        except Exception as ex:
            self.log.exception(f"Corrupt file {path_or_url}. {ex}")


class FlacFile(AudioFile):
    """FlacFile uses the metadata from the flac file itself,
    but only grabs the needed metadata from the header in gs or local file system."""

    def __init__(self, log, path_or_url: str, start: datetime):
        super().__init__(path_or_url, start)
        self.log = log
        self.path_or_url = path_or_url
        self.start = start
        self.end: Optional[datetime] = None
        self.duration_secs = 0
        self.fs = -1
        self.frames = -1
        self.channels = -1
        self.subtype = ""
        self.exception = ""
        self.path_or_url = path_or_url

        try:
            # if the in_file is a gs url, then read the metadata
            bucket, prefix, scheme = parse_s3_or_gcp_url(path_or_url)
            if scheme == "gs":
                url = f"http://storage.googleapis.com/{bucket}/{prefix}"

                info = sf.info(io.BytesIO(urlopen(url).read(20_000)), verbose=True)

                # get the duration from the extra_info data field which stores the duration in total bytes
                fields = info.extra_info.split(":")
                sample_rate = int(fields[3].split("\n")[0])
                channels = int(fields[2].split("\n")[0])
                length_microseconds = int(info.frames * 1e6 / info.samplerate)
                # get the file name from the url
                file_name = url.split("/")[-1]

                # files are in the format NRS11_20191231_230836.flac'
                # extract the timestamp from the file name
                f = Path(file_name).stem.split("_")
                # If the last two digits of the timestamp are 60, subtract 1 second
                # This is a bug in the FlacFile name
                if f[2][-2:] == "60":
                    f_c = f[1] + f[2]
                    # Make the last two digits 59
                    f_c = f_c[:-2] + "59"
                else:
                    f_c = f[1] + f[2]
                # convert the timestamp to a datetime object
                timestamp = datetime.strptime(f_c, "%Y%m%d%H%M%S")
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
            self.log.exception(f"Corrupt file {path_or_url}. {ex}")
