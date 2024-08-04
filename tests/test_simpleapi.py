from pbp.simpleapi import Pbp
from google.cloud.storage import Client as GsClient
import pytest


def test_required_parameters_are_given():
    pbp = Pbp()
    pbp.set_json_base_dir("/tmp/some_json_dir")
    pbp.set_global_attrs_uri("s3://example.com/g.yml")
    pbp.set_variable_attrs_uri("s3://example.com/v.yml")
    pbp.set_sensitivity(3.5)
    pbp.set_subset_to((20, 4000))
    pbp.set_download_dir("/tmp/download")
    pbp.set_output_dir("/tmp/output")
    pbp.set_output_prefix("TEST_")
    pbp.set_gs_client(GsClient.create_anonymous_client())

    pbp.check_parameters()


def test_required_parameters_are_missing():
    with pytest.raises(ValueError):
        Pbp().check_parameters()
