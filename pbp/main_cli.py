"""
Unified CLI entry point for mbari-pbp.

This provides a single entry point with subcommands for all pbp tools.
"""
import sys
import argparse
from typing import List, Optional


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point with subcommands."""
    parser = argparse.ArgumentParser(
        prog="pbp",
        description="PyPAM Based Processing - Audio data analysis tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  pbp hmb-gen --help          Show help for hmb-gen command
  pbp cloud --help            Show help for cloud command
  pbp hmb-plot --help         Show help for hmb-plot command
  pbp meta-gen --help         Show help for meta-gen command

For more information, visit: https://docs.mbari.org/pbp/
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s 1.8.2",
    )

    subparsers = parser.add_subparsers(
        title="commands",
        description="Available commands",
        dest="command",
        required=True,
    )

    # Register subcommands
    subparsers.add_parser(
        "hmb-gen",
        help="Main HMB generation program",
        add_help=False,
    )

    subparsers.add_parser(
        "cloud",
        help="Program for cloud based processing",
        add_help=False,
    )

    subparsers.add_parser(
        "hmb-plot",
        help="Utility program to plot HMB product",
        add_help=False,
    )

    subparsers.add_parser(
        "meta-gen",
        help="Generate JSON files with audio metadata",
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
