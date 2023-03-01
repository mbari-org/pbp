from src.misc_helper import gen_hour_minute_times


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
