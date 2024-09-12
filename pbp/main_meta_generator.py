import os
from datetime import datetime
from pathlib import Path
import loguru
import sys
import copy

from pbp.meta_gen.gen_nrs import NRSMetadataGenerator
from pbp.meta_gen.gen_iclisten import IcListenMetadataGenerator
from pbp.meta_gen.gen_soundtrap import SoundTrapMetadataGenerator
from pbp.main_meta_generator_args import parse_arguments

# Some imports, in particular involving data processing, cause a delay that is
# noticeable when just running the --help option. We get around this issue by
# postponing the imports until actually needed. See the main() function.


def main():
    opts = parse_arguments()

    loguru.logger.remove()
    log = copy.deepcopy(loguru.logger)
    info_format = "{message}"
    default_format = "{time} {level} {message}"
    log_filename = (f"{opts.output_dir}/{opts.recorder}{opts.start}_{opts.end}.log",)
    log.add(
        sys.stdout,
        level="INFO",
        format=info_format,
        filter=lambda record: record["level"].name == "INFO",
    )
    log.add(
        sink=open(log_filename, "w"), level="DEBUG", format=default_format, enqueue=True
    )

    log_dir = Path(opts.output_dir)
    json_dir = Path(opts.json_base_dir)
    if opts.xml_dir is None:
        if os.name == "nt":
            xml_dir_str = str(opts.uri).replace("file:\\\\\\", "")
        else:
            xml_dir_str = str(opts.uri).replace("file:///", "")

        xml_dir = Path(xml_dir_str)
    else:
        xml_dir = Path(opts.xml_dir)
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)
    start = datetime.strptime(opts.start, "%Y%m%d")
    end = datetime.strptime(opts.end, "%Y%m%d")

    try:
        if opts.recorder == "NRS":
            generator = NRSMetadataGenerator(
                log=log,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefixes=opts.prefix,
                start=start,
                end=end,
            )
            generator.run()
        if opts.recorder == "ICLISTEN":
            generator = IcListenMetadataGenerator(
                log=log,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefixes=opts.prefix,
                start=start,
                end=end,
            )
            generator.run()
            # TODO: add multiprocessing here for speed-up
        if opts.recorder == "SOUNDTRAP":
            generator = SoundTrapMetadataGenerator(
                log=log,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefixes=opts.prefix,
                start=start,
                end=end,
                xml_dir=xml_dir.as_posix(),
            )
            generator.run()
    except KeyboardInterrupt:
        log.info("INTERRUPTED")


if __name__ == "__main__":
    main()
