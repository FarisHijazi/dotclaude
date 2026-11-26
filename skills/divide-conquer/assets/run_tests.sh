#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
PYTHONPATH=src python3 -m pytest -q tests
