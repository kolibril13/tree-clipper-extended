#!/usr/bin/env bash
set -euo pipefail

VERSION="${1:-}"
ROOT_DIR="${2:-}"

if [[ -z "$VERSION" ]]; then
  echo "Usage: $0 <version> [root_dir]" >&2
  exit 1
fi

echo "Exporting trees for all .blend files under: $ROOT_DIR"
echo "Using version: $VERSION"
echo

# Find all .blend files and process them
find "$ROOT_DIR" -type f -name '*.blend' -print0 | while IFS= read -r -d '' file; do
  dir="$(dirname "$file")"
  base="$(basename "$file")"
  base_no_ext="${base%.blend}"
  outdir="${dir}/${base_no_ext}_${VERSION}"

  echo "Processing: $file"
  echo "  -> Output directory: $outdir"
  echo

  uv run packages/tree_clipper_tools/src/tree_clipper_tools/export_all_trees.py \
    --filename "$file" \
    --directory "$outdir"
done
