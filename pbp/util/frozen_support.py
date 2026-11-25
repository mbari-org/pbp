"""
Support for running as a PyInstaller-frozen standalone executable.
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Mapping, Optional


def user_cache_dir(
    platform: str = sys.platform,
    environ: Mapping[str, str] = os.environ,
    home: Optional[Path] = None,
) -> Path:
    """
    Returns the per-user cache directory for pbp on the given platform.
    """
    home = home or Path.home()
    if platform == "darwin":
        return home / "Library" / "Caches" / "mbari-pbp"
    if platform == "win32":
        base = environ.get("LOCALAPPDATA")
        return (
            (Path(base) if base else home / "AppData" / "Local") / "mbari-pbp" / "Cache"
        )
    base = environ.get("XDG_CACHE_HOME")
    return (Path(base) if base else home / ".cache") / "mbari-pbp"


def mpl_config_dir(cache_dir: Path, bundle_dir: str, version: str) -> Path:
    """
    Returns the matplotlib config directory to use for the given bundle.

    Specific to the bundle location and pbp version, as matplotlib's font cache
    refers to font files in the bundle: a moved or updated bundle then gets
    its own directory instead of a font cache with stale paths.
    """
    key = hashlib.sha256(str(Path(bundle_dir).resolve()).encode()).hexdigest()[:10]
    return cache_dir / f"matplotlib-{version}-{key}"


def use_persistent_mpl_config_dir() -> Optional[Path]:
    """
    When running frozen, makes matplotlib use a persistent config directory.

    PyInstaller's matplotlib runtime hook sets MPLCONFIGDIR to a new temporary
    directory on each launch (needed for --onefile bundles, whose location
    changes), so matplotlib rebuilds its font cache every time, which takes
    ~10 secs. Our bundle is --onedir (fixed location), so the cache can persist.

    Must be called before matplotlib is imported. Does nothing if not frozen,
    or if the directory cannot be created (the temporary one is kept then).

    Returns:
        The directory now used, or None.
    """
    bundle_dir = getattr(sys, "_MEIPASS", None)
    if not getattr(sys, "frozen", False) or bundle_dir is None:
        return None

    from pbp import get_pbp_version

    config_dir = mpl_config_dir(user_cache_dir(), bundle_dir, get_pbp_version())
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except OSError:
        return None
    os.environ["MPLCONFIGDIR"] = str(config_dir)
    return config_dir
