import os
import pathlib
from typing import Optional
from urllib.parse import ParseResult, urlparse

import loguru
from botocore.client import BaseClient, ClientError
from google.cloud.exceptions import NotFound as GsNotFound
from google.cloud.storage import Client as GsClient

from pbp.hmb_gen.misc_helper import map_prefix
from pbp.util.bucket_key_simple import get_bucket_key_simple


class UriHandler:
    """
    Handles URI resolution and file operations for both local and cloud-based URIs.

    Provides support for:
    - Cloud storage downloads (S3/GS)
    - Downloaded file cleanup
    - Local file path resolution
    - URI prefix mapping
    """

    def __init__(
        self,
        log: "loguru.Logger",
        base_dir: Optional[str] = None,
        path_map_prefix: str = "",
        path_prefix: str = "",
        download_dir: Optional[str] = None,
        assume_downloaded_files: bool = False,
        print_downloading_lines: bool = False,
        s3_client: Optional[BaseClient] = None,
        gs_client: Optional[GsClient] = None,
    ):
        """
        Initialize the URI handler with configuration for various URI types.

        Args:
            log: Logger instance.
            base_dir: Base directory for relative `path` attributes.
            path_map_prefix: Prefix mapping for resolving actual URIs using tilde (~) as separator.
                Example: `"s3://bucket~file:///local/path"` maps s3://bucket/* to file:///local/path/*.
            path_prefix: Ad hoc path prefix for file locations, e.g., `"/Volumes"`.
            download_dir: Directory to save downloaded files. Defaults to current directory.
            assume_downloaded_files: If True, skips re-downloading files that already exist.
            print_downloading_lines: If True, prints `"downloading <uri>"` messages to console.
            s3_client: S3 client for handling `s3://` URIs.
            gs_client: Google Cloud Storage client for handling `gs://` URIs.
        """
        self.log = log
        self.base_dir = base_dir
        self.path_map_prefix = path_map_prefix
        self.path_prefix = path_prefix
        self.download_dir: str = download_dir if download_dir else "."
        self.assume_downloaded_files = assume_downloaded_files
        self.print_downloading_lines = print_downloading_lines
        self.s3_client = s3_client
        self.gs_client = gs_client

    def resolve_uri(self, uri: str) -> tuple[str, ParseResult]:
        """
        Return the resolved URI and its parsed components.

        Args:
            uri: The original URI to resolve.

        Returns:
            Tuple of (resolved_uri, parsed_uri).
        """
        # Apply any path prefix mapping if configured:
        resolved_uri = map_prefix(self.path_map_prefix, uri)
        parsed_uri = urlparse(resolved_uri)
        return resolved_uri, parsed_uri

    def get_local_filename(self, uri: str) -> Optional[str]:
        """
        Get the local filename for a URI, downloading from cloud storage if needed.

        For cloud URIs (s3://, gs://), this will download the file and return the
        local path. For local URIs, this resolves the path according to the
        configured path settings.

        Args:
            uri: The URI to resolve to a local filename.

        Returns:
            Local filename or None if error.
        """
        resolved_uri, parsed_uri = self.resolve_uri(uri)

        if parsed_uri.scheme in ("s3", "gs"):
            return self._download_cloud_file(parsed_uri)

        return self._resolve_local_path(parsed_uri)

    def remove_downloaded_file(self, filename: str, original_uri: str) -> None:
        """
        Remove a downloaded file if it was downloaded from cloud storage.

        Args:
            filename: The local filename to potentially remove.
            original_uri: The original URI to check if it's a cloud URI.
        """
        if not pathlib.Path(filename).exists():
            return

        _, parsed_uri = self.resolve_uri(original_uri)

        if (
            self.s3_client is None and self.gs_client is None
        ) or parsed_uri.scheme not in ("s3", "gs"):
            self.log.debug(f"No file download involved for {original_uri=}")
            return

        try:
            os.remove(filename)
            self.log.debug(f"Removed cached file {filename} for {original_uri=}")
        except OSError as e:
            self.log.error(f"Error removing file {filename}: {e}")

    def _download_cloud_file(self, parsed_uri: ParseResult) -> Optional[str]:
        """
        Download a file from cloud storage (S3 or GS).

        Args:
            parsed_uri: Parsed URI for the cloud file.

        Returns:
            Local filename of downloaded file or None if error.
        """
        pathlib.Path(self.download_dir).mkdir(parents=True, exist_ok=True)

        bucket, key, simple = get_bucket_key_simple(parsed_uri)
        local_filename = f"{self.download_dir}/{simple}"

        if os.path.isfile(local_filename) and self.assume_downloaded_files:
            self.log.info(
                f"ASSUMING ALREADY DOWNLOADED: {bucket=} {key=} to {local_filename}"
            )
            if self.print_downloading_lines:
                print(f"Assuming already downloaded {parsed_uri.geturl()}")
            return local_filename

        scheme = parsed_uri.scheme
        self.log.info(f"Downloading {scheme=} {bucket=} {key=} to {local_filename}")
        if self.print_downloading_lines:
            print(f"downloading {parsed_uri.geturl()}")

        if scheme == "s3":
            assert self.s3_client is not None
            try:
                self.s3_client.download_file(bucket, key, local_filename)
                return local_filename
            except ClientError as e:
                self.log.error(f"Error downloading {scheme=} {bucket}/{key}: {e}")
                return None

        if scheme == "gs":
            assert self.gs_client is not None
            gs_bucket = self.gs_client.bucket(bucket)
            blob = gs_bucket.blob(key)
            try:
                blob.download_to_filename(local_filename)
                return local_filename
            except GsNotFound as e:
                self.log.error(f"Error downloading {scheme=} {bucket}/{key}: {e}")
                return None

        return None

    def _resolve_local_path(self, parsed_uri: ParseResult) -> str:
        """
        Resolve a local file path according to the configured path settings.

        Args:
            parsed_uri: Parsed URI for the local file.

        Returns:
            Resolved local filename.
        """
        path = parsed_uri.path

        if os.name == "nt":
            return parsed_uri.netloc + parsed_uri.path

        # For file:// URIs, check if we have a netloc (like "file://relative/path")
        # vs absolute paths (like "file:///absolute/path")
        if parsed_uri.netloc:
            # URI like "file://relative/path" - netloc is "relative", path is "/path"
            if self.base_dir is not None:
                local_filename = f"{self.base_dir}/{parsed_uri.netloc}{path}"
            else:
                local_filename = f"{parsed_uri.netloc}{path}"
        elif path.startswith("/"):
            # URI like "file:///absolute/path" - absolute path
            local_filename = f"{self.path_prefix}{path}"
        elif self.base_dir is not None:
            # Relative path with base directory
            local_filename = f"{self.base_dir}/{path}"
        else:
            # Just the path as-is
            local_filename = path

        return local_filename

    def is_cloud_uri(self, uri: str) -> bool:
        """
        Check if a URI is a cloud storage URI (s3:// or gs://).

        Args:
            uri: The URI to check.

        Returns:
            True if the URI is a cloud storage URI.
        """
        _, parsed_uri = self.resolve_uri(uri)
        return parsed_uri.scheme in ("s3", "gs")
