#!/usr/bin/env python
import os
import pathlib

import boto3

from src.file_helper import FileHelper
from src.misc_helper import set_logger
from src.process_helper import ProcessHelper


def main():
    # --------------------------
    # Cloud preparations:

    # The date to process. Format: "YYYYMMDD"
    date = os.environ["DATE"]
    assert date.isdigit() and len(date) == 8
    year, month, day = int(date[:4]), int(date[4:6]), int(date[6:8])

    # Bucket prefix to be used to locate the YYYYMMDD.json file
    json_bucket_prefix = os.getenv(
        "S3_JSON_BUCKET_PREFIX", "s3://pacific-sound-metadata/256khz"
    )

    # The bucket to write the output to
    output_bucket = os.getenv("S3_OUTPUT_BUCKET")

    # Convenience for testing (0 means no restriction)
    max_segments = int(os.getenv("MAX_SEGMENTS", "0"))

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
            print(f"Creating bucket {output_bucket}")
            s3_client.create_bucket(
                Bucket=output_bucket,
                CreateBucketConfiguration={"LocationConstraint": aws_region},
            )

    # --------------------------
    # Get working:

    # workspace for downloads and generated files to be uploaded
    cloud_tmp_dir = "cloud_tmp"

    download_dir = f"{cloud_tmp_dir}/downloads"
    pathlib.Path(download_dir).mkdir(parents=True, exist_ok=True)

    generated_dir = f"{cloud_tmp_dir}/generated"
    pathlib.Path(generated_dir).mkdir(parents=True, exist_ok=True)

    log_filename = set_logger(generated_dir, year, month, day)

    file_helper = FileHelper(
        json_base_dir=json_bucket_prefix,
        s3_client=s3_client,
        download_dir=download_dir,
    )

    processor_helper = ProcessHelper(
        file_helper,
        output_dir=generated_dir,
        gen_csv=False,
        max_segments=max_segments,
    )

    nc_filename = processor_helper.process_day(
        year=year,
        month=month,
        day=day,
    )

    if nc_filename is None:
        print("No NetDF file was generated.")
        return

    if output_bucket is not None:

        def upload(filename):
            print(f"Uploading {filename} to {output_bucket}")
            ok = s3_client.upload_file(filename, output_bucket)
            print(f"Upload result: {ok}")

        upload(log_filename)
        upload(nc_filename)


if __name__ == "__main__":
    main()
