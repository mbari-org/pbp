from src.file_helper import FileHelper


def main():
    json_base_dir = "tests/jsons"
    audio_base_dir = None

    file_helper = FileHelper(json_base_dir, audio_base_dir)

    if not file_helper.select_day(2022, 11, 2):
        return

    for audio_segment in file_helper.gen_audio_segments():
        print(f"  len(segment) = {len(audio_segment):,}")
        print(audio_segment)


if __name__ == "__main__":
    main()
