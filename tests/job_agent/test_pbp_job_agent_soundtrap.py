import os


def pbp_job_agent():
    repo_root = os.path.dirname(os.path.abspath(__file__))
    print(repo_root)
    config_yaml_path = os.path.join(
        repo_root, "yaml/soundtrap/test_deployment_global_attributes.yaml"
    )
    os.system("pbp-job-agent --config " + config_yaml_path)


def test_pbp_job_agent():
    pbp_job_agent()

    netcdf_exists = os.path.exists(
        "/home/mryan/Documents/GitHub/pbp/tests/job_agent/test_output/nc/"
    )
    pbp_hmb_gen_logs_exist = os.path.exists(
        "/home/mryan/Documents/GitHub/pbp/tests/job_agent/test_output/pbp_hmb_logs/"
    )
    json_exists = os.path.exists(
        "/home/mryan/Documents/GitHub/pbp/tests/metadata/soundtrap/2021-09-01T00:00:00Z.yaml"
    )
    pbp_meta_gen_logs_exists = os.path.exists(
        "/home/mryan/Documents/GitHub/pbp/tests/metadata/soundtrap/2021-09-01T00:00:00Z.log"
    )
    plot_exists = os.path.exists(
        "/home/mryan/Documents/GitHub/pbp/tests/plots/soundtrap/2021-09-01T00:00:00Z.png"
    )
    job_agent_logs_exists = os.path.exists(
        "/home/mryan/Documents/GitHub/pbp/tests/pbp-job-agent/soundtrap/2021-09-01T00:00:00Z.log"
    )

    assert pbp_hmb_gen_logs_exist == True
    assert json_exists == True
    assert pbp_meta_gen_logs_exists == True
    assert netcdf_exists == True
    assert plot_exists == True
    assert job_agent_logs_exists == True
