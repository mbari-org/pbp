from pbp.hmb_gen.simpleapi import HmbGen
from google.cloud.storage import Client as GsClient


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

    assert hmb_gen.check_parameters() is None


def test_multiprocessing_parameters():
    """Test that multiprocessing parameters can be set."""
    hmb_gen = HmbGen()
    
    # Test default values
    assert hmb_gen._use_multiprocessing is True
    assert hmb_gen._num_workers is None
    
    # Test setting values
    hmb_gen.set_use_multiprocessing(False)
    assert hmb_gen._use_multiprocessing is False
    
    hmb_gen.set_num_workers(4)
    assert hmb_gen._num_workers == 4


def test_required_parameters_are_missing(snapshot):
    assert HmbGen().check_parameters() == snapshot
