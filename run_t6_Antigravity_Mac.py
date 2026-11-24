import itertools, json, os, subprocess, sys, threading, time
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType

WORKDIR = os.path.dirname(os.path.abspath(__file__))
CNF_PATH = os.path.join(WORKDIR, "l909_s6.cnf")
RESULTS_PATH = os.path.join(WORKDIR, "t6_results.jsonl")
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
    pool, cl = build_pool(6)
    print(f"Pool built: vars={pool.top}, clauses={len(cl)}, pts={len(pts)}", flush=True)

    jobs = [
        ("kissat_seed1", ["kissat", "--seed=1", CNF_PATH]),
        ("kissat_seed2", ["kissat", "--seed=2", CNF_PATH]),
        ("kissat_seed3", ["kissat", "--seed=3", CNF_PATH]),
        ("kissat_sat_seed4", ["kissat", "--sat", "--seed=4", CNF_PATH]),
        ("cadical_seed1", ["cadical", "--seed=1", CNF_PATH]),
        ("cadical_sat_seed2", ["cadical", "--sat", "--seed=2", CNF_PATH]),
        ("pysat_cadical195", [os.path.join(WORKDIR, "venv/bin/python"), os.path.join(WORKDIR, "s909s.py"), "6", "cadical195"]),
    ]

    procs = {}
    lock = threading.Lock()
    stop_event = threading.Event()
    results = []

    def kill_others(winner):
        with lock:
            for name, p in procs.items():
                if name != winner and p.poll() is None:
                    try:
                        p.terminate()
                    except Exception:
                        pass

    def worker(name, cmd):
        t0 = time.time()
        p = subprocess.Popen(cmd, cwd=WORKDIR, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        with lock:
            procs[name] = p
        out, _ = p.communicate()
        dt = round(time.time() - t0, 2)
        rc = p.returncode

        status = f"EXIT_{rc}"
        circuit = None
        verify_info = None

        if name.startswith("pysat_"):
            if "size 6 SAT" in out:
                status = "SAT"
                for line in out.splitlines():
                    if line.strip().startswith("{"):
                        circuit = json.loads(line.strip())
                        ok_pts, bare, ok_bare = verify_circuit(circuit)
                        verify_info = {"ok_pts": ok_pts, "bare": bare, "ok_bare": ok_bare}
            elif "size 6 UNSAT" in out:
                status = "UNSAT"
        else:
            if rc == 10 or "s SATISFIABLE" in out:
                status = "SAT"
                circuit = decode_dimacs_model(out, pool, 6)
                ok_pts, bare, ok_bare = verify_circuit(circuit)
                verify_info = {"ok_pts": ok_pts, "bare": bare, "ok_bare": ok_bare}
            elif rc == 20 or "s UNSATISFIABLE" in out:
                status = "UNSAT"

        rec = {
            "name": name,
            "cmd": " ".join(cmd),
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
            results.append(rec)
            with open(RESULTS_PATH, "a") as f:
                f.write(json.dumps(rec) + "\n")
            print(f"[{rec['ts']}] {name}: {status} in {dt}s", flush=True)
            if status == "SAT" and circuit is not None:
                with open(FOUND_PATH, "w") as f:
                    json.dump({"solver": name, "wall_s": dt, "verify": verify_info, "circuit": circuit}, f, indent=2)
                print("FOUND_CIRCUIT:", json.dumps(circuit), flush=True)
                print("VERIFY:", verify_info, flush=True)
                stop_event.set()
        if status == "SAT":
            kill_others(name)

    threads = []
    for name, cmd in jobs:
        t = threading.Thread(target=worker, args=(name, cmd), daemon=False)
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("ALL_DONE", flush=True)

if __name__ == "__main__":
    main()
