#!/usr/bin/env bash
# Prepare the two immutable inputs for the Phase D.0 Zenodo upload.
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
out_dir=${1:-/tmp/dt4n-archive}
checksum_list="$repo_root/docs/phase-D/parquet-sha256-before-delete.txt"

mkdir -p "$out_dir"
cd "$repo_root"

sha256sum -c "$checksum_list"

archive_files=(
  docs/phase-D/parquet-sha256-before-delete.txt
  docs/phase-D/00-reproduction-audit.md
)
while read -r _sha parquet; do
  archive_files+=("$parquet")
  sidecar="${parquet%.parquet}.json"
  if [[ -f "$sidecar" ]]; then
    archive_files+=("$sidecar")
  fi
done < "$checksum_list"

tar -czf "$out_dir/dt4n-phase21R-parquet.tar.gz" "${archive_files[@]}"
tar -czf "$out_dir/dt4n-raw-measurements.tar.gz" results/RAW
(cd "$out_dir" && sha256sum \
  dt4n-phase21R-parquet.tar.gz \
  dt4n-raw-measurements.tar.gz) \
  | tee "$out_dir/SHA256SUMS"
ls -lh "$out_dir/dt4n-phase21R-parquet.tar.gz" \
  "$out_dir/dt4n-raw-measurements.tar.gz" \
  "$out_dir/SHA256SUMS"
