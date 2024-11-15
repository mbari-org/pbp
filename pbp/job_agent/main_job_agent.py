from pbp.main_hmb_generator_args import parse_arguments


def main():
    
    opts = parse_arguments()

    # pylint: disable=import-outside-toplevel
    from pbp.logging_helper import create_logger
    from pbp.job_agent.job_agent import JobAgent
    
    log = create_logger(
        log_filename_and_level=(
            f"{opts.orch_dir}/{opts.output_prefix}{opts.date}.log",
            "INFO",
        ),
        console_level="WARNING",
    )

    job_agent = JobAgent(
        recorder=opts.recorder,
        audio_base_dir=opts.audio_base_dir,
        json_base_dir=opts.json_base_dir,
        xml_dir=opts.xml_dir,
        start=opts.start,
        end=opts.end,
        prefix=opts.prefix,
        nc_output_dir=opts.output_dir,
        global_attrs_file=opts.global_attrs,
        variable_attrs_file=opts.variable_attrs,
        sensitivity_flat_value=opts.sensitivity_flat_value,
        latlon=opts.latlon,
        title=opts.title,
        cmlim=opts.cmlim,
        ylim=opts.ylim,
        log_dir = opts.log_dir)
    
    try:
        job_agent.run()
    except KeyboardInterrupt:
        log.info("INTERRUPTED")

if __name__ == "__main__":
    main()
