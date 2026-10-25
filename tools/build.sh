#!/bin/sh
# Build the Character Mode overlay onto the base ROM -> build/prism_cm.gbc (+ .sym, .map).
# A second image, build/prism_cm_test.gbc, adds the test-only drivers (-DCM_TEST); it is what the
# statistical tests use and is never distributed.
set -e
cd "$(dirname "$0")/.."
python3 tools/character_mode/emit_select.py >/dev/null
python3 tools/character_mode/emit_mart_evo.py >/dev/null
BASE="rom/Pokemon Prism (v0.95 build 254 Hotfix 5).gbc"
tools/bin/rgbasm -o build/character_mode.o src/character_mode.asm
tools/bin/rgblink -O "$BASE" -o build/prism_cm.gbc \
  -n build/prism_cm.sym -m build/prism_cm.map build/character_mode.o
tools/bin/rgbasm -DCM_TEST=1 -o build/character_mode_test.o src/character_mode.asm
tools/bin/rgblink -O "$BASE" -o build/prism_cm_test.gbc \
  -n build/prism_cm_test.sym -m build/prism_cm_test.map build/character_mode_test.o
tools/bin/rgbasm -DCM_TEST=1 -DCM_NO_EGGRELEARN=1 -o build/character_mode_test_noegg.o src/character_mode.asm
tools/bin/rgblink -O "$BASE" -o build/prism_cm_test_noegg.gbc \
  -n build/prism_cm_test_noegg.sym build/character_mode_test_noegg.o     # control: vanilla relearner list
tools/bin/rgbasm -DCM_TEST=1 -DCM_NO_MART=1 -o build/character_mode_test_nomart.o src/character_mode.asm
tools/bin/rgblink -O "$BASE" -o build/prism_cm_test_nomart.gbc \
  -n build/prism_cm_test_nomart.sym build/character_mode_test_nomart.o     # control: the Marts' own lists
tools/bin/rgbasm -DCM_TEST=1 -DCM_NO_ANYLEVEL=1 -o build/character_mode_test_nolv.o src/character_mode.asm
tools/bin/rgblink -O "$BASE" -o build/prism_cm_test_nolv.gbc \
  -n build/prism_cm_test_nolv.sym build/character_mode_test_nolv.o     # control: the relearner's level cut
sha1sum build/prism_cm.gbc
