from pbp.main_args import parse_arguments

# Some imports, in particular involving data processing, cause a delay that is
# noticeable when just running the --help option. We get around this issue by
# postponing the imports until actually needed. See the main() function.


def main():
    opts = parse_arguments()

    # pylint: disable=import-outside-toplevel
    import os

    from pbp.file_helper import FileHelper
    from pbp.logging_helper import create_logger
    from pbp.process_helper import ProcessHelper

    log = create_logger(
        log_filename_and_level=(
            f"{opts.output_dir}/{opts.output_prefix}{opts.date}.log",
            "INFO",
        ),
        console_level="WARNING",
    )

    s3_client = None
    if opts.s3:
        # pylint: disable=import-outside-toplevel
        import boto3

        kwargs = {}
        aws_region = os.getenv("AWS_REGION")
        if aws_region is not None:
            kwargs["region_name"] = aws_region

        s3_client = boto3.client("s3", **kwargs)

    gs_client = None
    if opts.gs:
        # pylint: disable=import-outside-toplevel
        from google.cloud.storage import Client as GsClient

        # TODO credentials; for now assuming only anonymous downloads
        gs_client = GsClient.create_anonymous_client()

    file_helper = FileHelper(
        log=log,
        json_base_dir=opts.json_base_dir,
        audio_base_dir=opts.audio_base_dir,
        audio_path_map_prefix=opts.audio_path_map_prefix,
        audio_path_prefix=opts.audio_path_prefix,
        s3_client=s3_client,
        gs_client=gs_client,
        download_dir=opts.download_dir,
        assume_downloaded_files=opts.assume_downloaded_files,
        retain_downloaded_files=opts.retain_downloaded_files,
    )

    process_helper = ProcessHelper(
        log=log,
        file_helper=file_helper,
        output_dir=opts.output_dir,
        output_prefix=opts.output_prefix,
        global_attrs_uri=opts.global_attrs,
        set_global_attrs=opts.set_global_attrs,
        variable_attrs_uri=opts.variable_attrs,
        voltage_multiplier=opts.voltage_multiplier,
        sensitivity_uri=opts.sensitivity_uri,
        sensitivity_flat_value=opts.sensitivity_flat_value,
        max_segments=opts.max_segments,
        subset_to=tuple(opts.subset_to) if opts.subset_to else None,
    )
    try:
        process_helper.process_day(opts.date)
    except KeyboardInterrupt:
        log.info("INTERRUPTED")


if __name__ == "__main__":
    main()
