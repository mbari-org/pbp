# pypam-based-processing, Apache License 2.0
# Filename: metadata/utils/corrector.py
# Description: Correct metadata for wav files and saves the results to a json file. Results are optionally uploaded to S3.

import datetime
from datetime import timedelta

import logger
import numpy as np
import pandas as pd
from pathlib import Path
import shutil
import boto3
import tempfile
import time
import re
import json
from urllib.parse import urlparse


class MetadataCorrector:

    def __init__(
            self,
            logger: PbpLogger,
            correct_df: pd.DataFrame,
            json_path_out: str,
            day: datetime,
            sound_trap: bool,
            seconds_per_file: float):
        """
        Correct the metadata for a day and save to a json file
        :param logger:
            The logger to use
        :param correct_df:
            The dataframe containing the metadata to correct
        :param json_path_out:
            The path to save the corrected metadata json file
        :param day:
            The day to correct
        :param sound_trap:
            True if the files are from a sound trap
        :param seconds_per_file:
            The number of seconds in each file; not used for sound trap files
        """
        self.correct_df = correct_df
        self.metadata_path = json_path_out
        self.day = day
        self.sound_trap = sound_trap
        self.seconds_per_file = seconds_per_file
        self.log = logger

    def run(self):
        """Run the corrector"""

        is_s3 = False
        if re.match(r'^s3://', self.metadata_path):
            is_s3 = True

        try:

            # Soundtrap files can be variable
            if self.sound_trap:
                files_per_day = None
                # Filter the metadata to the day, starting 6 hours before the day starts to capture overlap
                df = self.correct_df[(self.correct_df['start'] >= day - timedelta(hours=6)) & (self.correct_df['start'] < day + timedelta(days=1))]
            else: # ICListen files fixed, but may be missing or incomplete if the system was down
                files_per_day = int(86400 / self.seconds_per_file)
                # Filter the metadata to the day, starting 10 minutes before the day starts to capture overlap
                df = self.correct_df[(self.correct_df['start'] >= day - timedelta(minutes=10)) & (self.correct_df['start'] < day + timedelta(days=1))]

            self.log.debug(f'Creating metadata for day {day}')

            if len(df) == 0:
                self.log.warn(f'No metadata found for day {day}')
                return

            # convert the start and end times to datetime
            df = df.copy()

            df['start'] = pd.to_datetime(df['start'])
            df['end'] = pd.to_datetime(df['end'])

            # get the file list that covers the requested day
            self.log.info(f'Found {len(df)} files from day {day}, starting {df.iloc[0]["start"]} ending {df.iloc[-1]["end"]}')

            # if there are no files, then return
            if len(df) == 0:
                self.log.warn(f'No files found for {day}')
                return

            day_process = df

            if self.sound_trap:
                self.log.info(f'Soundtrap files for {day} are variable. Skipping duration check')
                for index, row in day_process.iterrows():
                    self.log.debug(f'File {row["uri"]} duration {row["duration_secs"]} ')
            else:
                for index, row in day_process.iterrows():
                    # if the duration_secs is not seconds per file, then the file is not complete
                    if row['duration_secs'] != self.seconds_per_file:
                        self.log.warn(f'File {row["duration_secs"]}  != {self.seconds_per_file}. File is not complete')
                        continue

            # check whether there is a discrepancy between the number of seconds in the file and the number
            # of seconds in the metadata. If there is a discrepancy, then correct the metadata
            # This is only reliable for full days of data contained in complete files
            day_process['jitter_secs'] = 0

            if self.sound_trap or \
                    (len(day_process) == files_per_day + 1 \
                     and len(day_process['duration_secs'].unique()) == 1 \
                     and day_process.iloc[0]['duration_secs'] == self.seconds_per_file):

                self.log.info(f'{len(day_process)} files available for {day}')

                # check whether the differences are all the same
                if len(day_process['start'].diff().unique()) == 1 or self.sound_trap:
                    self.log.warn(f'No drift for {day}')
                else:
                    self.log.info(f'Correcting drift for {day}')

                    # correct the metadata
                    jitter = 0
                    start = day_process.iloc[0]['start']
                    end = start + timedelta(seconds=self.seconds_per_file)

                    for index, row in day_process.iterrows():
                        # jitter is the difference between the expected start time and the actual start time
                        # jitter is 0 for the first file
                        if row.start == start:
                            # round the jitter to the nearest second
                            jitter = start.to_datetime64() - row.start.to_datetime64()
                            jitter = int(jitter / np.timedelta64(1, 's'))

                        # correct the start and end times
                        day_process.loc[index, 'start'] = start
                        day_process.loc[index, 'end'] = end
                        day_process.loc[index, 'jitter_secs'] = jitter

                        if self.sound_trap:
                            end = row.end
                        else:
                            end = start + timedelta(seconds=self.seconds_per_file)
                        # round the end time to the nearest second as the timestamp is only accurate to the second
                        end = end.replace(microsecond=0)
                        # set the times for the next files
                        start = end
            else:
                day_process = self.no_jitter(day, day_process)

            # drop any rows with duplicate uri times, keeping the first
            # duplicates can be caused by the jitter correction
            day_process = day_process.drop_duplicates(subset=['uri'], keep='first')

            # save explicitly as UTC by setting the timezone in the start and end times
            day_process['start'] = day_process['start'].dt.tz_localize('UTC')
            day_process['end'] = day_process['end'].dt.tz_localize('UTC')

            self.save_day(day, day_process, is_s3)

        except Exception as e:
            self.log.exception(f'Error correcting metadata for  {day}. {e}')
        finally:
            self.log.debug(f'Done correcting metadata for {day}')

    def no_jitter(
            self,
            day: datetime,
            day_process: pd.DataFrame) -> pd.DataFrame:
        """
        Set the jitter to 0 and calculate the end time from the start time and the duration
        :param day:
            The day being processed
        :param day_process:
            The dataframe to correct
        :return:
            The corrected dataframe
        """
        self.log.warn(f'Cannot correct {day}. Using file start times as is, setting jitter to 0 and using '
                      f'calculated end times.')
        # calculate the difference between each row start time and save as diff in a copy of the dataframe
        day_process = day_process.copy()
        day_process['diff'] = day_process['start'].diff()
        day_process['jitter_secs'] = 0
        # calculate the end time which is the start time plus the number of seconds in the file
        day_process['end'] = day_process['start'] + pd.to_timedelta(day_process['duration_secs'], unit='s')
        return day_process

    def save_day(
            self,
            day: datetime,
            day_process: pd.DataFrame,
            is_s3: bool,
            prefix: str = None):
        """
        Save the day's metadata to a single json file either locally or to s3
        :param day:
            The day to save
        :param day_process:
            The dataframe containing the metadata for the day
        :param prefix:
            An optional prefix for the filename
        :param is_s3:
            True if saving to s3
        :return:
        """
        # if the exception column is empty, then drop it
        if day_process['exception'].isnull().all():
            day_process.drop(columns=['exception'], inplace=True)
        else:
            # replace the NaN with an empty string
            day_process['exception'].fillna('', inplace=True)

        # drop the pcm, fs, subtype, etc. columns
        day_process.drop(columns=['fs', 'subtype', 'jitter_secs'], inplace=True)

        # if there is a diff column, then drop it
        if 'diff' in day_process.columns:
            day_process.drop(columns=['diff'], inplace=True)

        # Save with second accuracy to a temporary file formatted with ISO date format
        df_final = day_process.sort_values(by=['start'])

        with tempfile.TemporaryDirectory() as tmpdir:

            tmp_path = Path(tmpdir)
            if prefix:
                temp_metadata = tmp_path / f'{prefix}_{day:%Y%m%d}.json'
            else:
                temp_metadata = tmp_path / f'{day:%Y%m%d}.json'

            df_final.to_json(temp_metadata.as_posix(), orient='records', date_format='iso', date_unit='s')
            self.log.debug(f'Wrote {temp_metadata.as_posix()}')

            # read the file back in using records format with json
            with open(temp_metadata.as_posix(), 'r') as f:
                dict_records = json.load(f)

            # write the file back out with indenting
            with open(temp_metadata.as_posix(), 'w', encoding='utf-8') as f:
                json.dump(dict_records, f, ensure_ascii=True, indent=4)

            # if a s3 url then upload the file and retry if it fails
            if is_s3:
                client = boto3.client('s3')
                for retry in range(10):
                    try:
                        with open(temp_metadata.as_posix(), 'rb') as data:
                            p = urlparse(self.metadata_path.rstrip('/'))
                            self.log.info(f"Uploading to s3://{p.netloc}/{p.path.lstrip('/')}")
                            if prefix:
                                client.upload_fileobj(data, p.netloc,
                                                      f"{p.path.lstrip('/')}/{prefix}_{day:%Y%m%d}.json")
                            else:
                                client.upload_fileobj(data, p.netloc, f"{p.path.lstrip('/')}/{day:%Y/%Y%m%d}.json")
                            break
                    except Exception as e:
                        self.log.exception(f'Exception {e} on retry {retry}')
                        time.sleep(60)
            else:
                # copy the file to a local metadata directory
                shutil.copy2(temp_metadata.as_posix(), self.metadata_path.as_posix())
