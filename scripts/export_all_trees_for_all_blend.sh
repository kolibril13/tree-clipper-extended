#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-}"
OUTPUT_DIR="${2:-}"

echo "Exporting trees for all .blend files under: $INPUT_DIR"
echo "Output goes to: $OUTPUT_DIR"
echo

# Find all .blend files and process them
find "$INPUT_DIR" -type f -name '*.blend' -print0 | while IFS= read -r -d '' file; do
  dir="$(dirname "$file")"
  dir="$(realpath --relative-to "$INPUT_DIR" "$dir")"
  base="$(basename "$file")"
  base_no_ext="${base%.blend}"
  outdir="${OUTPUT_DIR}/${dir}/${base_no_ext}"

  echo "Processing: $file"
  echo "  -> Output directory: $outdir"
  echo

  uv run packages/tree_clipper_tools/src/tree_clipper_tools/export_all_trees.py \
    --filename "$file" \
    --directory "$outdir"
done
