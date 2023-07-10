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

# Run main (on my mac)
main-mac *more_args="":
    PYTHONPATH=. python src/main.py \
                 --json-base-dir=tests/json \
                 --audio-path-prefix=/Volumes \
                 --date=20220902 \
                 --voltage-multiplier=3 \
                 --sensitivity-uri=misc/icListen1689_sensitivity_hms256kHz.nc \
                 --gen-csv \
                 --subset-to 10 100000 \
                 --output-dir=output \
                 {{more_args}}

#                 --max-segments=5 \
#                 --output-dir=/Volumes/PAM_Analysis/pypam-space/test_output \

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

# MARS basic test for cloud processing
#main-cloud-mars-basic-test date="20220909":
main-cloud-mars-basic-test max_segments="60" date="20210901":
    #!/usr/bin/env bash
    export EXCLUDE_LOG_TIME=yes
    export ASSUME_DOWNLOADED_FILES=yes
    export MAX_SEGMENTS={{max_segments}}
    export DATE={{date}}
    export S3_JSON_BUCKET_PREFIX="s3://pacific-sound-metadata/256khz"
    export OUTPUT_PREFIX="MARS_pypam_0_2_0_"
    export VOLTAGE_MULTIPLIER=3
    export SENSITIVITY_NETCDF_URI=misc/icListen1689_sensitivity_hms256kHz.nc
    export GLOBAL_ATTRS_URI="metadata/mars/globalAttributes.json"
    export VARIABLE_ATTRS_URI="metadata/mars/variableAttributes.json"
    export CLOUD_TMP_DIR="cloud_tmp_mars"
    export REMOVE_DOWNLOADED_FILES=no
    export PYTHONPATH=.
    python src/main_cloud.py

# Process multiple days for MARS data
main-cloud-mars-multiple-days year="2022" month="9" *days="5 7 8 9":
    #!/usr/bin/env bash
    source virtenv/bin/activate
    set -ue
    output_dir="/PAM_Analysis/pypam-space/test_output_mars/with_pypam_0.2.0"
    mkdir -p "$output_dir"
    echo "Running: year={{year}} month={{month}} days={{days}}"
    for day in {{days}}; do
      date=$(printf "%04d%02d%02d" {{year}} {{month}} "$day")
      out="$output_dir/MARS_$date.out"
      just main-cloud-mars-basic-test $date > "$out" 2>&1 &
    done
    wait

# chumash basic test for cloud processing
main-cloud-chumash-basic-test max_segments="60" date="20230101":
    #!/usr/bin/env bash
    export DATE={{date}}
    export S3_JSON_BUCKET_PREFIX="s3://pacific-sound-metadata/ch01"
    export SENSITIVITY_FLAT_VALUE=176
    export GLOBAL_ATTRS_URI="metadata/chumash/globalAttributes.json"
    export VARIABLE_ATTRS_URI="metadata/chumash/variableAttributes.json"
    export MAX_SEGMENTS={{max_segments}}
    export CLOUD_TMP_DIR="cloud_tmp_chumash"
    export REMOVE_DOWNLOADED_FILES=no
    export PYTHONPATH=.
    python src/main_cloud.py

# Run main
main *args="":
    PYTHONPATH=. python src/main.py {{args}}

##############
# development:

# A convenient recipe for development
dev: check test format

# As the dev recipe plus pylint; good to run before committing changes
all: dev pylint

# Create virtual environment
virtenv:
    python3 -m venv virtenv

# Install dependencies
setup:
    pip3 install -r requirements.txt
    pip3 install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ lifewatch-pypam==0.2.0
    mypy --install-types

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
    python -m ufmt format .

# Format source code using ruff
ruff:
    ruff --fix .

# Run pylint
pylint:
    python -m pylint src

# With prior running of:
#   python -m pip install --upgrade build
# Create dist
dist:
    python -m build
