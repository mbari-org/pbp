from pbp.misc_helper import gen_hour_minute_times, map_prefix, extract_datetime
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


def test_extract_datetime():
    # Test flexible parsing - pattern found anywhere in string (last complete match is used)
    result = extract_datetime("path/to/MARS_20250914_122000.wav", "%Y%m%d_%H%M%S")
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test with different filename format
    result = extract_datetime("data_20230105080530.flac", "%Y%m%d%H%M%S")
    expected = datetime(2023, 1, 5, 8, 5, 30, tzinfo=timezone.utc)
    assert result == expected

    # Test with 2-digit year
    result = extract_datetime("path/foo_250914_122000.wav", "%y%m%d_%H%M%S")
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test with date-only pattern
    result = extract_datetime("/path/daily_20250914.wav", "%Y%m%d")
    expected = datetime(2025, 9, 14, 0, 0, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test with ISO format timestamp
    result = extract_datetime(
        "path/recording-2025-09-14T12:20:00.wav", "%Y-%m-%dT%H:%M:%S"
    )
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test exact match (entire string is timestamp)
    result = extract_datetime("20250914_122000", "%Y%m%d_%H%M%S")
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test when pattern doesn't exist in string
    result = extract_datetime("MARS_20250914_122000.wav", "%Y-%m-%d")
    assert result is None

    # Test with invalid date
    result = extract_datetime("MARS_20250230_122000.wav", "%Y%m%d_%H%M%S")
    assert result is None

    # Test empty string
    result = extract_datetime("", "%Y%m%d_%H%M%S")
    assert result is None

    # Test with multiple matches - returns last complete match
    result = extract_datetime("old_20240101_new_20250914_122000.wav", "%Y%m%d_%H%M%S")
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected

    # Test with multiple complete matches - returns last one
    result = extract_datetime(
        "data_20240101_120000_backup_20250914_122000.wav", "%Y%m%d_%H%M%S"
    )
    expected = datetime(2025, 9, 14, 12, 20, 0, tzinfo=timezone.utc)
    assert result == expected
