"""
Tests for edge cases in HMB generation reported in
https://github.com/mbari-org/pbp/issues/130 and
https://github.com/mbari-org/pbp/issues/131,
as well as the related startup parameter checks.
"""

import json
import pathlib
import sys
from argparse import Namespace
from datetime import datetime, timezone
from typing import Optional

import numpy as np
import pytest
import soundfile as sf
import xarray as xr

from pbp.hmb_gen.file_helper import FileHelper
from pbp.hmb_gen.main_hmb_generator import check_options
from pbp.hmb_gen.main_hmb_generator_args import parse_arguments
from pbp.hmb_gen.main_hmb_generator_file import FileProcessor
from pbp.hmb_gen.param_checks import check_date, check_hmb_gen_params
from pbp.hmb_gen.process_helper import ProcessHelper, save_dataset_to_netcdf
from pbp.util.logging_helper import create_logger

FS = 8000


@pytest.fixture
def log():
    return create_logger()


def _make_wav(path: pathlib.Path, secs: float, rate: int = FS) -> None:
    rng = np.random.default_rng(11)
    t = np.arange(int(secs * rate)) / rate
    sig = 0.3 * np.sin(2 * np.pi * 440 * t) + 0.02 * rng.standard_normal(len(t))
    sf.write(path, sig, rate, subtype="FLOAT")


def _write_day_json(
    json_base_dir: pathlib.Path, date: str, entries: list[tuple[pathlib.Path, float, str]]
) -> None:
    year_dir = json_base_dir / date[:4]
    year_dir.mkdir(parents=True, exist_ok=True)
    (year_dir / f"{date}.json").write_text(
        json.dumps(
            [
                {"uri": wav.as_uri(), "duration_secs": secs, "start": start}
                for wav, secs, start in entries
            ]
        )
    )


def _process_day(
    log, tmp_path: pathlib.Path, date: str, max_segments: int, **kwargs
) -> xr.Dataset:
    file_helper = FileHelper(log, json_base_dir=str(tmp_path / "json"))
    process_helper = ProcessHelper(
        log,
        file_helper,
        output_dir=str(tmp_path / "output"),
        output_prefix="TEST_",
        gen_netcdf=False,
        max_segments=max_segments,
        sensitivity_flat_value=-170.0,
        **kwargs,
    )
    result = process_helper.process_day(date)
    assert result is not None
    return result.dataset


def _file_opts(input_file: pathlib.Path, **kwargs) -> Namespace:
    d = dict(
        input_file=str(input_file),
        output_dir=str(input_file.parent),
        time_resolution=60,
        timestamp_pattern=None,
        global_attrs=None,
        variable_attrs=None,
        sensitivity_uri=None,
        sensitivity_flat_value=None,
        voltage_multiplier=None,
        subset_to=None,
        add_quality_flag=False,
    )
    d.update(kwargs)
    return Namespace(**d)


def _process_file(log, input_file: pathlib.Path, output_filename: pathlib.Path, **kwargs):
    with sf.SoundFile(input_file) as sound_file:
        return FileProcessor(
            _file_opts(input_file, **kwargs),
            log,
            sound_file,
            datetime(2024, 1, 1, tzinfo=timezone.utc),
            None,
            str(output_filename),
        ).process()


def _assert_missing_rows(ds: xr.Dataset, rows: list[int]) -> None:
    psd = ds.psd.values
    assert not np.isneginf(psd).any()
    for i in range(psd.shape[0]):
        assert np.isnan(psd[i]).all() == (i in rows), f"row {i}"


# --- #130 ---


def test_exclude_tone_calibration_file_starting_mid_segment(log, tmp_path):
    # 300-sec file starting at 00:00:30, with 45 secs excluded: its 30-sec
    # intersection with segment 00:00 is fully excluded.
    wav = tmp_path / "a.wav"
    _make_wav(wav, 300)
    _write_day_json(tmp_path / "json", "20240101", [(wav, 300.0, "2024-01-01T00:00:30Z")])

    ds = _process_day(
        log, tmp_path, "20240101", max_segments=6, exclude_tone_calibration_seconds=45
    )
    np.testing.assert_array_equal(ds.effort.values, [0, 45, 60, 60, 60, 30])
    assert ds.effort.values.sum() == 300 - 45
    _assert_missing_rows(ds, [0])


def test_sub_nfft_tail_segment_is_missing(log, tmp_path):
    wav = tmp_path / "a.wav"
    _make_wav(wav, 120.5)
    result = _process_file(log, wav, tmp_path / "a.nc", sensitivity_flat_value=-170.0)
    assert result is not None
    ds = result.dataset
    np.testing.assert_array_equal(ds.effort.values, [60, 60, 0])
    _assert_missing_rows(ds, [2])


def test_samplerate_change_segments_are_missing(log, tmp_path):
    wav1, wav2 = tmp_path / "c1.wav", tmp_path / "c2.wav"
    _make_wav(wav1, 120)
    _make_wav(wav2, 120, rate=2 * FS)
    _write_day_json(
        tmp_path / "json",
        "20240102",
        [(wav1, 120.0, "2024-01-02T00:00:00Z"), (wav2, 120.0, "2024-01-02T00:02:00Z")],
    )

    ds = _process_day(log, tmp_path, "20240102", max_segments=6)
    assert ds.sizes["time"] == 6
    np.testing.assert_array_equal(ds.effort.values, [60, 60, 0, 0, 0, 0])
    _assert_missing_rows(ds, [2, 3, 4, 5])


# --- #131 ---


def _assert_saved(result, output_filename: pathlib.Path, num_times: int) -> None:
    assert result is not None
    assert result.generated_filenames == [str(output_filename)]
    with xr.open_dataset(output_filename) as nc:
        assert "psd" in nc.data_vars
        assert nc.sizes["time"] == num_times


def test_save_without_sensitivity(log, tmp_path):
    wav = tmp_path / "a.wav"
    _make_wav(wav, 120)
    output_filename = tmp_path / "a.nc"
    result = _process_file(log, wav, output_filename)
    assert "sensitivity" not in result.dataset.variables
    _assert_saved(result, output_filename, num_times=2)


def test_save_single_segment(log, tmp_path):
    wav = tmp_path / "a.wav"
    _make_wav(wav, 30)
    output_filename = tmp_path / "a.nc"
    result = _process_file(log, wav, output_filename, sensitivity_flat_value=-170.0)
    _assert_saved(result, output_filename, num_times=1)


def test_failed_save_leaves_no_file(log, tmp_path, monkeypatch):
    def failing_to_netcdf(self, path, *args, **kwargs):
        pathlib.Path(path).touch()  # as h5netcdf creates the file before failing
        raise RuntimeError("simulated failure")

    monkeypatch.setattr(xr.Dataset, "to_netcdf", failing_to_netcdf)

    output_filename = tmp_path / "a.nc"
    ds = xr.Dataset({"effort": ("time", [60.0])})
    assert not save_dataset_to_netcdf(log, ds, str(output_filename))
    assert not output_filename.exists()

    wav = tmp_path / "a.wav"
    _make_wav(wav, 120)
    result = _process_file(log, wav, output_filename)
    assert result is not None
    assert result.generated_filenames == []
    assert not output_filename.exists()


# --- Startup parameter checks ---


@pytest.mark.parametrize(
    "date,ok",
    [("20240229", True), ("20230229", False), ("2024-01-01", False), (None, False)],
)
def test_check_date(date: Optional[str], ok: bool):
    assert (check_date(date) == []) == ok


@pytest.mark.parametrize(
    "kwargs,ok",
    [
        ({}, True),
        (dict(time_resolution=1), True),
        (dict(time_resolution=0), False),
        (dict(exclude_tone_calibration_seconds=0), True),
        (dict(exclude_tone_calibration_seconds=-1), False),
        (dict(max_segments=-1), False),
        (dict(subset_to=(10, 20000)), True),
        (dict(subset_to=(20000, 10)), False),
        (dict(subset_to=(-1, 10)), False),
    ],
)
def test_check_hmb_gen_params(kwargs: dict, ok: bool):
    assert (check_hmb_gen_params(**kwargs) == []) == ok


def _cli_errors(monkeypatch, *args: str) -> list[str]:
    monkeypatch.setattr(sys, "argv", ["pbp-hmb-gen", "--output-dir=out", *args])
    return check_options(parse_arguments())


def test_check_options(monkeypatch):
    day = ["--json-base-dir=json", "--date=20240101"]
    assert _cli_errors(monkeypatch, *day) == []
    assert _cli_errors(monkeypatch, *day, "--time-resolution=0") != []
    assert _cli_errors(monkeypatch, "--date=20240101") != []
    assert _cli_errors(monkeypatch, "--json-base-dir=json") != []

    file = ["--input-file=a.wav"]
    assert _cli_errors(monkeypatch, *file) == []
    assert _cli_errors(monkeypatch, *file, "--date=20240101") != []
    assert _cli_errors(monkeypatch, *file, "--exclude-tone-calibration=3") != []
    assert _cli_errors(monkeypatch, *file, "--max-segments=2") != []
