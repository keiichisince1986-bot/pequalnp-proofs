import itertools, json, os, queue, subprocess, sys, threading, time
from pysat.formula import IDPool, CNF
from pysat.card import CardEnc, EncType

WORKDIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(WORKDIR, "og_split_results.jsonl")
FOUND_PATH = os.path.join(WORKDIR, "FOUND_6.json")
CNF_DIR = os.path.join(WORKDIR, "og_cnfs")
os.makedirs(CNF_DIR, exist_ok=True)

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

def build_base(s=6):
    pool = IDPool()
    cl = []
    def v(*k): return pool.id(k)
    def OR_def(out, lits):
        cl.append([-out] + lits)
        for l in lits: cl.append([out, -l])
    def AND2(out, a, b):
        cl.append([-out, a]); cl.append([-out, b]); cl.append([out, -a, -b])
    for i in range(s):
        for side in 'LR':
            for P, (m, _) in enumerate(pts):
                terms = []
                for x in range(n):
                    if m >> x & 1: terms.append(v(side, i, 'var', x))
                for j in range(i):
                    t = v('t', side, i, j, P)
                    AND2(t, v(side, i, 'gate', j), v('g', j, P))
                    terms.append(t)
                OR_def(v('s', side, i, P), terms)
        for P in range(len(pts)):
            AND2(v('g', i, P), v('s', 'L', i, P), v('s', 'R', i, P))
    for P, (m, val) in enumerate(pts):
        terms = []
        for i in range(s):
            t = v('to', i, P)
            AND2(t, v('og', i), v('g', i, P))
            terms.append(t)
        o = v('out', P)
        OR_def(o, terms)
        cl.append([o] if val else [-o])
    for x in range(n):
        bs = []
        for i in range(s):
            b = v('bare', i, x)
            OR_def(b, [v('L', i, 'var', x), v('R', i, 'var', x)])
            bs.append(b)
        cl.extend(CardEnc.atmost(lits=bs, bound=2, vpool=pool, encoding=EncType.seqcounter).clauses)
    for i in range(s):
        for side in 'LR':
            cl.append([v(side, i, 'var', x) for x in range(n)] + [v(side, i, 'gate', j) for j in range(i)])
        users = [v(side, k, 'gate', i) for k in range(i + 1, s) for side in 'LR']
        cl.append(users + [v('og', i)])
    cl.append([v('og', s - 1)])
    cl.append([v('L', 0, 'var', 0)])
    return pool, cl

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

def main():
    nworkers = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    pool, base_cl = build_base(6)
    og_vars = [pool.id(('og', i)) for i in range(6)]
    print(f"Base CNF built: vars={pool.top}, clauses={len(base_cl)}, og_vars={og_vars}", flush=True)

    # Load already completed masks so script is safely resumable
    done = set()
    if os.path.exists(RESULTS_PATH):
        with open(RESULTS_PATH) as f:
            for line in f:
                line = line.strip()
                if not line: continue
                r = json.loads(line)
                if r.get("status") in ("SAT", "UNSAT"):
                    done.add(r["mask_str"])

    # Order:
    # 1) |og|=1: (5,)
    # 2) |og|=3 (10 masks, highest gate indices first -> often fastest to refute/solve)
    # 3) |og|=2 (5 masks, highest gate indices first)
    # 4) |og|=4, 5, 6 (16 masks, independent kissat re-verification of Antigravity-Win's UNSAT)
    masks_1 = [(5,)]
    masks_3 = sorted([tuple(sorted(c + (5,))) for c in itertools.combinations(range(5), 2)], reverse=True)
    masks_2 = sorted([tuple(sorted((i, 5))) for i in range(5)], reverse=True)
    masks_456 = []
    for k in (5, 4, 3):  # plus gate 5 -> |og| = 6, 5, 4
        masks_456.extend(sorted([tuple(sorted(c + (5,))) for c in itertools.combinations(range(5), k)], reverse=True))

    # Interleave first 4 workers across |og|=1, |og|=2, |og|=3 immediately!
    ordered = [masks_1[0], masks_2[0], masks_3[0], masks_3[1]] + masks_3[2:] + masks_2[1:] + masks_456

    q = queue.Queue()
    for m in ordered:
        ms = ",".join(map(str, m))
        if ms not in done:
            q.put(m)

    print(f"Queued {q.qsize()} og-mask jobs ({len(done)} already done), workers={nworkers}", flush=True)

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
            tag = "og_" + "_".join(map(str, mask))
            cnf_path = os.path.join(CNF_DIR, f"l909_s6_{tag}.cnf")
            extra = [[og_vars[i]] if i in mask else [-og_vars[i]] for i in range(6)]
            CNF(from_clauses=base_cl + extra).to_file(cnf_path)

            t0 = time.time()
            cmd = ["kissat", "--seed=1", cnf_path]
            print(f"[{time.strftime('%H:%M:%S')}] W{wid} START {tag} (|og|={len(mask)})", flush=True)
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
                "solver": "kissat 4.0.4",
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
                print(f"[{rec['ts']}] W{wid} DONE {tag} (|og|={len(mask)}): {status} in {dt}s", flush=True)
                if status == "SAT" and circuit is not None:
                    with open(FOUND_PATH, "w") as f:
                        json.dump({"solver": f"kissat ({tag})", "wall_s": dt, "verify": verify_info, "circuit": circuit}, f, indent=2)
                    print("FOUND_CIRCUIT:", json.dumps(circuit), flush=True)
                    print("VERIFY:", verify_info, flush=True)
                    stop_event.set()
            if status == "SAT":
                kill_all()
            q.task_done()

    threads = [threading.Thread(target=worker, args=(w,), daemon=False) for w in range(nworkers)]
    for t in threads: t.start()
    for t in threads: t.join()
    print("ALL_OG_SPLITS_DONE", flush=True)

if __name__ == "__main__":
    main()
