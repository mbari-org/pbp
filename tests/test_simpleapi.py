from pbp.simpleapi import HmbGen
from google.cloud.storage import Client as GsClient
import pytest


def test_required_parameters_are_given():
    hmb_gen = HmbGen()
    hmb_gen.set_json_base_dir("/tmp/some_json_dir")
    hmb_gen.set_global_attrs_uri("s3://example.com/g.yml")
    hmb_gen.set_variable_attrs_uri("s3://example.com/v.yml")
    hmb_gen.set_sensitivity(3.5)
    hmb_gen.set_subset_to((20, 4000))
    hmb_gen.set_download_dir("/tmp/download")
    hmb_gen.set_output_dir("/tmp/output")
    hmb_gen.set_output_prefix("TEST_")
    hmb_gen.set_gs_client(GsClient.create_anonymous_client())

    hmb_gen.check_parameters()


def test_required_parameters_are_missing():
    with pytest.raises(ValueError):
        HmbGen().check_parameters()
