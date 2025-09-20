from argparse import Namespace
from typing import Optional

import loguru
import pathlib
import soundfile as sf
from math import ceil
import numpy as np
import xarray as xr
from datetime import datetime, timezone, timedelta

from pbp.logging_helper import create_logger
from pbp.misc_helper import parse_timestamp
from pbp.process_helper import (
    ProcessDayResult,
    DEFAULT_QUALITY_FLAG_VALUE,
    save_dataset_to_netcdf,
)
from pbp.pypam_support import ProcessResult, PypamSupport


def main_hmb_generator_file(opts: Namespace) -> None:
    input_path = pathlib.Path(opts.input_file)
    if not input_path.exists():
        print(f"Input file '{opts.input_file}' does not exist.")
        exit(1)

    simple_name = input_path.stem

    if opts.timestamp_pattern is not None:
        base_dt = parse_timestamp(simple_name, opts.timestamp_pattern)
        if base_dt is not None:
            print(f"Extracted timestamp from filename: {base_dt.isoformat()}")
        else:
            print(
                f"Could not extract timestamp from '{simple_name}' with {opts.timestamp_pattern=}"
            )
            exit(1)
    else:
        base_dt = datetime(2000, 1, 1, tzinfo=timezone.utc)
        print(f"WARNING: No timestamp pattern provided, using {base_dt}.")

    sensitivity_da: Optional[xr.DataArray] = None
    if opts.sensitivity_uri is not None:
        if not pathlib.Path(opts.sensitivity_uri).exists():
            print(f"Sensitivity file '{opts.sensitivity_uri}' does not exist.")
            exit(1)
        sensitivity_da = xr.open_dataarray(opts.sensitivity_uri)
        print(f"Loaded sensitivity from '{opts.sensitivity_uri}'")

    sound_file = sf.SoundFile(opts.input_file)
    log_filename = f"{opts.output_dir}/{simple_name}.log"
    output_filename = f"{opts.output_dir}/{simple_name}.nc"

    print(f"  Input file:      {sound_file}")
    print(f"  log_filename:    {log_filename}")
    print(f"  output_filename: {output_filename}")
    print(f"  time_resolution: {opts.time_resolution}")

    log = create_logger(
        log_filename_and_level=(log_filename, "INFO"),
        console_level="WARNING",
    )

    try:
        res = FileProcessor(
            opts,
            log,
            sound_file,
            base_dt,
            sensitivity_da,
            output_filename,
        ).process()

        print(f"Result: {res}")
    except KeyboardInterrupt:
        log.info("INTERRUPTED")


class FileProcessor:
    def __init__(
        self,
        opts: Namespace,
        log: "loguru.Logger",
        sound_file: sf.SoundFile,
        base_dt: datetime,
        sensitivity_da: Optional[xr.DataArray],
        output_filename: str,
    ) -> None:
        self.opts = opts
        self.log = log
        self.sound_file = sound_file
        self.base_dt = base_dt
        self.sensitivity_da = sensitivity_da
        self.output_filename = output_filename

        self.pypam_support = PypamSupport(self.log)

        self.start_secs = 0
        self.num_samples_per_segment = ceil(
            self.opts.time_resolution * sound_file.samplerate
        )
        print(f"  num_samples_per_segment: {self.num_samples_per_segment}")

    def process(self) -> Optional[ProcessDayResult]:
        """
        Generates NetCDF file with the result of processing all segments of the given audio file.

        Returns:
            The result or None if no segments at all were processed.
        """
        self.log.info(f"Processing file: {self.sound_file.name}")
        self.log.info(f"Output will be saved to: {self.output_filename}")

        audio_segment = self.extract_next_audio_segment()
        if audio_segment is None:
            self.log.info("No audio segment extracted. Exiting.")
            return None

        subset_to = tuple(self.opts.subset_to) if self.opts.subset_to else None
        self.pypam_support.set_parameters(
            self.sound_file.samplerate,
            subset_to=subset_to,
        )

        segment_index = 0
        while audio_segment is not None:
            self.log.trace(f"{segment_index=} {audio_segment=}")
            dt = self.base_dt + timedelta(
                seconds=segment_index * self.opts.time_resolution
            )
            self.process_audio_segment(dt, audio_segment)
            audio_segment = self.extract_next_audio_segment()
            segment_index += 1

        print(f"  Gathered {segment_index} segments.")

        print("  Processing captured segments...")
        result: Optional[ProcessResult] = self.pypam_support.process_captured_segments(
            sensitivity_da=self.sensitivity_da,
        )

        if result is None:
            self.log.warning("No segments processed, nothing to aggregate.")
            return None

        psd_da = result.psd_da

        # rename 'frequency_bins' dimension to 'frequency':
        psd_da = psd_da.swap_dims(frequency_bins="frequency")

        data_vars = {
            "psd": psd_da,
            "effort": result.effort_da,
        }

        if self.sensitivity_da is not None:
            freq_subset = self.sensitivity_da.interp(frequency=psd_da.frequency)
            data_vars["sensitivity"] = freq_subset

        elif self.opts.sensitivity_flat_value is not None:
            # better way to capture a scalar?
            data_vars["sensitivity"] = xr.DataArray(
                data=[self.opts.sensitivity_flat_value],
                dims=["1"],
            ).astype(np.float32)

        if self.opts.add_quality_flag:
            data_vars["quality_flag"] = xr.DataArray(
                data=np.full(psd_da.shape, DEFAULT_QUALITY_FLAG_VALUE, dtype=np.int8),
                dims=psd_da.dims,
                coords=psd_da.coords,
                # attrs are assigned below.
            )

        # TODO
        # md_helper = self.metadata_helper
        #
        # md_helper.add_variable_attributes(psd_da["time"], "time")
        # md_helper.add_variable_attributes(data_vars["effort"], "effort")
        # md_helper.add_variable_attributes(psd_da["frequency"], "frequency")
        # if "sensitivity" in data_vars:
        #     md_helper.add_variable_attributes(data_vars["sensitivity"], "sensitivity")
        # if "quality_flag" in data_vars:
        #     md_helper.add_variable_attributes(data_vars["quality_flag"], "quality_flag")
        # md_helper.add_variable_attributes(data_vars["psd"], "psd")

        ds_result = xr.Dataset(
            data_vars=data_vars,
            # attrs=self._get_global_attributes(year, month, day),
        )

        save_dataset_to_netcdf(self.log, ds_result, self.output_filename)
        generated_filenames = [self.output_filename]

        return ProcessDayResult(generated_filenames, ds_result)

    def extract_next_audio_segment(self) -> np.ndarray | None:
        if self.sound_file.tell() >= len(self.sound_file):
            return None

        audio_segment = self.sound_file.read(self.num_samples_per_segment)
        actual_num_samples = len(audio_segment)
        actual_duration_secs = actual_num_samples / self.sound_file.samplerate
        self.log.trace(
            f"Extracted segment starting at {self.start_secs} secs: "
            f"{actual_num_samples} samples, {actual_duration_secs:.2f} secs"
        )
        self.start_secs += actual_duration_secs
        return audio_segment

    def pre_process_audio_segment(self, audio_segment: np.ndarray) -> np.ndarray:
        if self.opts.voltage_multiplier is not None:
            audio_segment *= self.opts.voltage_multiplier

        if self.opts.sensitivity_flat_value is not None:
            audio_segment = audio_segment * 10 ** (self.opts.sensitivity_flat_value / 20)

        return audio_segment

    def process_audio_segment(self, dt: datetime, audio_segment: np.ndarray) -> None:
        audio_segment = self.pre_process_audio_segment(audio_segment)
        self.pypam_support.add_segment(dt, audio_segment)
