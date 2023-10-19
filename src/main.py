import logging
import os

import boto3

from src.main_args import parse_arguments

# Some imports, in particular involving data processing, cause a delay that is
# noticeable when just running the --help option. We get around this issue by
# postponing the imports until actually needed. See the main() function.


def main(opts):
    # pylint: disable=import-outside-toplevel
    from src.file_helper import FileHelper
    from src.logging_helper import create_logger
    from src.process_helper import ProcessHelper

    logger = create_logger(
        log_filename_and_level=(
            f"{opts.output_dir}/{opts.output_prefix}{opts.date}.log",
            logging.INFO,
        ),
        console_level=logging.INFO,
    )

    s3_client = None
    if opts.s3:
        kwargs = {}
        aws_region = os.getenv("AWS_REGION")
        if aws_region is not None:
            kwargs["region_name"] = aws_region

        s3_client = boto3.client("s3", **kwargs)

    file_helper = FileHelper(
        logger=logger,
        json_base_dir=opts.json_base_dir,
        audio_base_dir=opts.audio_base_dir,
        audio_path_map_prefix=opts.audio_path_map_prefix,
        audio_path_prefix=opts.audio_path_prefix,
        s3_client=s3_client,
        download_dir=opts.download_dir,
    )

    processor_helper = ProcessHelper(
        logger=logger,
        file_helper=file_helper,
        output_dir=opts.output_dir,
        output_prefix=opts.output_prefix,
        gen_csv=opts.gen_csv,
        global_attrs_uri=opts.global_attrs,
        variable_attrs_uri=opts.variable_attrs,
        voltage_multiplier=opts.voltage_multiplier,
        sensitivity_uri=opts.sensitivity_uri,
        sensitivity_flat_value=opts.sensitivity_flat_value,
        max_segments=opts.max_segments,
        subset_to=tuple(opts.subset_to) if opts.subset_to else None,
    )
    try:
        processor_helper.process_day(opts.date)
    except KeyboardInterrupt:
        logger.info("INTERRUPTED")


if __name__ == "__main__":
    main(parse_arguments())
