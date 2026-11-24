import pytest

from pbp.util.file_uri_helper import file_uri_to_path


@pytest.mark.parametrize(
    "uri,expected",
    [
        # Standard 3-slash format with drive letter (RFC 8089)
        ("file:///C:/audio/nrs", "C:/audio/nrs"),
        ("file:///D:/data/test.json", "D:/data/test.json"),
        # Non-standard 2-slash format with drive letter
        ("file://C:/audio/nrs", "C:/audio/nrs"),
        # Backslashes
        ("file://C:\\audio\\nrs", "C:\\audio\\nrs"),
        # Drive-relative path
        ("file://C:file.wav", "C:file.wav"),
        # Percent-encoded characters
        ("file:///C:/my%20folder/nrs", "C:/my folder/nrs"),
        ("file://C:/my%20folder/nrs", "C:/my folder/nrs"),
        # Without drive letter (relative to current drive root)
        ("file:///audio/nrs", "/audio/nrs"),
        # Plain paths
        ("C:/audio/nrs", "C:/audio/nrs"),
        ("C:\\audio\\nrs", "C:\\audio\\nrs"),
        ("audio/nrs", "audio/nrs"),
    ],
)
def test_file_uri_to_path_windows(uri: str, expected: str):
    assert file_uri_to_path(uri, windows=True) == expected


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("file:///abs/audio/nrs", "/abs/audio/nrs"),
        ("file://rel/audio/nrs", "rel/audio/nrs"),
        ("/abs/audio/nrs", "/abs/audio/nrs"),
        ("rel/audio/nrs", "rel/audio/nrs"),
    ],
)
def test_file_uri_to_path_posix(uri: str, expected: str):
    assert file_uri_to_path(uri, windows=False) == expected
