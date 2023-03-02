from src.file_helper import FileHelper
from src.misc_helper import gen_hour_minute_times


def main():
    json_base_dir = "tests/json"
    audio_base_dir = "tests/wav"

    segment_size_in_mins: int = 1

    file_helper = FileHelper(json_base_dir, audio_base_dir, segment_size_in_mins)

    if not file_helper.select_day(2022, 9, 2):
        return

    for at_hour, at_minute in gen_hour_minute_times(segment_size_in_mins):
        print(f"extracting segment at {at_hour:02}h:{at_minute:02}m ...")
        audio_segment = file_helper.extract_audio_segment(at_hour, at_minute)
        if audio_segment is None:
            print(f"ERROR: cannot get audio segment at {at_hour:02}:{at_minute:02}")
            return
        print(f"  √ segment loaded, len = {len(audio_segment):,}")
        # print(audio_segment)


if __name__ == "__main__":
    main()
