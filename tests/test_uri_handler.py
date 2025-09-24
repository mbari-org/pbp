"""
Tests for UriHandler class.

These tests verify URI resolution, local path handling, cloud storage operations,
and file cleanup functionality.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch


from pbp.util.uri_handler import UriHandler


class TestUriHandler:
    """Test UriHandler functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.mock_logger = Mock()
        self.mock_s3_client = Mock()
        self.mock_gs_client = Mock()

    def test_init_default_values(self):
        """Test UriHandler initialization with default values."""
        handler = UriHandler(self.mock_logger)

        assert handler.log == self.mock_logger
        assert handler.audio_base_dir is None
        assert handler.audio_path_map_prefix == ""
        assert handler.audio_path_prefix == ""
        assert handler.download_dir == "."
        assert handler.assume_downloaded_files is False
        assert handler.print_downloading_lines is False
        assert handler.s3_client is None
        assert handler.gs_client is None

    def test_init_custom_values(self):
        """Test UriHandler initialization with custom values."""
        handler = UriHandler(
            log=self.mock_logger,
            audio_base_dir="/audio",
            audio_path_map_prefix="s3://bucket~file:///local",
            audio_path_prefix="/prefix",
            download_dir="/downloads",
            assume_downloaded_files=True,
            print_downloading_lines=True,
            s3_client=self.mock_s3_client,
            gs_client=self.mock_gs_client,
        )

        assert handler.audio_base_dir == "/audio"
        assert handler.audio_path_map_prefix == "s3://bucket~file:///local"
        assert handler.audio_path_prefix == "/prefix"
        assert handler.download_dir == "/downloads"
        assert handler.assume_downloaded_files is True
        assert handler.print_downloading_lines is True
        assert handler.s3_client == self.mock_s3_client
        assert handler.gs_client == self.mock_gs_client

    def test_resolve_uri_no_mapping(self):
        """Test URI resolution without prefix mapping."""
        handler = UriHandler(self.mock_logger)

        uri = "s3://bucket/file.wav"
        resolved_uri, parsed_uri = handler.resolve_uri(uri)

        assert resolved_uri == uri
        assert parsed_uri.scheme == "s3"
        assert parsed_uri.netloc == "bucket"
        assert parsed_uri.path == "/file.wav"

    @patch("pbp.util.uri_handler.map_prefix")
    def test_resolve_uri_with_mapping(self, mock_map_prefix):
        """Test URI resolution with prefix mapping."""
        mock_map_prefix.return_value = "file:///local/file.wav"

        handler = UriHandler(
            self.mock_logger, audio_path_map_prefix="s3://bucket~file:///local"
        )

        uri = "s3://bucket/file.wav"
        resolved_uri, parsed_uri = handler.resolve_uri(uri)

        mock_map_prefix.assert_called_once_with("s3://bucket~file:///local", uri)
        assert resolved_uri == "file:///local/file.wav"
        assert parsed_uri.scheme == "file"

    def test_is_cloud_uri_s3(self):
        """Test cloud URI detection for S3."""
        handler = UriHandler(self.mock_logger)

        assert handler.is_cloud_uri("s3://bucket/file.wav") is True

    def test_is_cloud_uri_gs(self):
        """Test cloud URI detection for GS."""
        handler = UriHandler(self.mock_logger)

        assert handler.is_cloud_uri("gs://bucket/file.wav") is True

    def test_is_cloud_uri_local(self):
        """Test cloud URI detection for local files."""
        handler = UriHandler(self.mock_logger)

        assert handler.is_cloud_uri("file:///local/file.wav") is False
        assert handler.is_cloud_uri("/local/file.wav") is False

    def test_get_local_filename_s3(self):
        """Test getting local filename for S3 URI."""
        with patch("tempfile.mkdtemp", return_value="/tmp/test_dir"):
            handler = UriHandler(
                self.mock_logger, s3_client=self.mock_s3_client, download_dir="/downloads"
            )

            with patch.object(
                handler,
                "_download_cloud_file_internal",
                return_value="/tmp/downloaded_file.wav",
            ) as mock_download:
                result = handler.get_local_filename("s3://bucket/file.wav")
                assert result == "/tmp/downloaded_file.wav"
                mock_download.assert_called_once()

    def test_get_local_filename_gs(self):
        """Test getting local filename for GS URI."""
        handler = UriHandler(self.mock_logger, gs_client=self.mock_gs_client)

        with patch.object(
            handler,
            "_download_cloud_file_internal",
            return_value="/tmp/downloaded_file.wav",
        ) as mock_download:
            result = handler.get_local_filename("gs://bucket/file.wav")
            assert result == "/tmp/downloaded_file.wav"
            mock_download.assert_called_once()

    def test_get_local_filename_local_absolute_path(self):
        """Test getting local filename for absolute local path."""
        handler = UriHandler(self.mock_logger, audio_path_prefix="/prefix")

        result = handler.get_local_filename("file:///audio/file.wav")

        assert result == "/prefix/audio/file.wav"

    def test_get_local_filename_local_with_base_dir(self):
        """Test getting local filename with base directory."""
        handler = UriHandler(self.mock_logger, audio_base_dir="/base")

        result = handler.get_local_filename("file://relative/file.wav")

        assert result == "/base/relative/file.wav"

    def test_get_local_filename_local_relative_no_base(self):
        """Test getting local filename for relative path without base directory."""
        handler = UriHandler(self.mock_logger)

        result = handler.get_local_filename("file://relative/file.wav")

        assert result == "relative/file.wav"

    @patch("os.name", "nt")
    def test_get_local_filename_windows(self):
        """Test getting local filename on Windows."""
        handler = UriHandler(self.mock_logger)

        result = handler.get_local_filename("file://C:/audio/file.wav")

        assert result == "C:/audio/file.wav"

    def test_get_local_filename_for_json_s3(self):
        """Test getting local filename for JSON file from S3."""
        handler = UriHandler(self.mock_logger, s3_client=self.mock_s3_client)

        with patch.object(
            handler, "_download_cloud_file_internal", return_value="/tmp/data.json"
        ) as mock_download:
            result = handler.get_local_filename_for_json("s3://bucket/data.json")
            assert result == "/tmp/data.json"
            mock_download.assert_called_once()

    def test_get_local_filename_for_json_local(self):
        """Test getting local filename for JSON file (local)."""
        handler = UriHandler(self.mock_logger)

        result = handler.get_local_filename_for_json("/path/to/data.json")

        assert result == "/path/to/data.json"

    @patch("os.name", "nt")
    def test_get_local_filename_for_json_windows(self):
        """Test getting local filename for JSON file on Windows."""
        handler = UriHandler(self.mock_logger)

        uri = "C:\\path\\to\\data.json"
        result = handler.get_local_filename_for_json(uri)

        assert result == uri

    def test_remove_downloaded_file_not_exists(self):
        """Test removing downloaded file when file doesn't exist."""
        handler = UriHandler(self.mock_logger)

        # Should not raise error for non-existent file
        handler.remove_downloaded_file("/nonexistent/file.wav", "s3://bucket/file.wav")

    def test_remove_downloaded_file_local_uri(self):
        """Test removing downloaded file for local URI (should not remove)."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            handler = UriHandler(self.mock_logger)

            handler.remove_downloaded_file(tmp_path, "file:///local/file.wav")

            # File should still exist (not removed for local URIs)
            assert Path(tmp_path).exists()
            self.mock_logger.debug.assert_called()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_remove_downloaded_file_no_clients(self):
        """Test removing downloaded file when no cloud clients are configured."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            handler = UriHandler(self.mock_logger)

            handler.remove_downloaded_file(tmp_path, "s3://bucket/file.wav")

            # File should still exist (no clients configured)
            assert Path(tmp_path).exists()
            self.mock_logger.debug.assert_called()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_remove_downloaded_file_s3_success(self):
        """Test successful removal of downloaded S3 file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            handler = UriHandler(self.mock_logger, s3_client=self.mock_s3_client)

            handler.remove_downloaded_file(tmp_path, "s3://bucket/file.wav")

            # File should be removed
            assert not Path(tmp_path).exists()
            self.mock_logger.debug.assert_called()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_remove_downloaded_file_gs_success(self):
        """Test successful removal of downloaded GS file."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            handler = UriHandler(self.mock_logger, gs_client=self.mock_gs_client)

            handler.remove_downloaded_file(tmp_path, "gs://bucket/file.wav")

            # File should be removed
            assert not Path(tmp_path).exists()
            self.mock_logger.debug.assert_called()
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    @patch("os.remove", side_effect=OSError("Permission denied"))
    def test_remove_downloaded_file_error(self, mock_remove):
        """Test error handling during file removal."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = tmp.name

        try:
            handler = UriHandler(self.mock_logger, s3_client=self.mock_s3_client)

            handler.remove_downloaded_file(tmp_path, "s3://bucket/file.wav")

            self.mock_logger.error.assert_called()
            error_call = self.mock_logger.error.call_args[0][0]
            assert "Error removing file" in error_call
        finally:
            Path(tmp_path).unlink(missing_ok=True)

    def test_download_parameters_passed_correctly(self):
        """Test that download parameters are passed correctly internally."""
        handler = UriHandler(
            log=self.mock_logger,
            download_dir="/custom/downloads",
            assume_downloaded_files=True,
            print_downloading_lines=True,
            s3_client=self.mock_s3_client,
            gs_client=self.mock_gs_client,
        )

        with patch.object(
            handler, "_download_cloud_file_internal", return_value="/tmp/file.wav"
        ) as mock_download:
            handler.get_local_filename("s3://bucket/file.wav")
            mock_download.assert_called_once()

    def test_download_failure_returns_none(self):
        """Test that download failure returns None."""
        handler = UriHandler(self.mock_logger, s3_client=self.mock_s3_client)

        with patch.object(
            handler, "_download_cloud_file_internal", return_value=None
        ) as mock_download:
            result = handler.get_local_filename("s3://bucket/nonexistent.wav")
            assert result is None
            mock_download.assert_called_once()


class TestUriHandlerIntegration:
    """Integration tests for UriHandler with real file operations."""

    def test_local_file_operations(self):
        """Test UriHandler with actual local files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create a test file
            test_file = Path(temp_dir) / "test.wav"
            test_file.write_text("test content")

            handler = UriHandler(Mock(), audio_base_dir=temp_dir)

            # Test local file resolution
            uri = "file://test.wav"
            result = handler.get_local_filename(uri)

            assert result == f"{temp_dir}/test.wav"
            assert Path(result).exists()

    def test_prefix_mapping_integration(self):
        """Test UriHandler with actual prefix mapping."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_logger = Mock()

            # Create handler with prefix mapping
            handler = UriHandler(
                mock_logger,
                audio_path_map_prefix=f"test://mapped~file://{temp_dir}",
                audio_base_dir=temp_dir,
            )

            # This should trigger prefix mapping via map_prefix
            uri = "test://mapped/subdir/file.wav"
            resolved_uri, parsed_uri = handler.resolve_uri(uri)

            # The map_prefix function should have been called
            assert resolved_uri != uri  # Should be different due to mapping
