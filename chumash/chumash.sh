#!/usr/bin/env bash

# A quick-n-dirty script to fulfill the following inquiry indicated on Slack
# related with creation of spectrograms for wav files under a given directory.
#
# "... take the base file name for creating the output png name:
# - changes the 6998 to CH01
# - adds 20 before 22 (after the first ., so we have full year info 2022)
# - changes .wav to .png for the output spectrogram
# - saves the png spectrogram files either with the wav files in that same
#   directory or in a folder we can specify".

function usage() {
    echo "Usage: $0 <wav_directory>  [<destination_directory>]"
    echo "Example: $0 /Volumes/PAM_Archive/CH01  /tmp"
    exit 1
}

function get_png_path() {
    local wav_file=$1
    local destination_directory=$2
    local base_wav=$(basename "$wav_file")
    local base_png=${base_wav%.wav}.png
    local base_png=${base_png//6998\./CH01_20}
    local path_png="$destination_directory/$base_png"
    echo "$path_png"
}

function main() {
    local wav_directory=$1
    if [ $# -gt 1 ]; then
        local destination_directory=$2
    else
        local destination_directory=$wav_directory
    fi

    for wav_file in $(find "$wav_directory" -name "*.wav"); do
        local path_png=$(get_png_path "$wav_file" "$destination_directory")
        echo "input : $wav_file"
        echo "output: $path_png"
        sox "$wav_file" -n spectrogram -o "$path_png"
        echo
    done
}

if [ $# -gt 0 ]; then
    main "$@"
else
    usage
fi