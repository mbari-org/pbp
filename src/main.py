from argparse import ArgumentParser, RawTextHelpFormatter

from src.file_helper import FileHelper

from src.misc_helper import info, set_logger

from src.process_helper import ProcessHelper


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
        "--audio-path-map-prefix",
        type=str,
        metavar="from~to",
        default="",
        help="Prefix mapping to get actual audio uri to be used."
        " Example: 's3://pacific-sound-256khz-2022~file:///PAM_Archive/2022'.",
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
        "--gen-csv",
        default=False,
        action="store_true",
        help="Also generate CSV version of the result. By default, only NetCDF is generated.",
    )

    parser.add_argument(
        "--save-extracted-wav",
        default=False,
        action="store_true",
        help="Save each extracted segment",
    )

    parser.add_argument(
        "--save-segment-result",
        default=False,
        action="store_true",
        help="Save result for each extracted segment",
    )

    parser.add_argument(
        "--max-segments",
        type=int,
        default=0,
        help="Test convenience: limit number of segments to process. By default, 0 (no limit).",
    )

    parser.add_argument(
        "-j",
        "--cpus",
        type=int,
        default=1,
        metavar="num",
        help="Number of cpus to use. 0 will indicate all available cpus. By default, 1.",
    )

    return parser.parse_args()


def main(opts):
    set_logger(opts.output_dir, opts.year, opts.month, opts.day)

    file_helper = FileHelper(
        json_base_dir=opts.json_base_dir,
        audio_base_dir=opts.audio_base_dir,
        audio_path_map_prefix=opts.audio_path_map_prefix,
        audio_path_prefix=opts.audio_path_prefix,
    )

    processor_helper = ProcessHelper(
        file_helper,
        output_dir=opts.output_dir,
        gen_csv=opts.gen_csv,
        save_segment_result=opts.save_segment_result,
        save_extracted_wav=opts.save_extracted_wav,
        num_cpus=opts.cpus,
        max_segments=opts.max_segments,
    )

    try:
        processor_helper.process_day(
            year=opts.year,
            month=opts.month,
            day=opts.day,
        )
    except KeyboardInterrupt:
        info("INTERRUPTED")


if __name__ == "__main__":
    main(parse_arguments())
