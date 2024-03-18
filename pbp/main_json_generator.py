from datetime import datetime
from pathlib import Path

from pbp.json_generator.gen_nrs import NRSMetadataGenerator
from pbp.json_generator.gen_iclisten import IcListenMetadataGenerator
from pbp.json_generator.gen_soundtrap import SoundTrapMetadataGenerator
from pbp.main_json_generator_args import parse_arguments

# Some imports, in particular involving data processing, cause a delay that is
# noticeable when just running the --help option. We get around this issue by
# postponing the imports until actually needed. See the main() function.


def main(opts):
    # pylint: disable=import-outside-toplevel
    import logging
    from pbp.logging_helper import create_logger

    logger = create_logger(
        log_filename_and_level=(
            f"{opts.output_dir}/{opts.recorder}{opts.start}_{opts.end}.log",
            logging.INFO,
        ),
        console_level=logging.INFO,
    )

    log_dir = Path(opts.output_dir)
    json_dir = Path(opts.json_base_dir)
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)
    start = datetime.strptime(opts.start, "%Y%m%d")
    end = datetime.strptime(opts.end, "%Y%m%d")

    try:
        if opts.recorder == "NRS":
            generator = NRSMetadataGenerator(
                pbp_logger=logger,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefix=opts.prefix,
                start=start,
                end=end,
            )
            generator.run()
        if opts.recorder == "ICLISTEN":
            generator = IcListenMetadataGenerator(
                pbp_logger=logger,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefix=opts.prefix,
                start=start,
                end=end,
            )
            generator.run()
            # TODO: add multiprocessing here for speed-up
        if opts.recorder == "SOUNDTRAP":
            generator = SoundTrapMetadataGenerator(
                pbp_logger=logger,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefix=opts.prefix,
                start=start,
                end=end,
            )
            generator.run()
    except KeyboardInterrupt:
        logger.info("INTERRUPTED")


if __name__ == "__main__":
    main(parse_arguments())
