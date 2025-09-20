from pbp.misc_helper import gen_hour_minute_times, map_prefix, parse_timestamp
from datetime import datetime, timezone


def test_gen_hour_minute_times(snapshot):
    def do_size(segment_size_in_mins: int):
        hour_minute_times = [
            f"{h:02} {m:02}" for (h, m) in gen_hour_minute_times(segment_size_in_mins)
        ]
        day_minutes = 24 * 60
        assert len(hour_minute_times) == day_minutes // segment_size_in_mins
        assert hour_minute_times == snapshot(
            name=f"segment_size_in_mins={segment_size_in_mins:02}"
        )

    do_size(1)
    do_size(10)
    do_size(60)


def test_map_prefix():
    prefix_map = "s3://pacific-sound-256khz-2022~file:///PAM_Archive/2022"

    def check(uri: str, mapped: str):
        assert map_prefix(prefix_map, uri) == mapped

    check(
        "s3://pacific-sound-256khz-2022/09/MARS_20220901_235016.wav",
        "file:///PAM_Archive/2022/09/MARS_20220901_235016.wav",
    )

    check(
        "s3://pacific-sound-256khz-2022/09/MARS_20220921_002442.wav",
        "file:///PAM_Archive/2022/09/MARS_20220921_002442.wav",
    )


def test_parse_timestamp():
    result = parse_timestamp("MARS_20250914_122000.wav", "MARS_%Y%m%d_%H%M%S.wav")
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    result = parse_timestamp("data_20230105_080530.flac", "data_%Y%m%d_%H%M%S.flac")
    expected = datetime(2023, 1, 5, 8, 5, 30, tzinfo=timezone.utc)
    assert result == expected

    # Test with 2-digit year in filename
    result = parse_timestamp("foo_250914_122000.wav", "foo_%y%m%d_%H%M%S.wav")
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test with only date in filename
    result = parse_timestamp("daily_20250914.wav", "daily_%Y%m%d.wav")
    expected = datetime(2025, 9, 14, 0, 0, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test with pattern that doesn't match string
    result = parse_timestamp("MARS_20250914_122000.wav", "HYDROPHONE_%Y%m%d_%H%M%S.wav")
    assert result is None

    # Test with wrong extension
    result = parse_timestamp("MARS_20250914_122000.wav", "MARS_%Y%m%d_%H%M%S.flac")
    assert result is None

    # Test with invalid date
    result = parse_timestamp("MARS_20250230_122000.wav", "MARS_%Y%m%d_%H%M%S.wav")
    assert result is None

    # Test empty string
    result = parse_timestamp("", "MARS_%Y%m%d_%H%M%S.wav")
    assert result is None
