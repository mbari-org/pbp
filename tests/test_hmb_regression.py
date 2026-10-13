"""
Regression tests for the PyPAM-dependent HMB generation path.

These capture current numeric results (in `tests/golden/*.npz`) and dataset
structure/metadata (syrupy snapshots) so that dependency updates, in particular
of `lifewatch-pypam`, can be verified for no unintended changes.

Regenerate goldens with `pytest --golden-update` only when a change in results
is understood and accepted.
"""

import json
import pathlib
from argparse import Namespace
from datetime import datetime, timezone
from typing import Any

import numpy as np
import pytest
import soundfile as sf
import xarray as xr

from pbp import get_pbp_version, get_pypam_version
from pbp.hmb_gen.file_helper import FileHelper
from pbp.hmb_gen.hmso_pypam import HmsoPypam, SpectrumBander
from pbp.hmb_gen.main_hmb_generator_file import FileProcessor
from pbp.hmb_gen.process_helper import ProcessHelper
from pbp.hmb_gen.pypam_support import PypamSupport
from pbp.util.logging_helper import create_logger

# float64 intermediate results:
RTOL_F64 = 1e-9
# float32 final (dB) results:
RTOL_F32 = 1e-6

TEST_WAV = pathlib.Path("tests/wav/test.wav").absolute()
GLOBAL_ATTRS = "metadata/mb05/globalAttributes_MB05.yaml"
VARIABLE_ATTRS = "metadata/mb05/variableAttributes_MB05.yaml"


@pytest.fixture
def log():
    return create_logger()


def _synthetic_signal(fs: int, secs: int) -> np.ndarray:
    rng = np.random.default_rng(42)
    t = np.arange(fs * secs) / fs
    tones = sum(a * np.sin(2 * np.pi * f * t) for f, a in [(100, 0.5), (1000, 0.2)])
    return tones + 0.05 * rng.standard_normal(len(t))


def _test_wav_data() -> tuple[np.ndarray, int]:
    data, fs = sf.read(TEST_WAV, dtype="float64")
    return data, fs


def _sensitivity_da(fs: int) -> xr.DataArray:
    freqs = np.linspace(0, fs / 2, 101)
    return xr.DataArray(
        data=-170.0 + 3.0 * np.sin(freqs / 1000.0),
        coords={"frequency": freqs},
        dims=["frequency"],
        name="sensitivity",
    )


def _normalize_attrs(attrs: dict[str, Any]) -> dict[str, Any]:
    """Masks values that legitimately vary across runs/versions."""
    versions = {
        get_pbp_version(): "<PBP_version>",
        get_pypam_version(): "<PyPAM_version>",
    }
    res = {}
    for k, v in attrs.items():
        if k == "date_created":
            v = "<date_created>"
        elif isinstance(v, str):
            for actual, placeholder in versions.items():
                v = v.replace(actual, placeholder)
        elif isinstance(v, np.generic):
            v = v.item()
        elif isinstance(v, np.ndarray):
            v = v.tolist()
        res[k] = v
    return res


def _structure(ds: xr.Dataset) -> dict[str, Any]:
    return {
        "dims": dict(ds.sizes),
        "attrs": _normalize_attrs(dict(ds.attrs)),
        "variables": {
            name: {
                "dims": list(var.dims),
                "dtype": str(var.dtype),
                "attrs": _normalize_attrs(dict(var.attrs)),
            }
            for name, var in sorted(ds.variables.items())
        },
    }


def _dataset_arrays(ds: xr.Dataset) -> dict[str, np.ndarray]:
    return {str(name): var.values for name, var in ds.variables.items()}


# --- HmsoPypam (direct pypam usage) ---


@pytest.mark.parametrize(
    "fs,nfft", [(8000, 8000), (16000, 16000), (48000, 48000), (48000, 4096)]
)
def test_hybrid_millidecade_limits(golden, fs, nfft):
    hmso = HmsoPypam(fs, nfft)
    bands_limits, bands_c = hmso.get_hybrid_millidecade_limits([0, fs / 2])
    golden.check(
        f"hmb_limits_fs{fs}_nfft{nfft}",
        {"bands_limits": np.asarray(bands_limits), "bands_c": np.asarray(bands_c)},
        rtol=RTOL_F64,
    )


@pytest.mark.parametrize("scaling", ["density", "spectrum"])
def test_compute_spectrum_synthetic(golden, scaling):
    fs = 8000
    hmso = HmsoPypam(fs, fs)
    fbands, spectrum = hmso.compute_spectrum(_synthetic_signal(fs, 10), scaling=scaling)
    golden.check(
        f"spectrum_synthetic_{scaling}",
        {"fbands": fbands, "spectrum": spectrum},
        rtol=RTOL_F64,
    )


def test_compute_spectrum_wav(golden):
    data, fs = _test_wav_data()
    hmso = HmsoPypam(fs, fs)
    fbands, spectrum = hmso.compute_spectrum(data[: 10 * fs])
    golden.check("spectrum_wav", {"fbands": fbands, "spectrum": spectrum}, rtol=RTOL_F64)


def test_spectra_ds_to_bands(golden):
    fs = 8000
    hmso = HmsoPypam(fs, fs)
    signal = _synthetic_signal(fs, 20)
    spectra, fbands = [], None
    for i in range(2):
        fbands, spectrum = hmso.compute_spectrum(signal[i * 10 * fs : (i + 1) * 10 * fs])
        spectra.append(spectrum)
    psd = xr.DataArray(
        data=spectra,
        coords={"time": [0, 10], "frequency": fbands},
        dims=["time", "frequency"],
    )
    bands_limits, bands_c = hmso.get_hybrid_millidecade_limits([0, fs / 2])
    res = hmso.spectra_ds_to_bands(psd, bands_limits, bands_c)
    golden.check(
        "spectra_ds_to_bands",
        {
            "values": res.values,
            "frequency_bins": res.frequency_bins.values,
            "lower_frequency": res.lower_frequency.values,
            "upper_frequency": res.upper_frequency.values,
        },
        rtol=RTOL_F64,
    )


@pytest.mark.parametrize(
    "fs,nfft,subset_to",
    [
        (8000, 8000, None),
        (48000, 48000, None),
        (48000, 48000, (10, 20000)),
        (48000, 4096, None),
        (48000, 4096, (10, 20000)),
        (256000, 256000, None),
        (256000, 256000, (100, 3000)),
    ],
)
def test_spectrum_bander_matches_pypam(log, fs, nfft, subset_to):
    # SpectrumBander (per-segment) must be equivalent to pypam's spectra_ds_to_bands.
    hmso = HmsoPypam(fs, nfft)
    fbands, _ = hmso.compute_spectrum(_synthetic_signal(fs, 2))
    bands_limits, bands_c = hmso.get_hybrid_millidecade_limits([0, fs / 2])
    if subset_to is not None:
        bands_limits, bands_c = PypamSupport(log)._adjust_limits(
            bands_limits, bands_c, subset_to
        )
    spectra = np.random.default_rng(42).random((3, len(fbands)))
    psd = xr.DataArray(
        data=spectra,
        coords={"time": [0, 1, 2], "frequency": fbands},
        dims=["time", "frequency"],
    )
    expected = hmso.spectra_ds_to_bands(psd, bands_limits, bands_c).values

    bander = SpectrumBander(fbands, bands_limits, hmso.fft_bin_width)
    actual = np.stack([bander.apply(s) for s in spectra])
    np.testing.assert_allclose(actual, expected, rtol=RTOL_F64)


# --- PypamSupport (aggregation) ---


@pytest.mark.parametrize(
    "subset_to,with_sensitivity",
    [(None, False), ((10, 20000), False), ((10, 20000), True)],
)
def test_pypam_support_aggregation(golden, log, subset_to, with_sensitivity):
    data, fs = _test_wav_data()
    seg = 10 * fs
    base = datetime(2023, 1, 1, tzinfo=timezone.utc).timestamp()

    def dt(i: int) -> datetime:
        return datetime.fromtimestamp(base + 10 * i, tz=timezone.utc)

    ps = PypamSupport(log)
    ps.add_missing_segment(dt(0))  # missing before set_parameters
    ps.set_parameters(fs, subset_to=subset_to)
    ps.add_segment(dt(1), data[0:seg])
    ps.add_missing_segment(dt(2))
    ps.add_segment(dt(3), data[seg : 2 * seg])
    ps.add_segment(dt(4), data[2 * seg : 2 * seg + seg // 2])  # partial segment

    result = ps.process_captured_segments(
        sensitivity_da=_sensitivity_da(fs) if with_sensitivity else None
    )
    assert result is not None
    name = f"pypam_support_{'full' if subset_to is None else 'subset'}"
    name += "_sens" if with_sensitivity else ""
    golden.check(
        name,
        {
            "psd": result.psd_da.values,
            "time": result.psd_da.time.values,
            "frequency": result.psd_da.frequency.values,
            "effort": result.effort_da.values,
        },
        rtol=RTOL_F32,
    )


def test_pypam_support_no_actual_segments(log):
    ps = PypamSupport(log)
    ps.add_missing_segment(datetime(2023, 1, 1, tzinfo=timezone.utc))
    assert ps.process_captured_segments() is None


# --- End-to-end ---


def _write_day_json(json_base_dir: pathlib.Path, audio_dir: pathlib.Path) -> None:
    # Two 60-sec entries (copies of test.wav) starting at 00:00:30 and 00:01:30, so that:
    #   segment 00:00 is partially covered (first file),
    #   segment 00:01 spans both files,
    #   segment 00:02 is partially covered (second file),
    #   segments 00:03, 00:04 are missing.
    audio_dir.mkdir()
    entries = []
    for m in (0, 1):
        wav = audio_dir / f"TEST_20230101_000{m}30.wav"
        wav.write_bytes(TEST_WAV.read_bytes())
        entries.append(
            {
                "uri": wav.as_uri(),
                "start": f"2023-01-01T00:0{m}:30Z",
                "end": f"2023-01-01T00:0{m + 1}:30Z",
                "duration_secs": 60.0,
                "channels": 1,
                "jitter": 0,
            }
        )
    (json_base_dir / "2023").mkdir(parents=True)
    (json_base_dir / "2023" / "20230101.json").write_text(json.dumps(entries))


def test_process_day_end_to_end(golden, snapshot, log, tmp_path):
    json_base_dir = tmp_path / "json"
    _write_day_json(json_base_dir, tmp_path / "audio")
    output_dir = tmp_path / "output"

    file_helper = FileHelper(log=log, json_base_dir=str(json_base_dir))
    process_helper = ProcessHelper(
        log=log,
        file_helper=file_helper,
        output_dir=str(output_dir),
        output_prefix="TEST_",
        add_quality_flag=True,
        global_attrs_uri=GLOBAL_ATTRS,
        set_global_attrs=[["serial_number", "000000"]],
        variable_attrs_uri=VARIABLE_ATTRS,
        voltage_multiplier=2.5,
        sensitivity_flat_value=176.0,
        max_segments=5,
        subset_to=(10, 20000),
    )
    result = process_helper.process_day("20230101")
    assert result is not None
    assert result.generated_filenames == [f"{output_dir}/TEST_20230101.nc"]

    ds = result.dataset
    assert _structure(ds) == snapshot
    golden.check("process_day", _dataset_arrays(ds), rtol=RTOL_F32)

    # generated NetCDF should have the same (raw, undecoded) values:
    with xr.open_dataset(result.generated_filenames[0], decode_times=False) as nc:
        assert _structure(nc) == snapshot(name="netcdf")
        golden.check("process_day", _dataset_arrays(nc), rtol=RTOL_F32)


def test_file_processor_end_to_end(golden, snapshot, log, tmp_path):
    sensitivity_nc = tmp_path / "sensitivity.nc"
    _sensitivity_da(48000).to_netcdf(sensitivity_nc)
    output_filename = tmp_path / "test.nc"

    opts = Namespace(
        input_file=str(TEST_WAV),
        output_dir=str(tmp_path),
        time_resolution=15,
        timestamp_pattern=None,
        global_attrs=GLOBAL_ATTRS,
        variable_attrs=VARIABLE_ATTRS,
        sensitivity_uri=str(sensitivity_nc),
        sensitivity_flat_value=None,
        voltage_multiplier=None,
        subset_to=[10, 20000],
        add_quality_flag=False,
    )
    with sf.SoundFile(TEST_WAV) as sound_file:
        result = FileProcessor(
            opts,
            log,
            sound_file,
            datetime(2023, 1, 1, tzinfo=timezone.utc),
            xr.open_dataarray(sensitivity_nc),
            str(output_filename),
        ).process()
    assert result is not None

    ds = result.dataset
    assert _structure(ds) == snapshot
    golden.check("file_processor", _dataset_arrays(ds), rtol=RTOL_F32)

    with xr.open_dataset(output_filename, decode_times=False) as nc:
        assert _structure(nc) == snapshot(name="netcdf")
        golden.check("file_processor", _dataset_arrays(nc), rtol=RTOL_F32)
