import itertools, json, os, queue, subprocess, sys, threading, time
from pysat.formula import IDPool

WORKDIR = os.path.dirname(os.path.abspath(__file__))
CNF_DIR = os.path.join(WORKDIR, "og_cnfs")
RESULTS_PATH = os.path.join(WORKDIR, "assigned_cadical_results.jsonl")
KISSAT_RESULTS_PATH = os.path.join(WORKDIR, "og_split_results.jsonl")
FOUND_PATH = os.path.join(WORKDIR, "FOUND_6.json")

E = [(0,1),(1,2),(2,3),(3,4),(4,0),(0,5),(1,6),(2,7),(3,8),(4,9),(5,7),(7,9),(9,6),(6,8),(8,5)]
n = 10
adj = [[False]*n for _ in range(n)]
for a, b in E:
    adj[a][b] = adj[b][a] = True

maxind = []
for m in range(1 << n):
    S = [i for i in range(n) if m >> i & 1]
    if any(adj[a][b] for a, b in itertools.combinations(S, 2)):
        continue
    if all(any(adj[a][w] for a in S) for w in range(n) if not m >> w & 1):
        maxind.append(m)
pts = [(m, False) for m in maxind] + [(m | (1 << w), True) for m in maxind for w in range(n) if not m >> w & 1]

def build_pool(s=6):
    pool = IDPool()
    def v(*k): return pool.id(k)
    for i in range(s):
        for side in 'LR':
            for P, (m, _) in enumerate(pts):
                for x in range(n):
                    if m >> x & 1: v(side, i, 'var', x)
                for j in range(i):
                    v('t', side, i, j, P); v(side, i, 'gate', j); v('g', j, P)
                v('s', side, i, P)
        for P in range(len(pts)):
            v('g', i, P); v('s', 'L', i, P); v('s', 'R', i, P)
    for P, (m, val) in enumerate(pts):
        for i in range(s):
            v('to', i, P); v('og', i); v('g', i, P)
        v('out', P)
    for x in range(n):
        for i in range(s):
            v('bare', i, x); v('L', i, 'var', x); v('R', i, 'var', x)
    return pool

def verify_circuit(C):
    def ev(U):
        val = []
        for i, g in enumerate(C['gates']):
            sl = any(U >> x & 1 for x in g['Lvars']) or any(val[j] for j in g['Lgates'])
            sr = any(U >> x & 1 for x in g['Rvars']) or any(val[j] for j in g['Rgates'])
            val.append(sl and sr)
        return any(val[j] for j in C['out'])
    ok_pts = all(ev(m) == t for m, t in pts)
    bare = [sum(1 for g in C['gates'] if x in g['Lvars'] or x in g['Rvars']) for x in range(n)]
    ok_bare = all(b <= 2 for b in bare)
    return ok_pts, bare, ok_bare

def decode_dimacs_model(stdout, pool, s=6):
    M = set()
    for line in stdout.splitlines():
        if line.startswith('v '):
            for tok in line[2:].split():
                lit = int(tok)
                if lit > 0:
                    M.add(lit)
    def v(*k): return pool.id(k)
    C = {'size': s, 'gates': [], 'out': [i for i in range(s) if v('og', i) in M]}
    for i in range(s):
        g = {}
        for side in 'LR':
            g[side + 'vars'] = [x for x in range(n) if v(side, i, 'var', x) in M]
            g[side + 'gates'] = [j for j in range(i) if v(side, i, 'gate', j) in M]
        C['gates'].append(g)
    return C

def get_done_masks():
    done = set()
    for path in (RESULTS_PATH, KISSAT_RESULTS_PATH):
        if os.path.exists(path):
            with open(path) as f:
                for line in f:
                    line = line.strip()
                    if not line: continue
                    try:
                        r = json.loads(line)
                        if r.get("status") in ("SAT", "UNSAT"):
                            done.add(r["mask_str"])
                    except Exception:
                        pass
    return done

def main():
    nworkers = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    pool = build_pool(6)
    # Strictly ONLY Antigravity-Mac's 4 assigned masks from TASKS.md SPLIT TABLE
    assigned = [(5,), (4, 5), (3, 4, 5), (2, 4, 5)]
    q = queue.Queue()
    for m in assigned:
        q.put(m)

    lock = threading.Lock()
    active_procs = {}
    stop_event = threading.Event()

    def kill_all():
        with lock:
            for wid, p in list(active_procs.items()):
                if p.poll() is None:
                    try: p.terminate()
                    except Exception: pass

    def worker(wid):
        while not stop_event.is_set():
            try:
                mask = q.get_nowait()
            except queue.Empty:
                return
            ms = ",".join(map(str, mask))
            if ms in get_done_masks():
                print(f"[{time.strftime('%H:%M:%S')}] W{wid} SKIP {ms} (already decided)", flush=True)
                q.task_done()
                continue
            tag = "og_" + "_".join(map(str, mask))
            cnf_path = os.path.join(CNF_DIR, f"l909_s6_{tag}.cnf")
            cmd = ["cadical", "--seed=1", cnf_path]
            t0 = time.time()
            print(f"[{time.strftime('%H:%M:%S')}] W{wid} START cadical {tag}", flush=True)
            p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            with lock:
                active_procs[wid] = p
            out, _ = p.communicate()
            dt = round(time.time() - t0, 2)
            rc = p.returncode

            status = f"EXIT_{rc}"
            circuit = None
            verify_info = None
            if rc == 10 or "s SATISFIABLE" in out:
                status = "SAT"
                circuit = decode_dimacs_model(out, pool, 6)
                ok_pts, bare, ok_bare = verify_circuit(circuit)
                verify_info = {"ok_pts": ok_pts, "bare": bare, "ok_bare": ok_bare}
            elif rc == 20 or "s UNSATISFIABLE" in out:
                status = "UNSAT"

            rec = {
                "tag": tag,
                "mask": list(mask),
                "mask_str": ms,
                "og_count": len(mask),
                "solver": "cadical 3.1.0",
                "status": status,
                "rc": rc,
                "wall_s": dt,
                "ts": time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            if verify_info is not None:
                rec["verify"] = verify_info
            if circuit is not None:
                rec["circuit"] = circuit

            with lock:
                with open(RESULTS_PATH, "a") as f:
                    f.write(json.dumps(rec) + "\n")
                print(f"[{rec['ts']}] W{wid} DONE cadical {tag}: {status} in {dt}s", flush=True)
                if status == "SAT" and circuit is not None:
                    with open(FOUND_PATH, "w") as f:
                        json.dump({"solver": f"cadical ({tag})", "wall_s": dt, "verify": verify_info, "circuit": circuit}, f, indent=2)
                    print("FOUND_CIRCUIT:", json.dumps(circuit), flush=True)
                    print("VERIFY:", verify_info, flush=True)
                    stop_event.set()
            if status == "SAT":
                kill_all()
            q.task_done()

    threads = [threading.Thread(target=worker, args=(w,), daemon=False) for w in range(nworkers)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("ALL_ASSIGNED_CADICAL_DONE", flush=True)

if __name__ == "__main__":
    main()
