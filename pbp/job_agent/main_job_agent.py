from pbp.job_agent.main_job_agent_args import (
    parse_arguments,
)  # This module is used to parse the arguments provided by the user.
from multiprocessing import (
    Process,
)  # This module is used to create allow multiple processes.


def main():  # This function represents the entry point for the job agent.
    deployment_configurations = parse_arguments()  # This function call parses the arguments provided by the user and returns a list of dictionaries.

    from pbp.job_agent.job_agent import (
        JobAgent,
    )  # This module is used to create the job agent object.

    processes = []  # This list is used to store the processes created by the job agent.
    for deployment_configuration in (
        deployment_configurations
    ):  # Iterates through the deployment configurations provided by the user.
        
        if deployment_configuration["recorder"] == "SOUNDTRAP":  # Checks if the recorder is SOUNDTRAP.
            
            job_agent = JobAgent(
                output_prefix=deployment_configuration["output_prefix"],
                recorder=deployment_configuration["recorder"],
                audio_base_dir=deployment_configuration["audio_base_dir"],
                json_base_dir=deployment_configuration["json_base_dir"],
                start=deployment_configuration["start"],
                end=deployment_configuration["end"],
                prefix=deployment_configuration["prefix"],
                nc_output_dir=deployment_configuration["nc_output_dir"],
                global_attrs=deployment_configuration["global_attrs"],
                variable_attrs=deployment_configuration["variable_attrs"],
                latlon=deployment_configuration["latlon"],
                title=deployment_configuration["title"],
                cmlim=deployment_configuration["cmlim"],
                ylim=deployment_configuration["ylim"],
                log_dir=deployment_configuration["log_dir"],
                meta_output_dir=deployment_configuration["meta_output_dir"],
                xml_dir=deployment_configuration["xml_dir"],
                sensitivity_flat_value=deployment_configuration["sensitivity_flat_value"],
                sensitivity_uri=None,
                voltage_multiplier=None
            )
            
        if deployment_configuration["recorder"] == "NRS":
        
            job_agent = JobAgent(
                output_prefix=deployment_configuration["output_prefix"],
                recorder=deployment_configuration["recorder"],
                audio_base_dir=deployment_configuration["audio_base_dir"],
                json_base_dir=deployment_configuration["json_base_dir"],
                start=deployment_configuration["start"],
                end=deployment_configuration["end"],
                prefix=deployment_configuration["prefix"],
                nc_output_dir=deployment_configuration["nc_output_dir"],
                global_attrs=deployment_configuration["global_attrs"],
                variable_attrs=deployment_configuration["variable_attrs"],
                latlon=deployment_configuration["latlon"],
                title=deployment_configuration["title"],
                cmlim=deployment_configuration["cmlim"],
                ylim=deployment_configuration["ylim"],
                log_dir=deployment_configuration["log_dir"],
                meta_output_dir=deployment_configuration["meta_output_dir"],
                xml_dir=None,
                sensitivity_flat_value=None,
                sensitivity_uri=deployment_configuration["sensitivity_uri"],
                voltage_multiplier=deployment_configuration["voltage_multiplier"]
            )

        pbp_job_agent_process = Process(
            target=job_agent.run
        )  # Creates a process for the job agent.
        
        processes.append(
            pbp_job_agent_process
        )  # Appends the process to the list of processes.

    for process in processes:  # Iterates through the processes.
        process.start()  # Starts the process.

    for process in processes:  # Iterates through the processes.
        try:  # Tries to join the process.
            process.join()  # Joins the process.
        except KeyboardInterrupt as error:
            print(
                f"Operation was interrupted by the user: {error}"
            )  # Prints the error message.
            process.terminate()  # Terminates the process.


if __name__ == "__main__":
    main()
