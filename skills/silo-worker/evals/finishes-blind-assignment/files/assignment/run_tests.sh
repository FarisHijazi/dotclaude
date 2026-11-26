#!/usr/bin/env bash
set -eu
cd "$(dirname "$0")"
PYTHONPATH=src:starter python3 -m pytest -q tests
