#!/bin/bash
# Watches for a 6-gate L-meta-909 circuit (local solver logs, or FOUND-6*.json pushed to wip-L-meta-909) and submits it at once.
S=/tmp/claude-0/-home-user/947ad36e-b637-54f5-b685-f17157b15fca/scratchpad; G=$S/gen; R=/home/user/pequalnp-proofs
CL=/tmp/claude-0/-home-user-Delivery-Control/947ad36e-b637-54f5-b685-f17157b15fca/scratchpad/claims
L=$G/autosubmit.log; tried=" "; lastwip=""
log(){ echo "$(TZ=Asia/Tokyo date '+%m-%d %H:%M:%S') $*" >> $L; }
try(){ # $1 = candidate json file
  h=$(sha256sum "$1" | cut -c1-16); case "$tried" in *" $h "*) return 1;; esac; tried="$tried$h "
  python3 -c "
import json,sys; c=json.load(open(sys.argv[1]))
c=c.get('circuit',c); c={'size':len(c['gates']),'gates':c['gates'],'out':c['out']}
assert c['size']<=6; json.dump(c,open(sys.argv[1],'w'))" "$1" || { log "bad json $1"; return 1; }
  (cd $CL && git fetch -q origin claims && git show origin/claims:CLAIMS.md | grep -qE '^\| L-meta-909 \| [^|]* \| (pr-ready|submitted|accepted)') && { log "already pr-ready by someone; stop"; exit 0; }
  log "submitting $1"; if $G/submit909.sh "$1" >> $L 2>&1; then log "SUBMITTED OK"; exit 0; else log "submit failed for $1"; fi
}
log "start"
while true; do
  for f in $S/s909/masks.log $S/s909/r6s_*.log $S/s909/r6_*.log; do
    [ -f "$f" ] || continue
    grep -oE '\{"size": 6, "gates": .*"out": \[[0-9, ]*\]\}' "$f" 2>/dev/null | while read -r j; do echo "$j" > $G/found_local_$(echo "$j" | sha256sum | cut -c1-8).json; done
  done
  w=$(cd $R && git ls-remote origin refs/heads/wip-L-meta-909 2>/dev/null | cut -c1-40)
  if [ -n "$w" ] && [ "$w" != "$lastwip" ]; then lastwip=$w
    (cd $R && git fetch -q origin +refs/heads/wip-L-meta-909:refs/remotes/origin/wip-L-meta-909) || true
    for p in $(cd $R && git ls-tree -r --name-only origin/wip-L-meta-909 | grep -E '(^|/)FOUND[-_]6[^/]*\.json$'); do
      (cd $R && git show "origin/wip-L-meta-909:$p") > "$G/found_wip_$(echo $p | tr '/' '_')"
    done
  fi
  for j in $G/found_*.json; do [ -f "$j" ] && try "$j"; done
  sleep 60
done
