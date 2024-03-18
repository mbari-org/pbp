from typing import Any, List

import pytest
from pbp.json_support import get_intersecting_entries, parse_json_file
from pbp.logging_helper import create_logger


def _as_jsons(the_list: List[Any]) -> List[str]:
    return [e.to_json() for e in the_list]


@pytest.fixture
def json_entries():
    return list(parse_json_file("tests/json/2022/20220902.json"))


def test_json_parsing(json_entries, snapshot):
    assert _as_jsons(json_entries) == snapshot


def test_get_intersecting_entries(json_entries, snapshot):
    year, month, day = 2022, 9, 2

    logger = create_logger()

    def do_test(segment_size_in_mins: int, at_hour: int, at_minute: int):
        intersecting_entries = get_intersecting_entries(
            logger,
            json_entries,
            year,
            month,
            day,
            at_hour,
            at_minute,
            segment_size_in_mins=segment_size_in_mins,
        )
        assert _as_jsons(intersecting_entries) == snapshot(
            name=f"size={segment_size_in_mins:02} h={at_hour:02} m={at_minute:02}"
        )

    do_test(1, 0, 0)
    do_test(1, 23, 59)
    do_test(20, 0, 0)
    do_test(10, 23, 40)


@pytest.fixture
def json_entries_2():
    res = list(parse_json_file("tests/json/2022/20221102.json"))
    return res


def test_json_parsing_2(json_entries_2, snapshot):
    assert _as_jsons(json_entries_2) == snapshot
