# Ad hoc script to generate plots for all netCDF files under a directory.
# Usage: ./misc/plot.sh <dir>

set -eu
source virtenv/bin/activate

dir=$1

for nc in "${dir}"/*nc; do
  echo -e "\n=== ${nc} ==="
  python src/main_plot.py \
         --latlon 35.77 -121.43 \
         --ylim 10 24000 \
         --title 'Location: MB05, Monterey Bay National Marine Sanctuary, 35.77°N 121.43°W' \
         "${nc}"
done
