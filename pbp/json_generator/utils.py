# pbp, Apache License 2.0
# Filename: json_generator/utils.py
# Description:  Utility functions for parsing S3, GS or local file urls and defining sound instrument types for metadata generation
from typing import Tuple
from urllib.parse import urlparse


class InstrumentType:
    NRS = "NRS"
    ICLISTEN = "ICLISTEN"
    SOUNDTRAP = "SOUNDTRAP"


def parse_s3_or_gcp_url(url) -> Tuple[str, str, str]:
    """
    Parse the S3, GS of local file url
    :param url:
    :return:
    """
    parsed_url = urlparse(url)
    bucket = parsed_url.netloc
    prefix = parsed_url.path.lstrip("/")
    if parsed_url.scheme == "file":
        bucket = ""
        prefix = parsed_url.path
    return bucket, prefix, parsed_url.scheme
