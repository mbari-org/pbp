from argparse import ArgumentParser, RawTextHelpFormatter
from pbp.meta_gen.utils import InstrumentType

from pbp import get_pbp_version
from pbp.job_agent.utils import yaml_to_json
from loguru import logger
import sys
import os

def parse_arguments():
    

    
    description = "Process ocean audio data archives to daily analysis products of hybrid millidecade spectra using PyPAM."
    example = """
    Examples:
    pbp_job_agent --json-base-dir=tests/json \\
        --audio-base-dir=tests/wav \\
        --date=20220902 \\
        --output-dir=output
    """
    parser = ArgumentParser(
        description=description, epilog=example, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--global-attrs",
        type=str,
        metavar="uri",
        default=None,
        nargs='+',
        required=True,
        help="URI of JSON file with global attributes to be added to the NetCDF file.",
    )

    if parser.parse_args().global_attrs is not None: # Checks if there is even a yaml file provided.
        
        for deployment_configuration in parser.parse_args().global_attrs: # Iterates through the yaml files provided.
            if deployment_configuration is not None: # If there is a yaml path is provided.
                yaml_data = yaml_to_json(deployment_configuration) # Convert the yaml file to a parsable object. This parsing is yaml based and distinct from the Argparse parsing.
                if yaml_data["pbp_job_agent"]["output_prefix"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'output_prefix' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                
                if yaml_data["pbp_job_agent"]["recorder"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'recorder' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                    
                if yaml_data["pbp_job_agent"]["log_dir"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'log_dir' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                    
                if yaml_data["pbp_job_agent"]["prefix"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'prefix' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                    
                if yaml_data["pbp_job_agent"]["start"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'start' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["end"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'end' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["audio_base_dir"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'audio_base_dir' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["json_base_dir"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'json_base_dir' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["xml_dir"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'xml_dir' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["nc_output_dir"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'nc_output_dir' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["variable_attrs"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'variable_attrs' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["sensitivity_flat_value"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'sensitivity_flat_value' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["latlon"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'latlon' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["title"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'title' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["cmlim"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'cmlim' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["ylim"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'ylim' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                if yaml_data["pbp_job_agent"]["meta_output_dir"] is not None: # If the yaml file has a recorder key present.
                    pass
                else:
                    logger.error("The 'meta_output_dir' key-value pair in the --global-attrs YAML file(s) is necessary to run the job agent.")
                    exit(1)
                    
            return yaml_data["pbp_job_agent"]
