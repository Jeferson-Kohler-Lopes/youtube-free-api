#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
read -r -p "URL ou @handle do canal: " CHANNEL
python -m collector.collect "$CHANNEL" --max-videos 200 --max-competitors 3 --output reports/latest.json
printf '\nRelatório criado em reports/latest.json\n'
