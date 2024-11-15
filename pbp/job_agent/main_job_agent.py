from pbp.job_agent.main_job_agent_args import parse_arguments


def main():
    opts = parse_arguments()

    # pylint: disable=import-outside-toplevel
    from pbp.logging_helper import create_logger
    from pbp.job_agent.job_agent import JobAgent
    
    log = create_logger(
        log_filename_and_level=(
            f"{opts.log_dir}/{opts.prefix}{opts.start}_{opts.end}.log",
            "INFO",
        ),
        console_level="WARNING",
    )

    job_agent = JobAgent(
        recorder=opts.recorder,
        audio_base_dir=opts.audio_base_dir,
        json_base_dir=opts.json_base_dir,
        start=opts.start,
        end=opts.end,
        prefix=opts.prefix,
        nc_output_dir=opts.nc_output_dir,
        global_attrs=opts.global_attrs,
        variable_attrs=opts.variable_attrs,
        sensitivity_flat_value=opts.sensitivity_flat_value,
        latlon=opts.latlon,
        title=opts.title,
        cmlim=opts.cmlim,
        ylim=opts.ylim,
        log_dir = opts.log_dir,
        meta_output_dir = opts.meta_output_dir,
        xml_dir = opts.xml_dir)
    
    try:
        job_agent.run()
    except KeyboardInterrupt:
        log.info("INTERRUPTED")

if __name__ == "__main__":
    main()
