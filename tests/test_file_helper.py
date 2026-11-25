import functools

import pytest

import pbp.hmb_gen.file_helper as file_helper_module
from pbp.hmb_gen.file_helper import FileHelper
from pbp.util.file_uri_helper import file_uri_to_path
from pbp.util.logging_helper import create_logger


@pytest.fixture
def file_helper(tmp_path):
    return FileHelper(create_logger(), json_base_dir=str(tmp_path))


@pytest.mark.parametrize(
    "uri,expected",
    [
        ("attrs.yaml", "attrs.yaml"),
        ("dir/attrs.yaml", "dir/attrs.yaml"),
        ("/abs/dir/attrs.yaml", "/abs/dir/attrs.yaml"),
        ("file:///abs/dir/attrs.yaml", "/abs/dir/attrs.yaml"),
    ],
)
def test_get_local_filename_local(file_helper, uri, expected):
    assert file_helper.get_local_filename(uri) == expected


@pytest.mark.parametrize(
    "uri,expected",
    [
        (r"C:\Users\x\attrs.yaml", r"C:\Users\x\attrs.yaml"),
        ("C:/Users/x/attrs.yaml", "C:/Users/x/attrs.yaml"),
        ("file:///C:/Users/x/attrs.yaml", "C:/Users/x/attrs.yaml"),
        (r"attrs.yaml", r"attrs.yaml"),
    ],
)
def test_get_local_filename_windows_keeps_drive(file_helper, monkeypatch, uri, expected):
    monkeypatch.setattr(
        file_helper_module,
        "file_uri_to_path",
        functools.partial(file_uri_to_path, windows=True),
    )
    assert file_helper.get_local_filename(uri) == expected
