#!/usr/bin/env bash
set -ue

from_day=$1
to_day=$2

year="2022"
month="9"
output_dir="/PAM_Analysis/pypam-space/test_output/daily"

echo "Running: year=$year month=$month from_day=$from_day to_day=$to_day"

export PYTHONPATH=.

for day in $(seq "$from_day" "$to_day"); do
  date=$(printf "%04d%02d%02d" "$year" "$month" "$day")
  base=$(printf "%s/milli_psd_$date" "$output_dir" "$date")
  err="$base.err"
  echo "running: day=$day output_dir=$output_dir"
  python src/main.py \
         --date="$date" \
         --json-base-dir=json/"$year" \
         --audio-path-map-prefix="s3://pacific-sound-256khz-${year}~file:///PAM_Archive/${year}" \
         --output-dir="$output_dir" \
         2> "$err" &
done
wait
