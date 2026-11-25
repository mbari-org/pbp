# Tests for URI handling in `hmb-gen --input-file` mode.

import pathlib
from argparse import Namespace

import numpy as np
import pytest
import soundfile as sf
import xarray as xr

from pbp.hmb_gen.main_hmb_generator_file import (
    _resolve_local_filename,
    main_hmb_generator_file,
)
from pbp.util.logging_helper import create_logger
from pbp.util.uri_handler import UriHandler

VARIABLE_ATTRS_YAML = """
time:
  long_name: UTC time beginning each 1-minute temporal bin
  units: seconds since 1970-01-01T00:00:00Z
psd:
  units: dB
"""


@pytest.fixture
def uri_handler():
    return UriHandler(create_logger())


def test_resolve_local_filename(uri_handler, tmp_path, capsys):
    file = tmp_path / "attrs.yaml"
    file.write_text("{}")

    assert _resolve_local_filename(uri_handler, str(file), "--opt") == str(file)
    assert _resolve_local_filename(uri_handler, file.as_uri(), "--opt") == str(file)

    missing = tmp_path / "missing.yaml"
    assert _resolve_local_filename(uri_handler, str(missing), "--opt") is None
    assert _resolve_local_filename(uri_handler, missing.as_uri(), "--opt") is None
    assert "ERROR: --opt: file not found: " in capsys.readouterr().out


@pytest.mark.parametrize(
    "uri,option",
    [
        ("s3://some-bucket/attrs.yaml", "--s3"),
        ("gs://some-bucket/attrs.yaml", "--gs"),
    ],
)
def test_resolve_local_filename_cloud_without_client(uri_handler, uri, option, capsys):
    assert _resolve_local_filename(uri_handler, uri, "--opt") is None
    assert option in capsys.readouterr().out


def _file_mode_opts(tmp_path: pathlib.Path, **kwargs) -> Namespace:
    wav = tmp_path / "SJW7045_20261022_235000.wav"
    rate = 8000
    rng = np.random.default_rng(11)
    sf.write(wav, 0.02 * rng.standard_normal(120 * rate), rate, subtype="FLOAT")
    d = dict(
        input_file=str(wav),
        output_dir=str(tmp_path),
        timestamp_pattern="%Y%m%d_%H%M%S",
        time_resolution=60,
        download_dir=None,
        assume_downloaded_files=False,
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


def test_input_file_mode_with_file_uris(tmp_path):
    variable_attrs = tmp_path / "variableAttributes.yaml"
    variable_attrs.write_text(VARIABLE_ATTRS_YAML)

    sensitivity = tmp_path / "sensitivity.nc"
    xr.DataArray(
        data=np.full(5, -170.0),
        dims=["frequency"],
        coords={"frequency": np.linspace(0, 4000, 5)},
        name="sensitivity",
    ).to_netcdf(sensitivity)

    opts = _file_mode_opts(
        tmp_path,
        variable_attrs=variable_attrs.as_uri(),
        sensitivity_uri=sensitivity.as_uri(),
    )
    main_hmb_generator_file(opts)

    with xr.open_dataset(tmp_path / "SJW7045_20261022_235000.nc") as ds:
        assert "sensitivity" in ds.data_vars
        assert ds.psd.attrs["units"] == "dB"
        assert ds.time.attrs["long_name"].startswith("UTC time")
        assert str(ds.time.values[0]).startswith("2026-10-22T23:50:00")


@pytest.mark.parametrize("option", ["variable_attrs", "global_attrs", "sensitivity_uri"])
def test_input_file_mode_with_missing_uri(tmp_path, option, capsys):
    opts = _file_mode_opts(tmp_path, **{option: (tmp_path / "missing").as_uri()})
    with pytest.raises(SystemExit):
        main_hmb_generator_file(opts)
    out = capsys.readouterr().out
    assert f"ERROR: --{option.replace('_', '-')}: file not found: " in out
