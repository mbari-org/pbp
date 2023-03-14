#!/usr/bin/env bash
year="2022"
month="9"
output_dir="/PAM_Analysis/pypam-space/test_output/daily"

for day in $(seq {{from_day}} {{to_day}}); do
  log=$(printf "%s/milli_psd_%04d%02d%02d.log" "$output_dir" "$year" "$month" "$day")
  cmd="just main-gizo year=$year month=$month day=$day output_dir=$output_dir"
  # echo "running $cmd > $log 2>&1"
  "$cmd" > "$log" 2>&1 &
done
wait
