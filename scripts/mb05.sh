#!/usr/bin/env bash
#set -eu
export PYTHONPATH=.

year=2022
months=$(seq 11 12)
days=$(seq 1 31)

instrument="SoundTrap ST600 HF, SN 6999"

for month in $months; do
  for day in $days; do
    date=$(printf "%04d%02d%02d" "$year" "$month" "$day")
    python src/main_hmb_generator.py \
           --audio-path-map-prefix="s3://pacific-sound-mb05/~/PAM_Archive/MB05/202211_6999/" \
           --date="$date" \
           --json-base-dir="/PAM_Analysis/JSON/mb05" \
           --global-attrs="metadata/mb05/globalAttributes_MB05.yaml" \
           --variable-attrs="metadata/mb05/variableAttributes_MB05.yaml" \
           --voltage-multiplier=1 \
           --sensitivity-flat-value=175.8 \
           --subset-to 10 24000 \
           --output-prefix=MB05_ \
           --output-dir="/PAM_Analysis/SoundTrapAWS/MB05/6999" \
          > "/tmp/MB05_$date.out" 2>&1 &
  done
done

# wait for all background jobs to finish:
wait
