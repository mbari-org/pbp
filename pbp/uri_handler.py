import os
import pathlib
from typing import Optional
from urllib.parse import ParseResult, urlparse

import loguru
from botocore.client import BaseClient
from google.cloud.storage import Client as GsClient

from pbp.download_uri import download_uri
from pbp.misc_helper import map_prefix


class UriHandler:
    """
    Handles URI resolution and file operations for both local and cloud-based URIs.

    This class factors out the common URI handling logic used by both FileHelper
    and SoundStatus classes, providing consistent behavior for:
    - URI prefix mapping
    - Local file path resolution
    - Cloud storage downloads (S3/GS)
    - Downloaded file cleanup
    """

    def __init__(
        self,
        log: "loguru.Logger",
        audio_base_dir: Optional[str] = None,
        audio_path_map_prefix: str = "",
        audio_path_prefix: str = "",
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
            audio_base_dir: Base directory for relative `path` attributes.
            audio_path_map_prefix: Prefix mapping for resolving actual URIs.
                Example: `"s3://bucket~file:///local/path"`.
            audio_path_prefix: Ad hoc path prefix for sound file locations, e.g., `"/Volumes"`.
            download_dir: Directory to save downloaded files. Defaults to current directory.
            assume_downloaded_files: If True, skips re-downloading files that already exist.
            print_downloading_lines: If True, prints `"downloading <uri>"` messages to console.
            s3_client: S3 client for handling `s3://` URIs.
            gs_client: Google Cloud Storage client for handling `gs://` URIs.
        """
        self.log = log
        self.audio_base_dir = audio_base_dir
        self.audio_path_map_prefix = audio_path_map_prefix
        self.audio_path_prefix = audio_path_prefix
        self.download_dir: str = download_dir if download_dir else "."
        self.assume_downloaded_files = assume_downloaded_files
        self.print_downloading_lines = print_downloading_lines
        self.s3_client = s3_client
        self.gs_client = gs_client

    def resolve_uri(self, uri: str) -> tuple[str, ParseResult]:
        """
        Apply URI prefix mapping and return the resolved URI and its parsed components.

        Args:
            uri: The original URI to resolve.

        Returns:
            Tuple of (resolved_uri, parsed_uri).
        """
        resolved_uri = map_prefix(self.audio_path_map_prefix, uri)
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

    def get_local_filename_for_json(self, uri: str) -> Optional[str]:
        """
        Get local filename for JSON files, with special handling for different schemes.

        Args:
            uri: The URI of the JSON file.

        Returns:
            Local filename or None if error.
        """
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme == "s3":
            return self._download_cloud_file(parsed_uri)

        # Assume local file
        if os.name == "nt":
            return uri
        else:
            return parsed_uri.path

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
        return download_uri(
            log=self.log,
            parsed_uri=parsed_uri,
            download_dir=self.download_dir,
            assume_downloaded_files=self.assume_downloaded_files,
            print_downloading_lines=self.print_downloading_lines,
            s3_client=self.s3_client,
            gs_client=self.gs_client,
        )

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
            if self.audio_base_dir is not None:
                sound_filename = f"{self.audio_base_dir}/{parsed_uri.netloc}{path}"
            else:
                sound_filename = f"{parsed_uri.netloc}{path}"
        elif path.startswith("/"):
            # URI like "file:///absolute/path" - absolute path
            sound_filename = f"{self.audio_path_prefix}{path}"
        elif self.audio_base_dir is not None:
            # Relative path with base directory
            sound_filename = f"{self.audio_base_dir}/{path}"
        else:
            # Just the path as-is
            sound_filename = path

        return sound_filename

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
