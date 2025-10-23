"""
Unified CLI entry point for mbari-pbp.

This provides a single entry point with subcommands for all pbp tools.
"""
import sys
import argparse
import multiprocessing
from typing import List, Optional

from pbp import get_pbp_version


def main(argv: Optional[List[str]] = None) -> int:
    """
    Main entry point with subcommands.
    """

    # Detect if running as a PyInstaller frozen executable
    # Reference: https://pyinstaller.org/en/stable/runtime-information.html
    is_frozen = getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")

    if argv is None:
        argv = sys.argv[1:]

    # Special handling for PyInstaller frozen executables only
    if is_frozen:
        # Required for multiprocessing in frozen applications (especially on Windows)
        multiprocessing.freeze_support()

        # When frozen with PyInstaller, multiprocessing may re-invoke this script
        # with internal commands like 'from multiprocessing.resource_tracker import main;main(10)'
        # These must be executed directly and not parsed by argparse
        if len(argv) > 0 and argv[0].startswith("from "):
            # This is a multiprocessing internal command, execute it directly
            code = " ".join(argv)
            exec(code)
            return 0

    parser = argparse.ArgumentParser(
        prog="pbp",
        description="PyPAM Based Processing for ocean passive acoustic monitoring",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pbp meta-gen --help         Show help for meta-gen command
  pbp hmb-gen --help          Show help for hmb-gen command
  pbp hmb-plot --help         Show help for hmb-plot command
  pbp cloud --help            Show help for cloud command

For more information, visit: https://docs.mbari.org/pbp/
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=get_pbp_version(),
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        required=True,
    )

    # Register subcommands

    subparsers.add_parser(
        "meta-gen",
        help="Generate JSON files with audio metadata",
        add_help=False,
    )

    subparsers.add_parser(
        "hmb-gen",
        help="Main HMB generation program",
        add_help=False,
    )

    subparsers.add_parser(
        "hmb-plot",
        help="Utility program to plot HMB product",
        add_help=False,
    )

    subparsers.add_parser(
        "cloud",
        help="Program for cloud based processing",
        add_help=False,
    )

    # Parse just the command, let subcommand handle its own args
    args, remaining = parser.parse_known_args(argv)

    # Set up sys.argv for the subcommand to parse
    # Subcommands expect sys.argv[0] to be the program name
    original_argv = sys.argv
    try:
        # Replace sys.argv with the subcommand and its arguments
        sys.argv = [f"pbp-{args.command}"] + remaining

        # Import and dispatch to the appropriate subcommand
        if args.command == "hmb-gen":
            from pbp.hmb_gen.main_hmb_generator import main as hmb_gen_main

            return hmb_gen_main()
        elif args.command == "cloud":
            from pbp.cloud.main_cloud import main as cloud_main

            return cloud_main()
        elif args.command == "hmb-plot":
            from pbp.hmb_plot.main_plot import main as plot_main

            return plot_main()
        elif args.command == "meta-gen":
            from pbp.meta_gen.main_meta_generator import main as meta_gen_main

            return meta_gen_main()
        else:
            parser.print_help()
            return 1
    finally:
        # Restore original sys.argv
        sys.argv = original_argv


if __name__ == "__main__":
    sys.exit(main())
