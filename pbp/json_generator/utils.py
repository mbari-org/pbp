from typing import Tuple
from urllib.parse import urlparse


def parse_s3_or_gcp_url(url) -> Tuple[str, str, str]:
    """
    Parse the S3, GS of local file url
    :param url:
    :return:
    """
    parsed_url = urlparse(url)
    bucket = parsed_url.netloc
    prefix = parsed_url.path.lstrip("/")
    return bucket, prefix, parsed_url.scheme
