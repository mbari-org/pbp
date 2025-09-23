import os
import pathlib
from typing import Optional
from urllib.parse import ParseResult

import loguru
from botocore.client import BaseClient, ClientError
from google.cloud.exceptions import NotFound as GsNotFound
from google.cloud.storage import Client as GsClient


def download_uri(
    log: "loguru.Logger",
    parsed_uri: ParseResult,
    download_dir: str,
    assume_downloaded_files: bool = False,
    print_downloading_lines: bool = False,
    s3_client: Optional[BaseClient] = None,
    gs_client: Optional[GsClient] = None,
) -> Optional[str]:
    """
    Downloads the given URI to the given download directory.

    NOTE: `assume_downloaded_files` can be set to True to skip re-downloading files
    that already exist in the download directory.

    One of `s3_client` or `gs_client` must be given.

    :return: Downloaded filename or None if error
    """

    pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)

    bucket, key, simple = get_bucket_key_simple(parsed_uri)
    local_filename = f"{download_dir}/{simple}"

    if os.path.isfile(local_filename) and assume_downloaded_files:
        log.info(f"ASSUMING ALREADY DOWNLOADED: {bucket=} {key=} to {local_filename}")
        if print_downloading_lines:
            print(f"Assuming already downloaded {parsed_uri.geturl()}")
        return local_filename

    scheme = parsed_uri.scheme
    log.info(f"Downloading {scheme=} {bucket=} {key=} to {local_filename}")
    if print_downloading_lines:
        print(f"downloading {parsed_uri.geturl()}")

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


def get_bucket_key_simple(parsed_uri: ParseResult) -> tuple[str, str, str]:
    bucket = parsed_uri.netloc
    key = parsed_uri.path.lstrip("/")
    simple = key.split("/")[-1] if "/" in key else key
    assert "/" not in simple, f"Unexpected simple_filename: '{simple}'"
    return bucket, key, simple
