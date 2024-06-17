#!/usr/bin/env bash
set -euo pipefail
repo_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
figure_dir="$repo_root/docs/figures"
tex_build_dir="$(mktemp -d)"
trap 'rm -rf -- "$tex_build_dir"' EXIT
pdflatex -interaction=nonstopmode -halt-on-error -output-directory "$tex_build_dir" \
  "$figure_dir/feedslicer_workflow.tex"
cp -- "$tex_build_dir/feedslicer_workflow.pdf" "$figure_dir/feedslicer_workflow.pdf"
pdftoppm -png -singlefile -scale-to 2000 \
  "$figure_dir/feedslicer_workflow.pdf" "$figure_dir/feedslicer_workflow"
pdftocairo -svg "$figure_dir/feedslicer_workflow.pdf" "$figure_dir/feedslicer_workflow.svg"
