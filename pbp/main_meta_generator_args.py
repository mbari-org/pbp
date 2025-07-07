from argparse import ArgumentParser, RawTextHelpFormatter

from pbp import get_pbp_version
from pbp.meta_gen.utils import InstrumentType


def parse_arguments():
    description = (
        "Generate JSONs with audio metadata for NRS flac files, "
        "IcListen wav files, and Soundtrap wav files from either a local directory or gs/s3 bucket."
    )
    example = """
Examples:
    pbp-meta-gen \\
                 --json-base-dir=tests/json/soundtrap \\
                 --output-dir=output \\
                 --uri=s3://pacific-sound-ch01 \\
                 --start=20230715 \\
                 --end=20230716 \\
                 --prefixes=7000 \\
                 --recorder=SOUNDTRAP
    """

    parser = ArgumentParser(
        description=description, epilog=example, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--version",
        action="version",
        version=get_pbp_version(),
    )

    parser.add_argument(
        "--recorder",
        choices=[
            InstrumentType.NRS,
            InstrumentType.ICLISTEN,
            InstrumentType.SOUNDTRAP,
            InstrumentType.RESEA,
        ],
        required=True,
        help="Choose the audio instrument type",
    )

    parser.add_argument(
        "--json-base-dir",
        type=str,
        metavar="dir",
        required=True,
        help="JSON base directory to store the metadata",
    )

    parser.add_argument(
        "--output-dir",
        type=str,
        metavar="dir",
        required=True,
        help="Output directory to store logs",
    )

    parser.add_argument(
        "--uri",
        type=str,
        metavar="uri",
        required=True,
        default=None,
        help="Location of the audio files. S3 location supported for IcListen or Soundtrap, and GS supported for NRS.",
    )

    parser.add_argument(
        "--start",
        type=str,
        required=True,
        metavar="YYYYMMDD",
        help="The starting date to be processed.",
    )

    parser.add_argument(
        "--end",
        type=str,
        required=True,
        metavar="YYYYMMDD",
        help="The ending date to be processed.",
    )

    parser.add_argument(
        "--prefix",
        type=str,
        required=True,
        nargs="+",
        help="Prefix for search to match the audio files e.g. 'MARS_' for MARS_YYYYMMDD_HHMMSS.wav, '7000. ' for "
        "7000.20220902.000000.wav",
    )

    parser.add_argument(
        "--xml-dir",
        type=str,
        metavar="dir",
        required=False,
        default=None,
        help="Specifies the directory where the log.xml files are located. If not specified, the default is the same directory as the audio files.",
    )

    return parser.parse_args()
