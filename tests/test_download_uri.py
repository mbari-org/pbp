from urllib.parse import urlparse

from pbp.download_uri import get_bucket_key_simple


def test_get_bucket_key_simple():
    def check(
        uri: str,
        expected_scheme: str,
        expected_bucket: str,
        expected_key: str,
        expected_simple: str,
    ):
        parsed_uri = urlparse(uri)
        assert parsed_uri.scheme == expected_scheme
        bucket, key, simple = get_bucket_key_simple(parsed_uri)
        assert bucket == expected_bucket
        assert key == expected_key
        assert simple == expected_simple

    check(
        "gs://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio/NRS11_20191231_230836.flac",
        "gs",
        "noaa-passive-bioacoustic",
        "nrs/audio/11/nrs_11_2019-2021/audio/NRS11_20191231_230836.flac",
        "NRS11_20191231_230836.flac",
    )

    check(
        "gcp://noaa-passive-bioacoustic/nrs/audio/11/nrs_11_2019-2021/audio//NRS11_20200811_015443.flac",
        "gcp",
        "noaa-passive-bioacoustic",
        "nrs/audio/11/nrs_11_2019-2021/audio//NRS11_20200811_015443.flac",
        "NRS11_20200811_015443.flac",
    )

    check(
        "s3://pacific-sound-256khz-2022/09/MARS_20220901_235016.wav",
        "s3",
        "pacific-sound-256khz-2022",
        "09/MARS_20220901_235016.wav",
        "MARS_20220901_235016.wav",
    )

    check(
        "s3://bucket/key",
        "s3",
        "bucket",
        "key",
        "key",
    )

    check(
        "s3://bucket/",
        "s3",
        "bucket",
        "",
        "",
    )

    check(
        "s3://bucket",
        "s3",
        "bucket",
        "",
        "",
    )
