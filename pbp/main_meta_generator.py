from argparse import Namespace
from datetime import datetime
from pathlib import Path

from pbp.logging_helper import create_logger
from pbp.meta_gen.gen_abstract import (
    MetadataGeneratorAbstract,
    SoundTrapMetadataGeneratorAbstract,
)
from pbp.meta_gen.gen_nrs import NRSMetadataGenerator
from pbp.meta_gen.gen_iclisten import IcListenMetadataGenerator
from pbp.meta_gen.gen_soundtrap import SoundTrapMetadataGenerator
from pbp.meta_gen.gen_resea import ReseaMetadataGenerator
from pbp.main_meta_generator_args import parse_arguments


# Some imports, in particular involving data processing, cause a delay that is
# noticeable when just running the --help option. We get around this issue by
# postponing the imports until actually needed. See the main() function.


def run_main_meta_generator(opts: Namespace):
    log_dir = Path(opts.output_dir)
    json_dir = Path(opts.json_base_dir)
    log_dir.mkdir(exist_ok=True, parents=True)
    json_dir.mkdir(exist_ok=True, parents=True)
    start = datetime.strptime(opts.start, "%Y%m%d")
    end = datetime.strptime(opts.end, "%Y%m%d")

    log = create_logger(
        log_filename_and_level=(
            f"{opts.output_dir}/{opts.recorder}{start:%Y%m%d}_{end:%Y%m%d}.log",
            "INFO",
        ),
        console_level="INFO",
    )

    generator: MetadataGeneratorAbstract | SoundTrapMetadataGeneratorAbstract
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
            )
            generator.run()
        if opts.recorder == "RESEA":
            generator = ReseaMetadataGenerator(
                log=log,
                uri=opts.uri,
                json_base_dir=json_dir.as_posix(),
                prefixes=opts.prefix,
                start=start,
                end=end,
            )
            generator.run()
    except KeyboardInterrupt:
        log.info("INTERRUPTED")


if __name__ == "__main__":
    run_main_meta_generator(parse_arguments())
