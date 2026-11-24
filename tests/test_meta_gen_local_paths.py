"""
NRS metadata generation from local files (https://github.com/mbari-org/pbp/issues/78),
including plain absolute paths (e.g., "C:\\..." on Windows).
"""

import json
from datetime import datetime
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from pbp.meta_gen.gen_nrs import NRSMetadataGenerator
from pbp.util.logging_helper import create_logger

FS = 8000
SECONDS_PER_FILE = 60
TIMES = ["000000", "000100", "000200"]


def _make_nrs_files(audio_dir: Path) -> None:
    audio_dir.mkdir(parents=True)
    sig = np.zeros(SECONDS_PER_FILE * FS)
    for t in TIMES:
        sf.write(audio_dir / f"NRS11_20191024_{t}.flac", sig, FS)


@pytest.mark.parametrize("uri_kind", ["file_uri", "absolute_path", "relative_path"])
def test_nrs_generator_local(tmp_path, monkeypatch, uri_kind: str):
    audio_dir = tmp_path / "audio"
    _make_nrs_files(audio_dir)
    if uri_kind == "file_uri":
        uri = audio_dir.as_uri()  # file:///...
    elif uri_kind == "absolute_path":
        uri = str(audio_dir)  # e.g., C:\\... on Windows
    else:
        monkeypatch.chdir(tmp_path)
        uri = "audio"

    json_dir = tmp_path / "json"
    NRSMetadataGenerator(
        log=create_logger(),
        uri=uri,
        json_base_dir=json_dir.as_posix(),
        prefixes=["NRS11_"],
        start=datetime(2019, 10, 24),
        end=datetime(2019, 10, 24),
        seconds_per_file=SECONDS_PER_FILE,
    ).run()

    json_file = json_dir / "2019" / "20191024.json"
    assert json_file.exists()
    entries = json.loads(json_file.read_text())
    assert [Path(e["uri"]).name for e in entries] == [
        f"NRS11_20191024_{t}.flac" for t in TIMES
    ]
    assert all(e["duration_secs"] == SECONDS_PER_FILE for e in entries)
