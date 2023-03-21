from argparse import ArgumentParser, RawTextHelpFormatter

from src.file_helper import FileHelper

from src.misc_helper import info, parse_date, set_logger

from src.process_helper import ProcessHelper


def parse_arguments():
    description = "Pypam based processing of a Pacific Sound data."
    example = """
Examples:
    src/main.py  --json-base-dir=tests/json \\
                 --audio-base-dir=tests/wav \\
                 --date=20220902 \\
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

    parser.add_argument(
        "--date",
        type=str,
        required=True,
        metavar="YYYYMMDD",
        help="The date to be processed.",
    )

    parser.add_argument(
        "--sensitivity-uri",
        type=str,
        default=None,
        metavar="file",
        help="URI of sensitivity NetCDF for calibration of result. By default, a flat value of 178 is applied.",
    )

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
        metavar="num",
        help="Test convenience: limit number of segments to process. By default, 0 (no limit).",
    )

    parser.add_argument(
        "--subset-to",
        type=int,
        nargs=2,
        default=None,
        metavar=("lower", "upper"),
        help="Subset the resulting PSD to [lower, upper), in terms of central frequency.",
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
    year, month, day = parse_date(opts.date)

    set_logger(opts.output_dir, year, month, day)

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
        sensitivity_uri=opts.sensitivity_uri,
        save_segment_result=opts.save_segment_result,
        save_extracted_wav=opts.save_extracted_wav,
        num_cpus=opts.cpus,
        max_segments=opts.max_segments,
        subset_to=tuple(opts.subset_to),
    )
    try:
        processor_helper.process_day(
            year=year,
            month=month,
            day=day,
        )
    except KeyboardInterrupt:
        info("INTERRUPTED")


if __name__ == "__main__":
    main(parse_arguments())
