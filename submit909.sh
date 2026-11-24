#!/bin/bash
# One-shot submission for L-meta-909: circuit JSON -> Lean file -> checker (check mode) -> branch push -> CLAIMS pr-ready.
# usage: submit909.sh circuit.json [statement.txt]      DRY=1 stops after the checker and restores the previous branch.
set -euo pipefail
S=/tmp/claude-0/-home-user/947ad36e-b637-54f5-b685-f17157b15fca/scratchpad
R=/home/user/pequalnp-proofs
CL=/tmp/claude-0/-home-user-Delivery-Control/947ad36e-b637-54f5-b685-f17157b15fca/scratchpad/claims
J=$(realpath "$1"); ST=$(realpath "${2:-$S/stmt909.txt}"); F=lean/PEqualNP/Outside/L_meta_909.lean
python3 $S/gen/gen909.py "$J" "$ST" $S/gen/L_meta_909.lean
cd $R
prev=$(git rev-parse --abbrev-ref HEAD)
git fetch -q upstream main
if git cat-file -e upstream/main:$F 2>/dev/null; then echo "ABORT: upstream main already has $F"; exit 4; fi
git checkout -q -B L-meta-909 upstream/main
cp $S/gen/L_meta_909.lean $F
set +e; node tools/check-lean.mjs $F "$ST" check > $S/gen/check909.log 2>&1; rc=$?; set -e
tail -3 $S/gen/check909.log | cut -c1-300
if [ $rc -ne 0 ]; then echo "CHECK FAILED rc=$rc"; rm -f $F; git checkout -q "$prev"; exit $rc; fi
if [ "${DRY:-0}" = 1 ]; then echo "DRY RUN OK"; rm -f $F; git checkout -q "$prev"; git branch -q -D L-meta-909; exit 0; fi
git add $F
git commit -q -m "L-meta-909: Petersen graph circuit with at most 6 AND gates" -m "Explicit circuit found by SAT exact synthesis; correctness by decide +kernel over all 10-bit inputs." -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GRmb8tABH44dj1Xrg61Rkh"
for t in 2 4 8 16; do git push -q -u origin L-meta-909 && break; sleep $t; done
cd $CL
git fetch -q origin claims && git rebase -q origin/claims
now=$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M')
sed -i "s/^| L-meta-909 | Claude | working | [^|]*| [^|]*|$/| L-meta-909 | Claude | pr-ready | $now | 6-AND circuit found; checker accepted (check mode); branch L-meta-909 pushed |/" CLAIMS.md
grep -n '^| L-meta-909 | Claude' CLAIMS.md
git commit -q -am "L-meta-909 pr-ready" && for t in 2 4 8 16; do git push -q origin claims && break; sleep $t; git fetch -q origin claims && git rebase -q origin/claims; done
echo "SUBMITTED: open-pr workflow will open the upstream PR"
