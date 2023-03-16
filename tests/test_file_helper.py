from urllib.parse import urlparse

from src.file_helper import get_bucket_key_simple


def test_get_bucket_key_simple():
    def check(uri: str, expected_bucket: str, expected_key: str, expected_simple: str):
        parsed_uri = urlparse(uri)
        assert parsed_uri.scheme == "s3"
        bucket, key, simple = get_bucket_key_simple(parsed_uri)
        assert bucket == expected_bucket
        assert key == expected_key
        assert simple == expected_simple

    check(
        "s3://pacific-sound-256khz-2022/09/MARS_20220901_235016.wav",
        "pacific-sound-256khz-2022",
        "09/MARS_20220901_235016.wav",
        "MARS_20220901_235016.wav",
    )

    check(
        "s3://bucket/key",
        "bucket",
        "key",
        "key",
    )

    check(
        "s3://bucket/",
        "bucket",
        "",
        "",
    )

    check(
        "s3://bucket",
        "bucket",
        "",
        "",
    )
