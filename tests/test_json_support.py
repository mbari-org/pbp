import pytest
from src.json_support import get_intersecting_entries, parse_json_lines_file


@pytest.fixture
def json_entries():
    return list(parse_json_lines_file("tests/json/20220902.json"))


def test_json_parsing(json_entries, snapshot):
    assert json_entries == snapshot


def test_get_intersecting_entries(json_entries, snapshot):
    year, month, day = 2022, 9, 2

    def do_test(segment_size_in_mins: int, at_hour: int, at_minute: int):
        intersecting_entries = get_intersecting_entries(
            json_entries, segment_size_in_mins, year, month, day, at_hour, at_minute
        )
        assert intersecting_entries == snapshot(
            name=f"size={segment_size_in_mins:02} h={at_hour:02} m={at_minute:02}"
        )

    do_test(1, 0, 0)
    do_test(1, 23, 59)
    do_test(20, 0, 0)
    do_test(10, 23, 40)
