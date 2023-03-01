from src.file_helper import FileHelper
from src.misc_helper import gen_hour_minute_times


def main():
    json_base_dir = "tests/jsons"
    audio_base_dir = "tests/wavs"

    segment_size_in_mins: int = 1

    file_helper = FileHelper(json_base_dir, audio_base_dir, segment_size_in_mins)

    if not file_helper.select_day(2022, 11, 2):
        return

    for at_hour, at_minute in gen_hour_minute_times(segment_size_in_mins):
        audio_segment = file_helper.extract_audio_segment(at_hour, at_minute)
        if audio_segment is None:
            print(f"ERROR: cannot get audio segment at {at_hour:02}:{at_minute:02}")
            return
        print(f"  len(segment) = {len(audio_segment):,}")
        print(audio_segment)


if __name__ == "__main__":
    main()
