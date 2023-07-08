from collections import OrderedDict

from src.metadata import replace_snippets


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
