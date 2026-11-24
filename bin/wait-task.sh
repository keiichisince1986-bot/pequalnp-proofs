#!/usr/bin/env bash
# Wait until TASKS.md on the claims branch has a task with status todo meant for NAME (or for any).
# Usage, from inside a clone of keiichisince1986-bot/pequalnp-proofs:
#   bash bin/wait-task.sh Antigravity-Mac        (or fetch this file from the claims branch first)
# Prints the matching task headers and exits 0. Exits 2 after MAXMIN minutes (default 25) so a
# caller with a time limit can simply run it again.
NAME="$1"; MAXMIN="${2:-25}"; INTERVAL="${3:-60}"
[ -n "$NAME" ] || { echo "usage: wait-task.sh NAME [maxminutes] [interval]"; exit 1; }
end=$(( $(date +%s) + MAXMIN * 60 ))
while :; do
  git fetch -q origin claims 2>/dev/null
  hits=$(git show origin/claims:TASKS.md 2>/dev/null | grep -E "^## T[0-9]+ .*status: todo( \(meant for ($NAME|any)\))?\s*$|^## T[0-9]+ .*status: todo \(meant for ($NAME|any)\)")
  if [ -n "$hits" ]; then echo "$hits"; exit 0; fi
  [ "$(date +%s)" -ge "$end" ] && { echo "no task for $NAME yet; run me again"; exit 2; }
  sleep "$INTERVAL"
done
