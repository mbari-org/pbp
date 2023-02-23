from src.json_support import parse_json_lines_file


def test_json_parsing(snapshot):
    parsed = list(parse_json_lines_file("tests/jsons/20220902.json"))
    assert parsed == snapshot
