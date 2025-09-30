from typing import Any, List

import pytest
from pbp.hmb_gen.json_support import get_intersecting_entries, parse_json_file
from pbp.util.logging_helper import create_logger


def _as_jsons(the_list: List[Any]) -> List[str]:
    return [e.to_json() for e in the_list]


@pytest.fixture
def json_entries():
    return list(parse_json_file("tests/json/2022/20220902.json"))


def test_json_parsing(json_entries, snapshot):
    assert _as_jsons(json_entries) == snapshot


def test_get_intersecting_entries(json_entries, snapshot):
    year, month, day = 2022, 9, 2

    log = create_logger()

    def do_test(
        segment_size_in_secs: int, at_hour: int, at_minute: int, at_second: int = 0
    ):
        intersecting_entries = get_intersecting_entries(
            log,
            json_entries,
            year,
            month,
            day,
            at_hour,
            at_minute,
            at_second,
            segment_size_in_secs=segment_size_in_secs,
        )
        assert _as_jsons(intersecting_entries) == snapshot(
            name=f"size={segment_size_in_secs:03} h={at_hour:02} m={at_minute:02} s={at_second:02}"
        )

    do_test(60, 0, 0)  # equivalent to 1 minute
    do_test(60, 23, 59)  # equivalent to 1 minute
    do_test(1200, 0, 0)  # equivalent to 20 minutes
    do_test(600, 23, 40)  # equivalent to 10 minutes
    do_test(10, 0, 0, 30)  # 10-second segment starting at 00:00:30
    do_test(15, 12, 30, 45)  # 15-second segment starting at 12:30:45
    do_test(5, 6, 15, 22)  # 5-second segment starting at 06:15:22


@pytest.fixture
def json_entries_2():
    res = list(parse_json_file("tests/json/2022/20221102.json"))
    return res


def test_json_parsing_2(json_entries_2, snapshot):
    assert _as_jsons(json_entries_2) == snapshot
