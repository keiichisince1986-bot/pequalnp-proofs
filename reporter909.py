# reporter909.py - no-LLM reporter for the L-meta-909 split runs (stdlib + git only).
# usage: python3 reporter909.py <agent name> [search root ...]
# Every 60 s: looks for a 6-gate SAT circuit in the local result files; if one verifies, pushes it at once
# as reports/<agent>/FOUND-6-<agent>.json to branch wip-L-meta-909 (Claude's container then submits it).
# Every 10 min: copies the result files and a solver-process snapshot to reports/<agent>/ and pushes them.
import json, os, re, shutil, subprocess, sys, time, platform
AGENT = sys.argv[1]
HOME = os.path.expanduser('~')
ROOTS = sys.argv[2:] or [os.path.join(HOME, '.gemini'), HOME]
REPO = 'https://github.com/keiichisince1986-bot/pequalnp-proofs'
CLONE = os.path.join(HOME, 'r909-' + AGENT)
NAME = re.compile(r'^(t7_.*results.*\.jsonl|og_split_results\.jsonl|assigned_cadical_results\.jsonl|.*_results\.jsonl|FOUND_6.*\.json)$')
SKIP = {'node_modules', '.git', 'AppData', 'Library', '.cache', '.npm', '.cargo', '.rustup', '.elan', '.lake', 'r909-' + AGENT}
EDGES = [(0,1),(1,2),(2,3),(3,4),(4,0),(0,5),(1,6),(2,7),(3,8),(4,9),(5,7),(7,9),(9,6),(6,8),(8,5)]
ADJ = {(a,b) for a,b in EDGES} | {(b,a) for a,b in EDGES}

def log(*a): print(time.strftime('%m-%d %H:%M:%S'), *a, flush=True)
def git(*a, check=True): return subprocess.run(['git', '-C', CLONE] + list(a), capture_output=True, text=True, check=check)

def points():
    pts = []
    for m in range(1 << 10):
        I = [v for v in range(10) if m >> v & 1]
        if any((a, b) in ADJ for a in I for b in I): continue
        if any(not any((a, w) in ADJ for a in I) for w in range(10) if w not in I): continue
        pts.append((m, False))
        for w in range(10):
            if not m >> w & 1: pts.append((m | 1 << w, True))
    return pts
PTS = points()

def verify(C):
    try:
        G = C['gates']
        if len(G) > 6 or C.get('size', len(G)) > 6: return False
        def ev(U):
            val = []
            for g in G:
                l = any(U >> x & 1 for x in g['Lvars']) or any(val[j] for j in g['Lgates'])
                r = any(U >> x & 1 for x in g['Rvars']) or any(val[j] for j in g['Rgates'])
                val.append(l and r)
            return any(val[j] for j in C['out'])
        bare = all(sum(1 for g in G if x in g['Lvars'] or x in g['Rvars']) <= 2 for x in range(10))
        return bare and all(ev(m) == t for m, t in PTS)
    except Exception:
        return False

def candidates(obj):
    if isinstance(obj, dict):
        if 'gates' in obj and 'out' in obj: yield obj
        for v in obj.values(): yield from candidates(v)
    elif isinstance(obj, list):
        for v in obj: yield from candidates(v)

def scan_files():
    found = []
    for root in ROOTS:
        if not os.path.isdir(root): continue
        for d, subs, files in os.walk(root):
            subs[:] = [s for s in subs if s not in SKIP and d.count(os.sep) - root.count(os.sep) < 9]
            for f in files:
                if NAME.match(f): found.append(os.path.join(d, f))
    return sorted(set(found))

def read_objs(p):
    try:
        txt = open(p, encoding='utf-8', errors='replace').read()
    except Exception:
        return []
    if p.endswith('.json'):
        try: return [json.loads(txt)]
        except Exception: return []
    out = []
    for line in txt.splitlines():
        try: out.append(json.loads(line))
        except Exception: pass
    return out

def push(msg):
    git('add', '-A', 'reports')
    if not git('status', '--porcelain', check=False).stdout.strip(): return
    git('commit', '-q', '-m', msg)
    for t in (2, 4, 8, 16, 32):
        if git('push', '-q', 'origin', 'HEAD:wip-L-meta-909', check=False).returncode == 0: log('pushed:', msg); return
        time.sleep(t); git('pull', '-q', '--rebase', 'origin', 'wip-L-meta-909', check=False)
    log('PUSH FAILED:', msg)

def procs():
    try:
        if platform.system() == 'Windows':
            return subprocess.run(['tasklist', '/V', '/FO', 'CSV'], capture_output=True, text=True).stdout
        return subprocess.run(['ps', '-axo', 'pid,etime,time,command'], capture_output=True, text=True).stdout
    except Exception as e:
        return str(e)

if not os.path.isdir(os.path.join(CLONE, '.git')):
    subprocess.run(['git', 'clone', '-q', '--depth', '20', '--single-branch', '-b', 'wip-L-meta-909', REPO, CLONE], check=True)
OUT = os.path.join(CLONE, 'reports', AGENT); os.makedirs(OUT, exist_ok=True)
log('reporter for', AGENT, 'roots', ROOTS, 'points', len(PTS))
files, last_scan, last_report, sent = [], 0, 0, set()
while True:
    now = time.time()
    if now - last_scan > 1800 or not files:
        files = scan_files(); last_scan = now; log('watching', len(files), 'files:', *files)
    for p in files:
        for o in read_objs(p):
            for C in candidates(o):
                key = json.dumps(C, sort_keys=True)
                if key in sent or not verify(C): continue
                sent.add(key)
                git('pull', '-q', '--rebase', 'origin', 'wip-L-meta-909', check=False)
                json.dump({'size': len(C['gates']), 'gates': C['gates'], 'out': C['out']}, open(os.path.join(OUT, 'FOUND-6-%s.json' % AGENT), 'w'))
                push('%s: FOUND 6-gate circuit (verified on %d points), from %s' % (AGENT, len(PTS), os.path.basename(p)))
    if now - last_report > 600:
        last_report = now
        git('pull', '-q', '--rebase', 'origin', 'wip-L-meta-909', check=False)
        for p in files:
            try: shutil.copy(p, os.path.join(OUT, re.sub(r'[^A-Za-z0-9_.-]', '_', os.path.relpath(p, HOME))[-120:]))
            except Exception: pass
        open(os.path.join(OUT, 'processes.txt'), 'w', encoding='utf-8').write(time.strftime('%Y-%m-%d %H:%M:%S local\n') + '\n'.join(l for l in procs().splitlines() if re.search(r'kissat|cadical|python|PID|Image', l, re.I)))
        push('%s: auto report %s' % (AGENT, time.strftime('%H:%M')))
    time.sleep(60)
