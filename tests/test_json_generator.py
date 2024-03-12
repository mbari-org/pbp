# pypam-based-processing
# Filename: tests/test_json_generator.py
# Description:  Test fixtures for the json generator classes.
# Tests the ability to generate metadata for soundtrap, iclisten, and nrs recording files.

import json

import boto3
import botocore
import pytest
from botocore.exceptions import ClientError
from datetime import datetime

import logging

from pathlib import Path

from src.json_generator.gen_nrs import NRSMetadataGenerator
from src.logging_helper import create_logger
from src.json_generator.gen_soundtrap import SoundTrapMetadataGenerator
from src.json_generator.gen_iclisten import IcListenMetadataGenerator


def get_aws_account() -> str:
    """
    Get the account number associated with this user
    :return:
    """
    try:
        account_number = boto3.client("sts").get_caller_identity()["Account"]
        print(f"Found account {account_number}")
        return account_number
    except ClientError as e:
        print(e)
        msg = (
            f"Could not get account number from AWS. Check your config.ini file. "
            f"Account number is not set in the config.ini file and AWS credentials are not configured."
        )
        print(msg)
        return None
    except botocore.exceptions.NoCredentialsError as e:
        print(e)
        return None


# Check if an AWS account is configured by checking if it can access the model with the default credentials
AWS_AVAILABLE = False
if get_aws_account():
    AWS_AVAILABLE = True


@pytest.mark.skipif(
    not AWS_AVAILABLE,
    reason="This test is excluded because it requires a valid AWS account",
)
def test_soundtrap_json_generator():
    """
    Test fixture for SoundTrapMetadataGenerator.
    Tests the SoundTrapMetadataGenerator class ability to generate metadata for soundtrap recording files.
    Two files should be generated in the json directory for the dates specified.
    :return:
    """
    log_dir = Path("tests/log")
    json_dir = Path("tests/json/soundtrap")
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    logger = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_soundtrap_metadata_generator.log",
            logging.INFO,
        ),
        console_level=logging.INFO,
    )

    start = datetime(2023, 7, 18)
    end = datetime(2023, 7, 19)
    gen = SoundTrapMetadataGenerator(
        pbp_logger=logger,
        uri="s3://pacific-sound-ch01",
        json_base_dir=json_dir.as_posix(),
        prefix=["7000"],
        start=start,
        end=end,
    )
    gen.run()

    # There should be two files in the json directory named 20230718.json and 20230719.json
    json_files = list(Path("tests/json/soundtrap").rglob("*.json"))
    assert len(json_files) == 2
    assert Path("tests/json/soundtrap/2023/20230718.json").exists()
    assert Path("tests/json/soundtrap/2023/20230719.json").exists()


@pytest.mark.skipif(
    not AWS_AVAILABLE,
    reason="This test is excluded because it requires a valid AWS account",
)
def test_iclisten_json_generator():
    """
    Test fixture for IcListenMetadataGenerator.
    Tests the IcListenMetadataGenerator class ability to generate metadata for soundtrap recording files.
    One file should be generated in the json directory for the date specified. Note this currently
    only works for MBARI MARS ICListen data
    :return:
    """

    log_dir = Path("tests/log")
    json_dir = Path("tests/json/mars")
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    logger = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_mars_metadata_generator.log",
            logging.INFO,
        ),
        console_level=logging.INFO,
    )

    start = datetime(2023, 7, 18, 0, 0, 0)
    end = datetime(2023, 7, 18, 0, 0, 0)

    # If only running one day, use a single generator
    generator = IcListenMetadataGenerator(
        pbp_logger=logger,
        uri="s3://pacific-sound-256khz",
        json_base_dir=json_dir.as_posix(),
        prefix=["MARS"],
        start=start,
        end=end,
        seconds_per_file=300,
    )
    generator.run()
    # There should be one files in the json directory named 20230718.json and it should have 145 json objects
    json_files = list(Path("tests/json/mars/").rglob("*.json"))
    assert len(json_files) == 1
    assert Path("tests/json/mars/2023/20230718.json").exists()

    # Read the file and check the number of json objects
    with open("tests/json/mars/2023/20230718.json") as f:
        json_objcts = json.load(f)
        if len(json_objcts) != 145:
            assert False


def test_nrs_json_generator():
    """
    Test fixture for NRSMetadataGenerator.
    Tests the NRSMetadataGenerator class ability to generate metadata for NRS recording files.
    One files should be generated in the json directory for the date specified.
    :return:
    """
    log_dir = Path("tests/log")
    json_dir = Path("tests/json/nrs")
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)

    logger = create_logger(
        log_filename_and_level=(
            f"{log_dir}/test_nrs_metadata_generator.log",
            logging.INFO,
        ),
        console_level=logging.INFO,
    )

    start = datetime(2019, 10, 24, 0, 0, 0)
    end = datetime(2019, 10, 24, 0, 0, 0)

    generator = NRSMetadataGenerator(
        pbp_logger=logger,
        uri="gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio",
        json_base_dir=json_dir.as_posix(),
        prefix=["NRS11"],
        start=start,
        end=end,
        seconds_per_file=14400.0,
    )
    generator.run()
    # There should be one files in the json directory named 20230718.json, and it should have 7 json objects
    json_files = list(Path("tests/json/nrs/").rglob("*.json"))
    assert len(json_files) == 1
    assert Path("tests/json/nrs/2019/20191024.json").exists()

    # Read the file and check the number of json objects
    with open("tests/json/nrs/2019/20191024.json") as f:
        json_objcts = json.load(f)
        if len(json_objcts) != 7:
            assert False
