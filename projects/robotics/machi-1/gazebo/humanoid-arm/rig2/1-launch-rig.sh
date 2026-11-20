#!/bin/bash
set -e
HERE="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$HERE/7-launch-rig2.sh" "$@"