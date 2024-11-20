from pbp.job_agent.main_job_agent_args import parse_arguments
from multiprocessing import Process
def main():
    
    deployment_configurations = parse_arguments()

    from pbp.job_agent.job_agent import JobAgent
    processes = []
    for deployment_configuration in deployment_configurations:

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
            sensitivity_flat_value=deployment_configuration["sensitivity_flat_value"],
            latlon=deployment_configuration["latlon"],
            title=deployment_configuration["title"],
            cmlim=deployment_configuration["cmlim"],
            ylim=deployment_configuration["ylim"],
            log_dir=deployment_configuration["log_dir"],
            meta_output_dir=deployment_configuration["meta_output_dir"],
            xml_dir=deployment_configuration["xml_dir"]
        )
        
        
        pbp_job_agent_process = Process(target = job_agent.run)
        processes.append(pbp_job_agent_process)
        
    

    for process in processes:
        process.start()
            
    for process in processes:
        try:
            process.join()
        except KeyboardInterrupt as error:
            print(f"Operation was interrupted by the user: {error}")
            process.terminate()
            process.join()


if __name__ == "__main__":
    main()
