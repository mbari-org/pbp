from argparse import ArgumentParser, RawTextHelpFormatter
from pbp.meta_gen.utils import InstrumentType

from pbp import get_pbp_version
from pbp.job_agent.utils import yaml_to_json

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
        help="URI of JSON file with global attributes to be added to the NetCDF file.",
    )

    if parser.parse_args().global_attrs is not None: # Checks if there is even a yaml file provided.
        yaml_path =  parser.parse_args().global_attrs # The yaml_path is the path to the yaml file but it is not known yet if the value exists in the yaml.
        if yaml_path is not None: # If there is a yaml path is provided.
            yaml_data = yaml_to_json(yaml_path) # Convert the yaml file to a parsable object. This parsing is yaml based and distinct from the Argparse parsing.
            if yaml_data["pbp_job_agent"]["output_prefix"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--output_prefix",
                    choices=[InstrumentType.NRS, InstrumentType.ICLISTEN, InstrumentType.SOUNDTRAP],
                    required=False,
                    default=yaml_data["pbp_job_agent"]["output_prefix"],
                    help="Choose the audio instrument type",
                )
            else:
                parser.add_argument(
                    "--recorder",
                    choices=[InstrumentType.NRS, InstrumentType.ICLISTEN, InstrumentType.SOUNDTRAP],
                    required=True,
                    help="Choose the audio instrument type",
                )
            
            if yaml_data["pbp_job_agent"]["recorder"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--recorder",
                    choices=[InstrumentType.NRS, InstrumentType.ICLISTEN, InstrumentType.SOUNDTRAP],
                    required=False,
                    default=yaml_data["pbp_job_agent"]["recorder"],
                    help="Choose the audio instrument type",
                )
            else:
                parser.add_argument(
                    "--recorder",
                    choices=[InstrumentType.NRS, InstrumentType.ICLISTEN, InstrumentType.SOUNDTRAP],
                    required=True,
                    help="Choose the audio instrument type",
                )
                
            if yaml_data["pbp_job_agent"]["log_dir"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--log_dir",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["log_dir"],
                    help="The path where the job agent log file will be saved.",
                )
            else:
                parser.add_argument(
                    "--log_dir",
                    required=True,
                    help="The path where the job agent log file will be saved.",
                )
                
            if yaml_data["pbp_job_agent"]["prefix"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--prefix",
                    required=False,
                    metavar="prefix",
                    default=yaml_data["pbp_job_agent"]["prefix"],
                    help="The path where the job agent log file will be saved.",
                )
            else:
                parser.add_argument(
                    "--prefix",
                    required=True,
                    metavar="prefix",
                    help="The path where the job agent log file will be saved.",
                )
                
            if yaml_data["pbp_job_agent"]["start"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--start",
                    required=False,
                    metavar="start date",
                    default=yaml_data["pbp_job_agent"]["start"],
                    help="The desired starting date of the deployment period for processing.",
                )
            else:
                parser.add_argument(
                    "--start",
                    required=True,
                    metavar="start date",
                    help="The desired starting date of the deployment period for processing.",
                )
            if yaml_data["pbp_job_agent"]["end"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--end",
                    required=False,
                    metavar="start date",
                    default=yaml_data["pbp_job_agent"]["end"],
                    help="The desired starting date of the deployment period for processing.",
                )
            else:
                parser.add_argument(
                    "--end",
                    required=True,
                    metavar="start date",
                    help="The desired starting date of the deployment period for processing.",
                )
            if yaml_data["pbp_job_agent"]["audio_base_dir"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--audio_base_dir",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["audio_base_dir"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--audio_base_dir",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["json_base_dir"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--json_base_dir",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["json_base_dir"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--json_base_dir",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["xml_dir"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--xml_dir",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["xml_dir"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--xml_dir",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["nc_output_dir"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--nc_output_dir",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["nc_output_dir"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--nc_output_dir",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["variable_attrs"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--variable_attrs",
                    default=yaml_data["pbp_job_agent"]["variable_attrs"],
                    required=False,
                    help="",
                )
            else:
                parser.add_argument(
                    "--variable_attrs",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["sensitivity_flat_value"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--sensitivity_flat_value",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["sensitivity_flat_value"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--sensitivity_flat_value",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["latlon"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--latlon",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["latlon"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--latlon",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["title"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--title",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["title"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--title",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["cmlim"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--cmlim",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["cmlim"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--cmlim",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["ylim"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--ylim",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["ylim"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--ylim",
                    required=True,
                    help="",
                )
            if yaml_data["pbp_job_agent"]["meta_output_dir"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--meta_output_dir",
                    required=False,
                    default=yaml_data["pbp_job_agent"]["meta_output_dir"],
                    help="",
                )
            else:
                parser.add_argument(
                    "--meta_output_dir",
                    required=True,
                    help="",
                )


            
            


    parser.add_argument(
        "--version",
        action="version",
        version=get_pbp_version(),
    )
    
    



    return parser.parse_args()
