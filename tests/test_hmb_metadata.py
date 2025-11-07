from collections import OrderedDict
import pytest

from pbp.hmb_gen.hmb_metadata import parse_attributes, replace_snippets


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


def test_parse_attributes_invalid_json():
    """Test that invalid JSON raises appropriate error"""
    contents = """
        {
            "a1": "Lorem ipsum",
            "a2": "ipsum amet."
            INVALID
        }
    """
    with pytest.raises(Exception):  # JSONDecodeError
        parse_attributes(contents, ".json")


def test_parse_attributes_invalid_yaml():
    """Test that invalid YAML raises appropriate error"""
    contents = """
        title: >-
          Invalid YAML
        invalid: [unclosed
    """
    with pytest.raises(Exception):  # yaml.YAMLError
        parse_attributes(contents, ".yaml")


def test_parse_attributes_unsupported_format():
    """Test that unsupported file format raises ValueError"""
    contents = "some content"
    with pytest.raises(ValueError, match="Unrecognized contents for format"):
        parse_attributes(contents, ".txt")
