from collections import OrderedDict

import xarray as xr

from pbp.hmb_gen.hmb_metadata import (
    HmbMetadataHelper,
    parse_attributes,
    replace_snippets,
)


def test_parse_attributes_json():
    contents = """
        {
            "a1": "Lorem ipsum",
            "a2": "ipsum amet."
        }
    """
    attrs = parse_attributes(contents, ".json")
    assert attrs == OrderedDict(
        {
            "a1": "Lorem ipsum",
            "a2": "ipsum amet.",
        }
    )


def test_parse_attributes_yaml():
    contents = """
        title: >-
          Hybrid Millidecade Band Sound Pressure Levels Computed at 1 Minute Resolution
          from Oceanic Passive Acoustic Monitoring Recordings
          at the Monterey Accelerated Research System (MARS) Cabled Observatory
    """
    attrs = parse_attributes(contents, ".yaml")
    assert attrs == OrderedDict(
        {
            "title": "Hybrid Millidecade Band Sound Pressure Levels Computed at 1 Minute Resolution from Oceanic Passive Acoustic Monitoring Recordings at the Monterey Accelerated Research System (MARS) Cabled Observatory",
        }
    )


def test_replace_snippets():
    attributes = OrderedDict(
        {
            "a1": "Lorem ipsum, {{foo}} ipsum.",
            "a2": "ipsum amet.",
        }
    )

    replaced = replace_snippets(
        attributes=attributes,
        snippets={
            "{{foo}}": "XYZ",
        },
    )

    assert replaced == OrderedDict(
        {
            "a1": "Lorem ipsum, XYZ ipsum.",
            "a2": "ipsum amet.",
        }
    )


class _RecordingLog:
    def __init__(self):
        self.records: list[tuple[str, str]] = []

    def __getattr__(self, level: str):
        return lambda msg: self.records.append((level, msg))


def _levels(variable_attributes) -> list[str]:
    log = _RecordingLog()
    helper = HmbMetadataHelper(log, variable_attributes=variable_attributes)  # type: ignore
    da = xr.DataArray([1.0], dims=["time"])
    helper.add_variable_attributes(da, "psd")
    helper.add_variable_attributes(da, "effort")
    assert da.attrs == ({"units": "dB"} if variable_attributes else {})
    return [level for level, _ in log.records]


def test_add_variable_attributes():
    # no variable attributes given at all (they are optional): no warnings
    assert _levels(None) == []
    # given, but missing for some variable: warning for that variable
    assert _levels(OrderedDict({"psd": {"units": "dB"}})) == ["debug", "warning"]
