import pathlib

from src.file_helper import FileHelper
from src.misc_helper import gen_hour_minute_times
from src.pypam_support import pypam_process


def process_day(file_helper: FileHelper, year: int, month: int, day: int):
    if not file_helper.select_day(year, month, day):
        return

    output_dir = "output"
    pathlib.Path(output_dir).mkdir(exist_ok=True)

    for at_hour, at_minute in gen_hour_minute_times(file_helper.segment_size_in_mins):
        print(f"\nSegment at {at_hour:02}h:{at_minute:02}m ...")
        print(f"  - extracting {file_helper.segment_size_in_mins * 60}-sec segment:")
        extraction = file_helper.extract_audio_segment(at_hour, at_minute)
        if extraction is None:
            print(f"ERROR: cannot get audio segment at {at_hour:02}:{at_minute:02}")
            return

        sample_rate, audio_segment = extraction
        # print(f"  √ segment loaded, len = {len(audio_segment):,}")
        print("  - processing ...")
        milli_psd = pypam_process(sample_rate, audio_segment)

        # Note: preliminary naming for output, etc.
        netcdf_filename = f"{output_dir}/milli_psd_{year:04}{month:02}{day:02}_{at_hour:02}{at_minute:02}00.nc"
        print(f"  - saving milli_psd result to {netcdf_filename}")
        milli_psd.to_netcdf(netcdf_filename)
        # on my Mac: format='NETCDF4_CLASSIC' triggers:
        #    ValueError: invalid format for scipy.io.netcdf backend: 'NETCDF4_CLASSIC'


def main():
    json_base_dir = "tests/json"
    audio_base_dir = "tests/wav"
    segment_size_in_mins: int = 1
    file_helper = FileHelper(json_base_dir, audio_base_dir, segment_size_in_mins)
    try:
        process_day(file_helper, 2022, 9, 2)
    except KeyboardInterrupt:
        print("\nInterrupted")


if __name__ == "__main__":
    main()
