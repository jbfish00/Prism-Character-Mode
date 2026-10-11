#!/bin/sh
# Build, then write build/prism_cm.bps (a BPS patch against the untouched base ROM).
# Never distribute the ROM itself; the patch is the deliverable.
set -e
cd "$(dirname "$0")/.."
tools/build.sh
BASE="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
tools/bin/flips --create --bps "$BASE" build/prism_cm.gbc build/prism_cm.bps
ls -l build/prism_cm.bps
