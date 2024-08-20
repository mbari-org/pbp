#!/usr/bin/env python

#
# TODO Adjustments for GS as this script is still only focused on S3.
#

# Script for cloud based processing. By this, we basically mean the ability
# to get input files (json and wav) from S3 and write output files to S3.
#
# Inputs to the program are to be passed via environment variables:
#  DATE: (Required)
#     The date to process. Format: "YYYYMMDD".
#  S3_JSON_BUCKET_PREFIX: (Optional)
#     Bucket prefix to be used to locate the YYYYMMDD.json file
#     By default, "s3://pacific-sound-metadata/256khz".
#  S3_OUTPUT_BUCKET: (Optional)
#     The bucket to write the generated output to.
#     Typically this is to be provided but it is optional to facilitate testing.
#  OUTPUT_PREFIX: (Optional)
#     Output filename prefix. By default, "milli_psd_".
#     The resulting file will be named as <OUTPUT_PREFIX><DATE>.nc.
#  GLOBAL_ATTRS_URI: (Optional)
#     URI of JSON file with global attributes to be added to the NetCDF file.
#  VARIABLE_ATTRS_URI: (Optional)
#     URI of JSON file with attributes to associate to the variables in the NetCDF file.
#  VOLTAGE_MULTIPLIER: (Optional)
#     Applied on the loaded signal.
#  SENSITIVITY_NETCDF_URI: (Optional)
#     URI of sensitivity NetCDF file that should be used to calibrate the result.
#  SENSITIVITY_FLAT_VALUE: (Optional)
#     Flat sensitivity value to be used for calibration
#     if SENSITIVITY_NETCDF_URI is not given.
#  SUBSET_TO: (Required)  Format: "lower,upper"
#     Subset the resulting PSD to [lower, upper), in terms of central frequency.
#
# *Note*:
#   TODO retrieve sensitivity information using PyHydrophone when none
#     of the `SENSITIVITY_*` environment variables above are given.
#
# Mainly for testing purposes, also these environment variables are inspected:
#
#  CLOUD_TMP_DIR: (Optional)
#     Local workspace for downloads and for generated files to be uploaded.
#     By default, "cloud_tmp".
#
#  MAX_SEGMENTS: (Optional)
#     0, the default, means no restriction, that is, all segments for each day
#     will be processed.
#
#  ASSUME_DOWNLOADED_FILES: (Optional)
#     If "yes", then if any destination file for a download exists,
#     it is assumed downloaded already.
#     The default is that downloads are always performed.
#
#  RETAIN_DOWNLOADED_FILES: (Optional)
#     If "yes", do not remove any downloaded files after use.
#     The default is that any downloaded file is removed after use.

import os
import pathlib

import boto3

from pbp.file_helper import FileHelper
from pbp.logging_helper import create_logger
from pbp.process_helper import ProcessHelper


def main():
    # --------------------------
    # Cloud preparations:

    # The date to process. Format: "YYYYMMDD"
    date = os.environ["DATE"]

    # Bucket prefix to be used to locate the YYYYMMDD.json file
    json_bucket_prefix = os.getenv(
        "S3_JSON_BUCKET_PREFIX", "s3://pacific-sound-metadata/256khz"
    )

    output_prefix = os.getenv("OUTPUT_PREFIX", "milli_psd_")

    # The bucket to write the output to
    output_bucket = os.getenv("S3_OUTPUT_BUCKET")

    # Applied on the loaded signal
    voltage_multiplier = (
        float(os.getenv("VOLTAGE_MULTIPLIER"))
        if os.getenv("VOLTAGE_MULTIPLIER") is not None
        else None
    )

    global_attrs_uri = os.getenv("GLOBAL_ATTRS_URI")
    variable_attrs_uri = os.getenv("VARIABLE_ATTRS_URI")

    # URI of sensitivity NetCDF file to be used for calibration
    sensitivity_uri = os.getenv("SENSITIVITY_NETCDF_URI")

    # Flat sensitivity value to be used for calibration
    sensitivity_flat_value = (
        float(os.getenv("SENSITIVITY_FLAT_VALUE"))
        if os.getenv("SENSITIVITY_FLAT_VALUE") is not None
        else None
    )

    subset_to_string = os.environ["SUBSET_TO"]
    subset_to = tuple(int(val.strip()) for val in subset_to_string.split(","))
    assert len(subset_to) == 2

    # Convenience for testing (0 means no restriction)
    max_segments = int(os.getenv("MAX_SEGMENTS", "0"))

    # workspace for downloads and generated files to be uploaded
    cloud_tmp_dir = os.getenv("CLOUD_TMP_DIR", "cloud_tmp")

    download_dir = f"{cloud_tmp_dir}/downloads"
    pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)

    generated_dir = f"{cloud_tmp_dir}/generated"
    pathlib.Path(generated_dir).mkdir(parents=True, exist_ok=True)

    log_filename = f"{generated_dir}/{output_prefix}{date}.log"
    log = create_logger(
        log_filename_and_level=(log_filename, "INFO"),
        console_level="DEBUG",
    )

    kwargs = {}
    aws_region = os.getenv("AWS_REGION")
    if aws_region is not None:
        kwargs["region_name"] = aws_region

    s3_client = boto3.client("s3", **kwargs)

    if output_bucket is not None:
        # create output_bucket if it does not exist
        found = any(
            b["Name"] == output_bucket for b in s3_client.list_buckets()["Buckets"]
        )
        if not found:
            log.info(f"Creating bucket {output_bucket}")
            s3_client.create_bucket(
                Bucket=output_bucket,
                CreateBucketConfiguration={"LocationConstraint": aws_region},
            )

    else:
        log.info("No output bucket specified. Output will not be uploaded.")

    # --------------------------
    # Get working:

    file_helper = FileHelper(
        json_base_dir=json_bucket_prefix,
        s3_client=s3_client,
        gs_client=None,  # TODO
        download_dir=download_dir,
        assume_downloaded_files=os.getenv("ASSUME_DOWNLOADED_FILES", "no") == "yes",
        retain_downloaded_files=os.getenv("RETAIN_DOWNLOADED_FILES", "no") == "yes",
    )

    process_helper = ProcessHelper(
        file_helper=file_helper,
        output_dir=generated_dir,
        output_prefix=output_prefix,
        global_attrs_uri=global_attrs_uri,
        variable_attrs_uri=variable_attrs_uri,
        voltage_multiplier=voltage_multiplier,
        sensitivity_uri=sensitivity_uri,
        sensitivity_flat_value=sensitivity_flat_value,
        max_segments=max_segments,
        subset_to=subset_to,
    )

    result = process_helper.process_day(date)

    if result is None:
        log.warning(f"No NetDF file was generated.  ({date=})")
        return

    log.info(f"Generated files: {result.generated_filenames}")

    if output_bucket is not None:

        def upload(filename):
            log.info(f"Uploading {filename} to {output_bucket}")
            filename_out = pathlib.Path(filename).name
            ok = s3_client.upload_file(filename, output_bucket, filename_out)
            log.info(f"Upload result: {ok}")

        for generated_filename in result.generated_filenames:
            upload(generated_filename)

        # result of uploading the log itself won't of course show up there
        upload(log_filename)

    else:
        log.info("No uploads attempted as output bucket was not given.")


if __name__ == "__main__":
    main()
