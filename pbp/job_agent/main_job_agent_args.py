from argparse import ArgumentParser, RawTextHelpFormatter
from pbp.meta_gen.utils import InstrumentType

from pbp import get_pbp_version
from pbp.job_agent.utils import yaml_to_json

def parse_arguments():
    description = "Process ocean audio data archives to daily analysis products of hybrid millidecade spectra using PyPAM."
    example = """
    Examples:
    pbp-job-agent --json-base-dir=tests/json \\
        --audio-base-dir=tests/wav \\
        --date=20220902 \\
        --output-dir=output
    """

    parser = ArgumentParser(
        description=description, epilog=example, formatter_class=RawTextHelpFormatter
    )

    parser.add_argument(
        "--set-global-attr",
        type=str,
        nargs=2,
        default=None,
        metavar=("key", "value"),
        dest="set_global_attrs",
        action="append",
        help="Replace {{key}} with the given value for every occurrence of {{key}}"
        " in the global attrs file.",
    )
    

    if len(parser.parse_args()) > 0: # Checks if there is even a yaml file provided.
        yaml_path =  parser.parse_args().variable_attrs # The yaml_path is the path to the yaml file but it is not known yet if the value exists in the yaml.
        if yaml_path is not None: # If there is a yaml path is provided.
            print("Variable attributes file is provided")
            yaml_data = yaml_to_json(yaml_path) # Convert the yaml file to a parsable object. This parsing is yaml based and distinct from the Argparse parsing.
            if yaml_data["pbp-meta-gen"]["recorder"] is not None: # If the yaml file has a recorder key present.
                parser.add_argument(
                    "--recorder",
                    choices=[InstrumentType.NRS, InstrumentType.ICLISTEN, InstrumentType.SOUNDTRAP],
                    required=False,
                    help="Choose the audio instrument type",
                )
            else:
                parser.add_argument(
                    "--recorder",
                    choices=[InstrumentType.NRS, InstrumentType.ICLISTEN, InstrumentType.SOUNDTRAP],
                    required=True,
                    help="Choose the audio instrument type",
                )
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass
            if yaml_data[""][""] is not None:
                pass

    parser.add_argument(
        "--version",
        action="version",
        version=get_pbp_version(),
    )
    
    



    return parser.parse_args()
