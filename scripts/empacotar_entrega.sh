#!/usr/bin/env bash
set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
output_path="${1:-${project_root}/dist/vantara-concilia-entrega.zip}"
staging_dir="$(mktemp -d)"

cleanup() {
  rm -rf -- "${staging_dir}"
}
trap cleanup EXIT

mkdir -p "${staging_dir}/vantara-concilia" "$(dirname "${output_path}")"

rsync -a \
  --exclude '/.git/' \
  --exclude '/.env' \
  --exclude '/.venv/' \
  --exclude '/.pytest_cache/' \
  --exclude '/.cache_ia/' \
  --exclude '*/.cache_ia/' \
  --exclude '/.DS_Store' \
  --exclude '/__pycache__/' \
  --exclude '*/__pycache__/' \
  --exclude '*.pyc' \
  --exclude '*.pyo' \
  --exclude '/node_modules/' \
  --exclude '/ppt/node_modules/' \
  --exclude '/out_upload/' \
  --exclude '/out_debug/' \
  --exclude '/out_demo/' \
  --exclude '/dist/' \
  "${project_root}/" "${staging_dir}/vantara-concilia/"

rm -f -- "${output_path}"
(
  cd "${staging_dir}"
  zip -qr "${output_path}" vantara-concilia
)

printf 'Pacote criado em: %s\n' "${output_path}"
