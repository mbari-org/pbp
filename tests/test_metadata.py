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


# TODO  NOTE: the following test is useful, but will be unnecessary once
#   we keep only the YAML version of the metadata files.
def test_compare_attrs_parsed_from_json_and_yaml():
    for x in ["mars", "chumash"]:
        with open(f"metadata/{x}/globalAttributes.yaml", "r", encoding="UTF-8") as f:
            from_yaml = parse_attributes(f.read(), ".yaml")
        with open(f"metadata/{x}/globalAttributes.json", "r", encoding="UTF-8") as f:
            from_json = parse_attributes(f.read(), ".json")
        assert from_yaml == from_json

        with open(f"metadata/{x}/variableAttributes.yaml", "r", encoding="UTF-8") as f:
            from_yaml = parse_attributes(f.read(), ".yaml")
        with open(f"metadata/{x}/variableAttributes.json", "r", encoding="UTF-8") as f:
            from_json = parse_attributes(f.read(), ".json")
        assert from_yaml == from_json


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
