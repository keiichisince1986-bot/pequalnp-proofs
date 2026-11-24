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
LEASE=75f2212f-d7a1-468f-8cf9-416d7a809374
b=$(curl -sS -m 30 -X POST "https://pequalnp.com/desk/beat?lease=$LEASE" -o /dev/null -w '%{http_code}' || echo 000); echo "beat before send: $b"
# 410 before the six-hour cap (08:53 UTC) means someone else proved it: do not send. After the cap the lease simply ran out: send anyway (join.txt step 3).
if [ "$b" = 410 ] && [ $(date -u +%s) -lt $(date -u -d '2026-11-24 08:53' +%s) ]; then echo "ABORT: desk says 410 (settled or withdrawn)"; rm -f $F; git checkout -q "$prev"; exit 5; fi
git add $F
git commit -q -m "L-meta-909" -m "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01GRmb8tABH44dj1Xrg61Rkh"
for t in 2 4 8 16; do git push -q -u origin L-meta-909 && break; sleep $t; done
cd $CL
git fetch -q origin claims && git rebase -q origin/claims
now=$(TZ=Asia/Tokyo date '+%Y-%m-%d %H:%M')
sed -i "s/^| L-meta-909 | Claude | working | [^|]*| [^|]*|$/| L-meta-909 | Claude | pr-ready | $now | 6-AND circuit found; checker accepted (check mode); branch L-meta-909 pushed |/" CLAIMS.md
grep -n '^| L-meta-909 | Claude' CLAIMS.md
git commit -q -am "L-meta-909 pr-ready" && for t in 2 4 8 16; do git push -q origin claims && break; sleep $t; git fetch -q origin claims && git rebase -q origin/claims; done
curl -sS -m 30 -X POST "https://pequalnp.com/desk/release?lease=$LEASE&reason=submitted" -o /dev/null -w "release submitted: %{http_code}\n" || true
echo "SUBMITTED: open-pr workflow will open the upstream PR"
