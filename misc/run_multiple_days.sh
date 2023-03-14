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
  base=$(printf "%s/milli_psd_%04d%02d%02d" "$output_dir" "$year" "$month" "$day")
  out="$base.out"
  err="$base.err"
  echo "running: day=$day output_dir=$output_dir"
  python src/main.py \
         --year="$year" --month="$month" --day="$day" \
         --json-base-dir=json/"$year" \
         --audio-path-map-prefix="s3://pacific-sound-256khz-${year}~file:///PAM_Archive/${year}" \
         --output-dir="$output_dir" \
         > "$out" 2> "$err" &
done
wait
