#
# Run these recipes using `just` - https://github.com/casey/just.
#

# List recipes
list:
    @just --list --unsorted

####################
# some conveniences:

# ssh to gizo
ssh-gizo user="carueda" server="gizo.shore.mbari.org":
    ssh {{user}}@{{server}}

# Package and transfer complete code to gizo
to-gizo user="carueda" server="gizo.shore.mbari.org": tgz
    #!/usr/bin/env bash
    HASH=$(git rev-parse --short HEAD)
    echo "$HASH" > HASH
    scp HASH pypam-based-processing_${HASH}.tgz {{user}}@{{server}}:/PAM_Analysis/pypam-space/processing_our_data/

# Package for subsequent code transfer to gizo
tgz:
    #!/usr/bin/env bash
    HASH=$(git rev-parse --short HEAD)
    git archive ${HASH} -o pypam-based-processing_${HASH}.tgz --prefix=pypam-based-processing/

# Run main (on gizo)
main-gizo date="20220902" output_dir="/PAM_Analysis/pypam-space/test_output/daily":
    PYTHONPATH=. python src/main.py \
                 --json-base-dir=json \
                 --date={{date}} \
                 --voltage-multiplier=3 \
                 --sensitivity-uri=misc/icListen1689_sensitivity_hms256kHz.nc \
                 --subset-to 10 100000 \
                 --audio-path-map-prefix="s3://pacific-sound-256khz-2022~file:///PAM_Archive/2022" \
                 --output-dir={{output_dir}}

# Run main (on gizo) with some initial test jsons
main-gizo-test *more_args="":
    PYTHONPATH=. python src/main.py \
                 --json-base-dir=tests/json \
                 --date=20220902 \
                 --voltage-multiplier=3 \
                 --sensitivity-uri=misc/icListen1689_sensitivity_hms256kHz.nc \
                 --subset-to 10 100000 \
                 --audio-base-dir=tests/wav \
                 --audio-path-map-prefix="s3://pacific-sound-256khz-2022~file:///PAM_Archive/2022" \
                 --output-dir=/PAM_Analysis/pypam-space/test_output/daily \
                 {{more_args}}

# Run multiple days (on gizo)
main-gizo-multiple-days year month *days="":
    #!/usr/bin/env bash
    source virtenv/bin/activate
    set -ue
    output_dir="/PAM_Analysis/pypam-space/test_output/daily"
    echo "Running: year={{year}} month={{month}} days={{days}}"
    export PYTHONPATH=.
    for day in {{days}}; do
      date=$(printf "%04d%02d%02d" {{year}} {{month}} "$day")
      base="$output_dir/milli_psd_$date"
      out="$base.out"
      echo "running: day=$day output_dir=$output_dir"
      python src/main.py \
             --json-base-dir=json \
             --date="$date" \
             --voltage-multiplier=3 \
             --sensitivity-uri=misc/icListen1689_sensitivity_hms256kHz.nc \
             --subset-to 10 100000 \
             --audio-path-map-prefix="s3://pacific-sound-256khz-{{year}}~file:///PAM_Archive/{{year}}" \
             --output-dir="$output_dir" \
             > "$out" 2>&1 &
    done
    wait

# Replicate notebook
main-mb05 *more_args="":
    #!/usr/bin/env bash
    #mkdir -p NB_SPACE/JSON/2022
    mkdir -p NB_SPACE/DOWNLOADS
    mkdir -p NB_SPACE/OUTPUT

    PYTHONPATH=. EXCLUDE_LOG_TIME=yes \
        python src/main.py \
                 --date=20220812 \
                 --json-base-dir=NB_SPACE/JSON \
                 --voltage-multiplier=1 \
                 --sensitivity-flat-value=1 \
                 --global-attrs metadata/mb05/globalAttributes_MB05.yaml \
                 --variable-attrs metadata/mb05/variableAttributes_MB05.yaml \
                 --subset-to 10 24000 \
                 --output-dir=NB_SPACE/OUTPUT \
                 --output-prefix=MB05_ \
                 --download-dir=NB_SPACE/DOWNLOADS \
                 --assume-downloaded-files \
                 --retain-downloaded-files \
                 --max-segments=5 \
                 {{more_args}}

#                 --max-segments=5 \
#                 --output-dir=/Volumes/PAM_Analysis/pypam-space/test_output \

# Exercise program with `gs://` URIs
main-nrs11 date='20200101' *more_args='':
    #!/usr/bin/env bash
    WS=NRS11
    mkdir -p $WS/DOWNLOADS
    mkdir -p $WS/OUTPUT
    PYTHONPATH=. EXCLUDE_LOG_TIME=yes \
        python src/main.py \
                 --date={{date}} \
                 --gs \
                 --json-base-dir=$WS/noaa-passive-bioacoustic_nrs_11_2019-2021 \
                 --global-attrs="$WS/globalAttributes_NRS11.yaml" \
                 --set-global-attr serial_number "000000" \
                 --variable-attrs="$WS/variableAttributes_NRS11.yaml" \
                 --voltage-multiplier=2.5 \
                 --sensitivity-uri="$WS/NRS11_H5R6_sensitivity_hms5kHz.nc" \
                 --subset-to 10 2000 \
                 --output-prefix=NRS11_ \
                 --output-dir="$WS/OUTPUT" \
                 --download-dir="$WS/DOWNLOADS" \
                 --retain-downloaded-files \
                 --assume-downloaded-files \
                 {{more_args}}

# E.g., all January 2020 days: 2020 1 $(seq 1 31)
main-nrs11-multiple-days year month *days="":
    #!/usr/bin/env bash
    WS=NRS11
    mkdir -p $WS/DOWNLOADS  $WS/OUTPUT
    echo "Running: year={{year}} month={{month}} days={{days}}"
    export PYTHONPATH=.
    for day in {{days}}; do
      date=$(printf "%04d%02d%02d" {{year}} {{month}} "$day")
      python src/main.py \
             --date="$date" \
             --gs \
             --json-base-dir=$WS/noaa-passive-bioacoustic_nrs_11_2019-2021 \
             --global-attrs="$WS/globalAttributes_NRS11.yaml" \
             --set-global-attr serial_number "000000" \
             --variable-attrs="$WS/variableAttributes_NRS11.yaml" \
             --voltage-multiplier=2.5 \
             --sensitivity-uri="$WS/NRS11_H5R6_sensitivity_hms5kHz.nc" \
             --subset-to 10 2000 \
             --output-prefix=NRS11_ \
             --output-dir="$WS/OUTPUT" \
             --download-dir="$WS/DOWNLOADS" \
             --retain-downloaded-files \
             --assume-downloaded-files \
            > "$WS/OUTPUT/NRS11_$date.out" 2>&1 &
    done
    wait

# Plot NRS11 datasets
plot-nrs11 *netcdfs='NRS11/OUTPUT/NRS11_20200101.nc':
    python src/plot.py \
      --ylim 10 2000 \
      --cmlim 64 108 \
      --latlon 37.88 -123.44 \
      --title "NOAA Ocean Noise Reference Station NRS11, Cordell Bank National Marine Sanctuary:  37.88°N, 123.44°W" \
      {{netcdfs}}

# Basic test for cloud processing
main-cloud-basic-test max_segments="1" date="20220902":
    #!/usr/bin/env bash
    export EXCLUDE_LOG_TIME=yes
    export DATE={{date}}
    export VOLTAGE_MULTIPLIER=3
    export SENSITIVITY_NETCDF_URI=misc/icListen1689_sensitivity_hms256kHz.nc
    export MAX_SEGMENTS={{max_segments}}
    export PYTHONPATH=.
    python src/main_cloud.py

# dev/test conveniences:
#    export EXCLUDE_LOG_TIME=yes
#    export ASSUME_DOWNLOADED_FILES=yes
#    export MAX_SEGMENTS=60
#main-cloud-mars-basic-test max_segments="60" date="20210901":
# MARS basic test for cloud processing
main-cloud-mars-basic-test date="20210901":
    #!/usr/bin/env bash
    export DATE={{date}}
    export S3_JSON_BUCKET_PREFIX="s3://pacific-sound-metadata/256khz"
    export OUTPUT_PREFIX="MARS_"
    export VOLTAGE_MULTIPLIER=3
    export SENSITIVITY_NETCDF_URI=misc/icListen1689_sensitivity_hms256kHz.nc
    export GLOBAL_ATTRS_URI="metadata/mars/globalAttributes.yaml"
    export VARIABLE_ATTRS_URI="metadata/mars/variableAttributes.yaml"
    export CLOUD_TMP_DIR="with_pypam_0.2.0"
    export RETAIN_DOWNLOADED_FILES=yes
    export PYTHONPATH=.
    python src/main_cloud.py

# Process multiple days for MARS data
main-cloud-mars-multiple-days year="2022" month="9" *days="5 7 8 9":
    #!/usr/bin/env bash
    source virtenv/bin/activate
    set -ue
    output_dir="with_pypam_0.2.0"
    mkdir -p "$output_dir"
    echo "Running: year={{year}} month={{month}} days={{days}}"
    for day in {{days}}; do
      date=$(printf "%04d%02d%02d" {{year}} {{month}} "$day")
      out="$output_dir/MARS_$date.out"
      just main-cloud-mars-basic-test $date > "$out" 2>&1 &
    done
    wait

#    export MAX_SEGMENTS=60
#    export ASSUME_DOWNLOADED_FILES=yes
# chumash basic test for cloud processing
main-cloud-chumash-basic-test date="20230108":
    #!/usr/bin/env bash
    export DATE={{date}}
    export S3_JSON_BUCKET_PREFIX="s3://pacific-sound-metadata/ch01"
    export SENSITIVITY_FLAT_VALUE=176.1
    export OUTPUT_PREFIX="CH01_"
    export GLOBAL_ATTRS_URI="metadata/chumash/globalAttributes.yaml"
    export VARIABLE_ATTRS_URI="metadata/chumash/variableAttributes.yaml"
    export CLOUD_TMP_DIR="cloud_tmp_chumash"
    export RETAIN_DOWNLOADED_FILES=yes
    export PYTHONPATH=.
    python src/main_cloud.py

# Run main
main *args="":
    PYTHONPATH=. python src/main.py {{args}}

##############
# misc/utils:

# Generate summary plots
plot *args:
    python src/plot.py {{args}}

##############
# docker:

dockerize-for-notebooks dockerfile='docker/Dockerfile-minimal':
    docker build -f {{dockerfile}} -t mbari/pbp .

run-docker-for-notebooks dir='notebooks':
    docker run -it --rm -p 8899:8899 mbari/pbp:1


##############
# development:

# A convenient recipe for development
dev: check test format

# As the dev recipe plus lint; good to run before committing changes
all: dev lint

# Create virtual environment
virtenv:
    python3.9 -m venv virtenv

# Install dependencies
setup:
    pip3 install -r requirements.txt
    mypy --install-types
    pip3 install types-PyYAML
    pip3 install types-python-dateutil


# Install updated dependencies
update-deps:
    pip3 install -r requirements.txt

# Do static type checking (not very strict)
check:
    python -m mypy .

# Install std types for mypy
install-types:
    python -m mypy --install-types

# Do snapshot-update
snapshot-update:
    python -m pytest --snapshot-update

# Run tests
test *options="":
    python -m pytest {{options}}

# Format source code
format:
    ruff format .

# Lint source code
lint:
    ruff check --fix

# List git tags
tags:
    git tag -l | sort -V | tail

# With prior running of:
#   python -m pip install --upgrade build
# Create dist
dist:
    python -m build
