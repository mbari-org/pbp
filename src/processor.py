import pathlib

import soundfile as sf

from src.file_helper import FileHelper
from src.misc_helper import gen_hour_minute_times
from src.pypam_support import pypam_process


def process_day(
    file_helper: FileHelper,
    year: int,
    month: int,
    day: int,
    output_dir: str,
    save_extracted_wav: bool = False,
):
    if not file_helper.select_day(year, month, day):
        return

    pathlib.Path(output_dir).mkdir(exist_ok=True)

    # TODO capture info for "effort" variable, in particular,
    #  the number of seconds of actual data per segment

    for at_hour, at_minute in gen_hour_minute_times(file_helper.segment_size_in_mins):
        print(f"\nSegment at {at_hour:02}h:{at_minute:02}m ...")
        print(f"  - extracting {file_helper.segment_size_in_mins * 60}-sec segment:")
        extraction = file_helper.extract_audio_segment(at_hour, at_minute)
        # TODO properly consider the 3 possible cases for the segment:
        #   whole data, partial data, no data
        # for now, assuming whole minute segment
        if extraction is None:
            print(f"ERROR: cannot get audio segment at {at_hour:02}:{at_minute:02}")
            return

        audio_info, audio_segment = extraction

        if save_extracted_wav:
            wav_filename = f"{output_dir}/extracted_{year:04}{month:02}{day:02}_{at_hour:02}{at_minute:02}00.wav"
            sf.write(
                wav_filename, audio_segment, audio_info.samplerate, audio_info.subtype
            )
            print(f"  √ saved extracted wav: {wav_filename} len={len(audio_segment):,}")

        audio_segment *= 3  # voltage multiplier

        # print(f"  √ segment loaded, len = {len(audio_segment):,}")
        print("  - processing ...")
        milli_psd = pypam_process(audio_info.samplerate, audio_segment)

        # Note: preliminary naming for output, etc.
        netcdf_filename = f"{output_dir}/milli_psd_{year:04}{month:02}{day:02}_{at_hour:02}{at_minute:02}00.nc"
        print(f"  - saving milli_psd result to {netcdf_filename}")
        milli_psd.to_netcdf(netcdf_filename)
        # on my Mac: format='NETCDF4_CLASSIC' triggers:
        #    ValueError: invalid format for scipy.io.netcdf backend: 'NETCDF4_CLASSIC'
