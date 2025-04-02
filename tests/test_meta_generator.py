# pypam-based-processing
# Filename: tests/test_json_generator.py
# Description:  Test fixtures for the json generator classes.
# Tests the ability to generate metadata for soundtrap, iclisten, and nrs recording files.


import boto3
from botocore import UNSIGNED
from botocore.client import Config
from datetime import datetime
from pathlib import Path
import json

from pbp.logging_helper import create_logger
from pbp.meta_gen.gen_nrs import NRSMetadataGenerator
from pbp.meta_gen.gen_soundtrap import SoundTrapMetadataGenerator
from pbp.meta_gen.gen_iclisten import IcListenMetadataGenerator
from pbp.meta_gen.utils import InstrumentType

# which is .gitignore'ed
OUT_BASE_DIR = Path("tests/json_generator_tmp")


def create_test_logger(name: str):
    log_dir = OUT_BASE_DIR / "log"
    log_dir.mkdir(exist_ok=True, parents=True)
    return create_logger(
        log_filename_and_level=(
            f"{log_dir}/{name}.log",
            "INFO",
        ),
        console_level="INFO",
    )


def create_json_dir(name: str) -> Path:
    json_dir = OUT_BASE_DIR / name
    if json_dir.exists():
        import shutil

        shutil.rmtree(json_dir)
    json_dir.mkdir(exist_ok=True, parents=True)
    return json_dir


def test_soundtrap_generator_s3():
    """
    Test fixture for SoundTrapMetadataGenerator.
    Tests the SoundTrapMetadataGenerator class ability to generate metadata for soundtrap recording files stored in S3.
    Two files should be generated in the json directory for the dates specified.
    :return:
    """
    log = create_test_logger("test_soundtrap_generator_s3")
    json_dir = create_json_dir("soundtrap_s3")

    start = datetime(2023, 7, 15)
    end = datetime(2023, 7, 16)
    gen = SoundTrapMetadataGenerator(
        log=log,
        uri="s3://pacific-sound-ch01",
        json_base_dir=json_dir.as_posix(),
        prefixes=["7000"],
        start=start,
        end=end,
    )
    gen.run()

    # There should be two files in the json directory - one for each day
    json_files = list(json_dir.rglob("*.json"))
    assert len(json_files) == 2
    assert (json_dir / "2023" / "20230715.json").exists()
    assert (json_dir / "2023" / "20230716.json").exists()

    # Each file should have 5 json objects
    for json_file in json_files:
        with open(json_file) as f:
            json_objects = json.load(f)
            assert len(json_objects) == 5

    # There should also be a coverage plot in the base json directory
    coverage_plot = (
        json_dir / f"{InstrumentType.SOUNDTRAP.lower()}_coverage_20230715_20230716.jpg"
    )
    assert coverage_plot.exists()


def test_soundtrap_generator_local():
    """
    Test fixture for SoundTrapMetadataGenerator.
    Tests the SoundTrapMetadataGenerator class ability to generate metadata for soundtrap recording files stored locally
    Two files should be generated in the json directory for the dates specified.
    :return:
    """
    log = create_test_logger("test_soundtrap_generator_local")
    json_dir = create_json_dir("soundtrap_local")

    wav_dir = Path(__file__).parent / "wav" / "soundtrap"
    wav_dir.mkdir(exist_ok=True, parents=True)

    # Fetch a file and its associated xml from the S3 bucket
    client = boto3.client("s3", config=Config(signature_version=UNSIGNED))
    client.download_file(
        "pacific-sound-ch01",
        "6716.221116080000.wav",
        (wav_dir / "6716.221116080000.wav").as_posix(),
    )
    client.download_file(
        "pacific-sound-ch01",
        "6716.221116080000.log.xml",
        (wav_dir / "6716.221116080000.log.xml").as_posix(),
    )

    start = datetime(2022, 11, 16)
    end = datetime(2022, 11, 16)
    gen = SoundTrapMetadataGenerator(
        log=log,
        uri=f"file://{wav_dir.as_posix()}",
        json_base_dir=json_dir.as_posix(),
        prefixes=["6716"],
        start=start,
        end=end,
    )
    gen.run()

    # There should be one file in the json directory - one for each day
    json_files = list(json_dir.rglob("*.json"))
    assert len(json_files) == 1
    assert (json_dir / "2022" / "20221116.json").exists()

    # The file should have 1 json object
    for json_file in json_files:
        with open(json_file) as f:
            json_objects = json.load(f)
            assert len(json_objects) == 1

    # There should also be a coverage plot in the base json directory
    coverage_plot = (
        json_dir / f"{InstrumentType.SOUNDTRAP.lower()}_coverage_20221116_20221116.jpg"
    )
    assert coverage_plot.exists()


def test_iclisten_generator():
    """
    Test fixture for IcListenMetadataGenerator.
    Tests the IcListenMetadataGenerator class ability to generate metadata for soundtrap recording files.
    One file should be generated in the json directory for the date specified. Note this currently
    only works for MBARI MARS ICListen data
    :return:
    """
    log = create_test_logger("test_iclisten_generator")
    json_dir = create_json_dir("mars")

    start = datetime(2023, 7, 18, 0, 0, 0)
    end = datetime(2023, 7, 18, 0, 0, 0)

    # If only running one day, use a single generator
    generator = IcListenMetadataGenerator(
        log=log,
        uri="s3://pacific-sound-256khz",
        json_base_dir=json_dir.as_posix(),
        prefixes=["MARS_"],
        start=start,
        end=end,
        seconds_per_file=600,
    )
    generator.run()
    # There should be one files in the json directory named 20230718.json and it should have 145 json objects
    json_files = list(json_dir.rglob("*.json"))
    assert len(json_files) == 1
    json_file = json_dir / "2023" / "20230718.json"
    assert json_file.exists()

    # Read the file and check the number of json objects
    with open(json_file) as f:
        json_objects = json.load(f)
        assert len(json_objects) == 145

    # There should also be a coverage plot in the base json directory
    coverage_plot = (
        json_dir / f"{InstrumentType.ICLISTEN.lower()}_coverage_20230718_20230718.jpg"
    )
    assert coverage_plot.exists()


def test_nrs_generator():
    """
    Test fixture for NRSMetadataGenerator.
    Tests the NRSMetadataGenerator class ability to generate metadata for NRS recording files.
    One files should be generated in the json directory for the date specified.
    :return:
    """
    log = create_test_logger("test_nrs_generator")
    json_dir = create_json_dir("nrs")

    start = datetime(2019, 10, 24, 0, 0, 0)
    end = datetime(2019, 10, 24, 0, 0, 0)

    generator = NRSMetadataGenerator(
        log=log,
        uri="gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio",
        json_base_dir=json_dir.as_posix(),
        prefixes=["NRS11_"],
        start=start,
        end=end,
        seconds_per_file=14400.0,
    )
    generator.run()
    # There should be one file in the json directory and with number of objects as indicated
    json_files = list(json_dir.rglob("*.json"))
    assert len(json_files) == 1
    json_file = json_dir / "2019" / "20191024.json"
    assert json_file.exists()

    # Read the file and check the number of json objects
    with open(json_file) as f:
        json_objects = json.load(f)
        assert len(json_objects) == 7

    # There should also be a coverage plot in the base json directory
    coverage_plot = (
        json_dir / f"{InstrumentType.NRS.lower()}_coverage_20191024_20191024.jpg"
    )
    assert coverage_plot.exists()


def test_datetime_support():
    """
    Test fixture for all audio file formats.
    Tests the ability to extract the datetime from the audio file name.
    :return:
    """
    filenames = [
        "s3://MARS_20191022_235758.wav",
        "gs://6550.221113155338.wav",
        "NRS11_20191023_222260.flac",  # Invalid seconds example
        "gs://6000.221011155338.wav",
        "MARS_20191022T235743Z.wav",
        "6000.230111155338.wav",
        "PacFLT_2_TM02_20130515_234500.d100.x.wav",
        "PacFLT_2_TM02_20130515_234500.d100.x.wav",
    ]
    prefixes = [
        "MARS_",
        "6550",
        "NRS11_",
        "6000",
        "MARS_",
        "6000",
        "PacFLT_2_TM02_",
        "PacFLT_2_TM02",
    ]
    expected = [
        datetime(2019, 10, 22, 23, 57, 58),
        datetime(2022, 11, 13, 15, 53, 38),
        datetime(2019, 10, 23, 22, 22, 59),
        datetime(2022, 10, 11, 15, 53, 38),
        datetime(2019, 10, 22, 23, 57, 43),
        datetime(2023, 1, 11, 15, 53, 38),
        datetime(2013, 5, 15, 23, 45, 0),
        datetime(2013, 5, 15, 23, 45, 0),
    ]
    from pbp.meta_gen.utils import get_datetime

    for i, filename in enumerate(filenames):
        assert get_datetime(filename, [prefixes[i]]) == expected[i]
