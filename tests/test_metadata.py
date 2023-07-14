from collections import OrderedDict

from src.metadata import parse_attributes, replace_snippets


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
