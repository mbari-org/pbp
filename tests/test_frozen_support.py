import os
import sys
from pathlib import Path

import pbp.util.frozen_support as fs


def test_user_cache_dir():
    home = Path("/home/u")
    assert fs.user_cache_dir("darwin", {}, home) == home / "Library/Caches/mbari-pbp"
    assert fs.user_cache_dir("linux", {}, home) == home / ".cache/mbari-pbp"
    assert fs.user_cache_dir("linux", {"XDG_CACHE_HOME": "/xdg"}, home) == Path(
        "/xdg/mbari-pbp"
    )
    assert fs.user_cache_dir("win32", {"LOCALAPPDATA": "/lad"}, home) == Path(
        "/lad/mbari-pbp/Cache"
    )
    assert fs.user_cache_dir("win32", {}, home) == home / "AppData/Local/mbari-pbp/Cache"


def test_mpl_config_dir_depends_on_bundle_and_version(tmp_path: Path):
    a = fs.mpl_config_dir(tmp_path, "/apps/pbp-a/_internal", "1.10.1")
    assert a.parent == tmp_path
    assert a.name.startswith("matplotlib-1.10.1-")
    assert a == fs.mpl_config_dir(tmp_path, "/apps/pbp-a/_internal", "1.10.1")
    assert a != fs.mpl_config_dir(tmp_path, "/apps/pbp-b/_internal", "1.10.1")
    assert a != fs.mpl_config_dir(tmp_path, "/apps/pbp-a/_internal", "1.10.2")


def test_use_persistent_mpl_config_dir_not_frozen(monkeypatch):
    monkeypatch.delattr(sys, "frozen", raising=False)
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/original")
    assert fs.use_persistent_mpl_config_dir() is None
    assert os.environ["MPLCONFIGDIR"] == "/tmp/original"


def test_use_persistent_mpl_config_dir_frozen(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path / "bundle"), raising=False)
    monkeypatch.setattr(fs, "user_cache_dir", lambda: tmp_path / "cache")
    monkeypatch.setenv("MPLCONFIGDIR", "/tmp/pyinstaller-temp")

    config_dir = fs.use_persistent_mpl_config_dir()

    assert config_dir is not None
    assert config_dir.is_dir()
    assert config_dir.parent == tmp_path / "cache"
    assert os.environ["MPLCONFIGDIR"] == str(config_dir)
