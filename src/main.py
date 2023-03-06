from argparse import ArgumentParser, RawTextHelpFormatter

from src import processor

from src.file_helper import FileHelper


def parse_arguments():
    description = "Pypam based processing of a Pacific Sound data."
    example = """
Examples:
    src/main.py  --json-base-dir=tests/json \\
                 --audio-base-dir=tests/wav \\
                 --year=2022 \\
                 --month=9 \\
                 --day=2 \\
                 --output-dir=output
    """

    parser = ArgumentParser(
        description=description, epilog=example, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--json-base-dir",
        type=str,
        metavar="dir",
        required=True,
        help="JSON base directory",
    )

    parser.add_argument(
        "--audio-base-dir",
        type=str,
        metavar="dir",
        default=None,
        help="Audio base directory. By default, none",
    )

    parser.add_argument(
        "--audio-path-prefix",
        type=str,
        metavar="dir",
        default="",
        help="Ad hoc path prefix for wav location, for example, /Volumes."
        " By default, no prefix applied.",
    )

    parser.add_argument("--year", type=int, metavar="YYYY", required=True, help="Year")
    parser.add_argument("--month", type=int, metavar="M", required=True, help="Month")
    parser.add_argument("--day", type=int, metavar="D", required=True, help="Day")

    parser.add_argument(
        "--output-dir",
        type=str,
        metavar="dir",
        required=True,
        help="Output directory",
    )

    parser.add_argument(
        "--save-extracted-wav",
        default=False,
        action="store_true",
        help="Save each extracted segment",
    )

    return parser.parse_args()


def main(opts):
    file_helper = FileHelper(
        json_base_dir=opts.json_base_dir,
        audio_base_dir=opts.audio_base_dir,
        audio_path_prefix=opts.audio_path_prefix,
    )
    try:
        processor.process_day(
            file_helper,
            year=opts.year,
            month=opts.month,
            day=opts.day,
            output_dir=opts.output_dir,
            save_extracted_wav=opts.save_extracted_wav,
        )
    except KeyboardInterrupt:
        print("\nInterrupted")


if __name__ == "__main__":
    main(parse_arguments())
