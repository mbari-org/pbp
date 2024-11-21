from argparse import ArgumentParser, RawTextHelpFormatter
from pbp.meta_gen.utils import InstrumentType

from pbp import get_pbp_version
from pbp.job_agent.utils import yaml_to_json
from loguru import logger
import sys
import os


def parse_arguments():
    """This function processes the command-line arguments for the job agent.
    The primary argument is --config, which specifies the path to a YAML file
    containing the job agent's configuration. If multiple --config arguments
    are provided, the function launches multiple job agents concurrently, each
    running as a separate process rather than a thread. Ensure that your local
    machine can support the number of processes being created.

    Returns:
        _type_: _description_
    """

    description = "Deploys a job agent to process audio files. Each yaml file configuration argument spawns a new process."
    example = """
    Examples:
    pbp-job-agent --config /path/to/deployment/global_config_1.yaml /path/to/deployment/global_config_2.yaml
    
    Runs two job-job-agent process concurrently with the configurations provided in the yaml files.
    
    An Example YAML Content (For SoundTrap) ~ global_config_1.yaml:
    
    pbp_job_agent:
      output_prefix: Georges_Bank_2021
      recorder: "SOUNDTRAP"
      audio_base_dir: "/home/user/SOUNDTRAP_DEPLOYMENT/"
      json_base_dir: "/home/user/SOUNDTRAP_DEPLOYMENT/JSON"
      xml_dir: "/home/user/SOUNDTRAP_DEPLOYMENT"
      start: "20220521"
      end: "20220521"
      prefix: "6550"
      nc_output_dir: "/home/user/SOUNDTRAP_DEPLOYMENT/NC"
      global_attrs: "/path/to/deployment/global_config_1.yaml"
      variable_attrs: "/path/to/deployment/variable_config_1.yaml"
      sensitivity_flat_value: "176.6"
      latlon: "-31.711 115.583"
      title: "Georges_Bank_2021"
      cmlim: "36 107"
      ylim: "10 24000"
      meta_output_dir: "/home/user/SOUNDTRAP_DEPLOYMENT/META"
      voltage_multiplier: ""
      sensitivity_uri: ""
      log_dir: "/home/user/SOUNDTRAP_DEPLOYMENT/AGENT"
    """
    parser = ArgumentParser(
        description=description, epilog=example, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--config",
        type=str,
        metavar="path",
        nargs="+",
        required=True,
        help="path to the YAML file(s) that contain the configurations for the pbp-job-agent",
    )

    if (
        parser.parse_args().config is not None
    ):  # Checks if there is even a yaml file provided as an argument.
        for config_path in parser.parse_args().config:  # For each yaml argument.
            if not os.path.isfile(
                config_path
            ):  # If the yaml file does not exist despite being provided an argument.
                logger.error(
                    f"The config path {config_path} does not exist or is not a file."
                )  # Provide error message to logs/user
                exit(1)
        deployment_configurations = []  # A data structure to store the parsed yaml configurations.
        for (
            deployment_configuration
        ) in parser.parse_args().config:  # Iterates through the yaml files provided.
            if deployment_configuration is not None:  # TODO: This may be redundant
                yaml_data = yaml_to_json(
                    deployment_configuration
                )  # Convert the yaml file to a parsable object. This parsing is yaml based and distinct from the Argparse parsing.
                if (
                    yaml_data["pbp_job_agent"]["output_prefix"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'output_prefix' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)

                if (
                    yaml_data["pbp_job_agent"]["recorder"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'recorder' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)

                if (
                    yaml_data["pbp_job_agent"]["log_dir"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'log_dir' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)

                if (
                    yaml_data["pbp_job_agent"]["prefix"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'prefix' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)

                if (
                    yaml_data["pbp_job_agent"]["start"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'start' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["end"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'end' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["audio_base_dir"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'audio_base_dir' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["json_base_dir"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'json_base_dir' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["xml_dir"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'xml_dir' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["nc_output_dir"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'nc_output_dir' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["variable_attrs"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'variable_attrs' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["sensitivity_flat_value"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'sensitivity_flat_value' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["latlon"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'latlon' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["title"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'title' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["cmlim"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'cmlim' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["ylim"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'ylim' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["meta_output_dir"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'meta_output_dir' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)
                if (
                    yaml_data["pbp_job_agent"]["global_attrs"] is not None
                ):  # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error(
                        "The 'global_attrs' key-value pair in the --config YAML file(s) is necessary to run the job agent."
                    )
                    exit(1)

                deployment_configurations.append(
                    yaml_data["pbp_job_agent"]
                )  # Append the parsed yaml data to the deployment configurations list.

        return deployment_configurations  # Return the list of parsed yaml data.
