from argparse import ArgumentParser, RawTextHelpFormatter

from src.file_helper import FileHelper

from src.misc_helper import info, set_logger

from src.process_helper import ProcessHelper


def parse_arguments():
    description = "PyPAM based processing of Pacific Sound data."
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
        "--global-attrs",
        type=str,
        metavar="uri",
        default=None,
        help="URI of JSON file with global attributes to be added to the NetCDF file.",
    )

    parser.add_argument(
        "--variable-attrs",
        type=str,
        metavar="uri",
        default=None,
        help="URI of JSON file with attributes to associate to the variables in the NetCDF file.",
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
        "--voltage-multiplier",
        type=float,
        default=None,
        metavar="value",
        help="Applied on the loaded signal.",
    )

    parser.add_argument(
        "--sensitivity-uri",
        type=str,
        default=None,
        metavar="file",
        help="URI of sensitivity NetCDF for calibration of result. "
        "Has precedence over --sensitivity-flat-value.",
    )

    parser.add_argument(
        "--sensitivity-flat-value",
        type=float,
        default=None,
        metavar="value",
        help="Flat sensitivity value to be used for calibration.",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        metavar="dir",
        required=True,
        help="Output directory",
    )

    parser.add_argument(
        "--output-prefix",
        type=str,
        metavar="prefix",
        default="milli_psd_",
        help="Output filename prefix",
    )

    parser.add_argument(
        "--gen-csv",
        default=False,
        action="store_true",
        help="Also generate CSV version of the result. By default, only NetCDF is generated.",
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

    return parser.parse_args()


def main(opts):
    set_logger(f"{opts.output_dir}/{opts.output_prefix}{opts.date}.log")

    file_helper = FileHelper(
        json_base_dir=opts.json_base_dir,
        audio_base_dir=opts.audio_base_dir,
        audio_path_map_prefix=opts.audio_path_map_prefix,
        audio_path_prefix=opts.audio_path_prefix,
    )

    processor_helper = ProcessHelper(
        file_helper,
        output_dir=opts.output_dir,
        output_prefix=opts.output_prefix,
        gen_csv=opts.gen_csv,
        gen_plot=opts.gen_plot,
        global_attrs_uri=opts.global_attrs,
        variable_attrs_uri=opts.var_attrs,
        voltage_multiplier=opts.voltage_multiplier,
        sensitivity_uri=opts.sensitivity_uri,
        sensitivity_flat_value=opts.sensitivity_flat_value,
        max_segments=opts.max_segments,
        subset_to=tuple(opts.subset_to) if opts.subset_to else None,
    )
    try:
        processor_helper.process_day(opts.date)
    except KeyboardInterrupt:
        info("INTERRUPTED")


if __name__ == "__main__":
    main(parse_arguments())
