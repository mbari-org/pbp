#!/usr/bin/env python

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
#  GEN_PLOT: (Optional)
#     Set this to 'y' to also generate plot file.
#
# *Note*:
#   TODO retrieve sensitivity information using PyHydrophone when none
#     of the `SENSITIVITY_*` environment variables above are given.
#
# Mainly for testing purposes, also these environment variables are inspected:
#  CLOUD_TMP_DIR: (Optional)
#     Local workspace for downloads and for generated files to be uploaded.
#     By default, "cloud_tmp".
#  MAX_SEGMENTS: (Optional)
#     0, the default, means no restriction, that is, all segments for each day
#     will be processed.
#  REMOVE_DOWNLOADED_FILES: (Optional)
#     "yes", the default, means that any downloaded files for a day
#     will be removed after processing.

import os
import pathlib

import boto3

from src.file_helper import FileHelper
from src.misc_helper import info, set_logger, warn
from src.process_helper import ProcessHelper


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

    gen_plot = "y" == os.getenv("GEN_PLOT")

    # Convenience for testing (0 means no restriction)
    max_segments = int(os.getenv("MAX_SEGMENTS", "0"))

    # workspace for downloads and generated files to be uploaded
    cloud_tmp_dir = os.getenv("CLOUD_TMP_DIR", "cloud_tmp")

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
            info(f"Creating bucket {output_bucket}")
            s3_client.create_bucket(
                Bucket=output_bucket,
                CreateBucketConfiguration={"LocationConstraint": aws_region},
            )

    else:
        info("No output bucket specified. Output will not be uploaded.")

    # --------------------------
    # Get working:

    download_dir = f"{cloud_tmp_dir}/downloads"
    pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)

    generated_dir = f"{cloud_tmp_dir}/generated"
    pathlib.Path(generated_dir).mkdir(parents=True, exist_ok=True)

    log_filename = f"{generated_dir}/{output_prefix}{date}.log"
    set_logger(log_filename)

    file_helper = FileHelper(
        json_base_dir=json_bucket_prefix,
        s3_client=s3_client,
        download_dir=download_dir,
    )

    processor_helper = ProcessHelper(
        file_helper,
        output_dir=generated_dir,
        output_prefix=output_prefix,
        gen_csv=False,
        gen_plot=gen_plot,
        global_attrs_uri=global_attrs_uri,
        variable_attrs_uri=variable_attrs_uri,
        voltage_multiplier=voltage_multiplier,
        sensitivity_uri=sensitivity_uri,
        sensitivity_flat_value=sensitivity_flat_value,
        max_segments=max_segments,
        subset_to=(10, 100_000),  # TODO allow indicating this.
    )

    nc_filename = processor_helper.process_day(date)

    if nc_filename is None:
        warn(f"No NetDF file was generated.  ({date=})")
        return

    if output_bucket is not None:

        def upload(filename):
            info(f"Uploading {filename} to {output_bucket}")
            filename_out = pathlib.Path(filename).name
            ok = s3_client.upload_file(filename, output_bucket, filename_out)
            info(f"Upload result: {ok}")

        upload(log_filename)
        upload(nc_filename)

    else:
        info("No uploads attempted as output bucket was not given.")


if __name__ == "__main__":
    main()
