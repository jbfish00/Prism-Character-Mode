#!/bin/sh
# Build, then run every Character Mode test against the built ROM. Each test also has a
# --tamper negative control (must FAIL) listed after the positive runs.
cd "$(dirname "$0")/.."
PY=tools/emu_venv/bin/python3
tools/build.sh >/dev/null || exit 1
rc=0
for t in tools/tests/verify_hooks.py tools/unit_test_gate.py tools/unit_test_wildmon.py \
         tools/tests/test_select.py tools/tests/test_persist.py tools/tests/test_intro_persist.py \
         tools/tests/test_gift.py tools/tests/test_withdraw.py tools/tests/test_trade.py \
         tools/tests/test_catch_odds.py tools/tests/test_qol.py tools/tests/test_roster.py \
         tools/tests/test_legend.py tools/tests/test_vanilla_equiv.py tools/tests/test_live_catch.py tools/tests/test_fieldmenu.py tools/tests/test_live_species.py tools/tests/test_live_expshare.py tools/tests/test_egg.py tools/tests/test_linktrade.py tools/tests/test_live_obstacles.py; do
  printf '%-45s ' "$t"
  if $PY "$t" >/tmp/prism_test.$$ 2>&1; then echo PASS; else echo FAIL; tail -5 /tmp/prism_test.$$; rc=1; fi
done
echo "--- negative controls (each must FAIL):"
for t in tools/tests/verify_hooks.py tools/tests/test_select.py tools/tests/test_persist.py tools/tests/test_gift.py \
         tools/tests/test_withdraw.py tools/tests/test_trade.py tools/tests/test_catch_odds.py tools/tests/test_qol.py tools/tests/test_roster.py \
         tools/tests/test_legend.py tools/tests/test_vanilla_equiv.py tools/tests/test_live_catch.py tools/tests/test_fieldmenu.py tools/tests/test_live_species.py tools/tests/test_live_expshare.py tools/tests/test_egg.py tools/tests/test_linktrade.py tools/tests/test_live_obstacles.py; do
  printf '%-45s ' "$t --tamper"
  if $PY "$t" --tamper >/dev/null 2>&1; then echo "UNEXPECTED PASS"; rc=1; else echo "fails as it should"; fi
done
rm -f /tmp/prism_test.$$
exit $rc
