# Parallel 6-core runner for T7 · L-meta-909 (Antigravity-Win).
# Runs s909s.py at s=6 across glucose4, maplechrono, minisat22, and og-count splits (1,2,3, then 4,5,6 with cadical195).
import itertools, sys, time, json
from multiprocessing import Pool
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

E = [
    (0, 1), (1, 2), (2, 3), (3, 4), (4, 0),
    (0, 5), (1, 6), (2, 7), (3, 8), (4, 9),
    (5, 7), (7, 9), (9, 6), (6, 8), (8, 5),
]
N = 10


def get_pts():
    adj = [[False] * N for _ in range(N)]
    for a, b in E:
        adj[a][b] = adj[b][a] = True
    maxind = []
    for m in range(1 << N):
        S = [i for i in range(N) if (m >> i) & 1]
        if any(adj[a][b] for a, b in itertools.combinations(S, 2)):
            continue
        if all(any(adj[a][w] for a in S) for w in range(N) if not ((m >> w) & 1)):
            maxind.append(m)
    pts = [(m, False) for m in maxind] + [
        (m | (1 << w), True) for m in maxind for w in range(N) if not ((m >> w) & 1)
    ]
    return maxind, pts


def build_s909s(s, og_exact=None):
    _, pts = get_pts()
    pool = IDPool()
    cl = []

    def v(*k):
        return pool.id(k)

    def OR_def(out, lits):
        cl.append([-out] + lits)
        for l in lits:
            cl.append([out, -l])

    def AND2(out, a, b):
        cl.append([-out, a])
        cl.append([-out, b])
        cl.append([out, -a, -b])

    for i in range(s):
        for side in 'LR':
            for P, (m, _) in enumerate(pts):
                terms = []
                for x in range(N):
                    if (m >> x) & 1:
                        terms.append(v(side, i, 'var', x))
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

    for x in range(N):
        bs = []
        for i in range(s):
            b = v('bare', i, x)
            OR_def(b, [v('L', i, 'var', x), v('R', i, 'var', x)])
            bs.append(b)
        cl.extend(CardEnc.atmost(lits=bs, bound=2, vpool=pool, encoding=EncType.seqcounter).clauses)

    # Sound symmetry breaking from s909s.py
    for i in range(s):
        for side in 'LR':
            cl.append([v(side, i, 'var', x) for x in range(N)] + [v(side, i, 'gate', j) for j in range(i)])
        users = [v(side, k, 'gate', i) for k in range(i + 1, s) for side in 'LR']
        cl.append(users + [v('og', i)])
    cl.append([v('og', s - 1)])
    cl.append([v('L', 0, 'var', 0)])

    if og_exact is not None:
        og_lits = [v('og', i) for i in range(s)]
        cl.extend(CardEnc.equals(lits=og_lits, bound=og_exact, vpool=pool, encoding=EncType.seqcounter).clauses)

    return pool, cl, pts, v


def verify_circuit(C, pts):
    def ev(U):
        val = []
        for g in C['gates']:
            sl = any((U >> x) & 1 for x in g['Lvars']) or any(val[j] for j in g['Lgates'])
            sr = any((U >> x) & 1 for x in g['Rvars']) or any(val[j] for j in g['Rgates'])
            val.append(sl and sr)
        return any(val[j] for j in C['out'])

    pts_ok = all(ev(m) == t for m, t in pts)
    bare = [sum(1 for g in C['gates'] if x in g['Lvars'] or x in g['Rvars']) for x in range(N)]
    wf = all(
        all(0 <= j < i for j in g['Lgates']) and all(0 <= j < i for j in g['Rgates'])
        for i, g in enumerate(C['gates'])
    )
    return pts_ok and wf and all(b <= 2 for b in bare), bare


def run_job(job):
    label, s, solver_name, og_exact = job
    pool, cl, pts, v = build_s909s(s, og_exact=og_exact)
    t0 = time.time()
    with Solver(name=solver_name, bootstrap_with=cl) as so:
        ok = so.solve()
        dt = time.time() - t0
        res = {
            'label': label,
            's': s,
            'solver': solver_name,
            'og_exact': og_exact,
            'vars': pool.top,
            'clauses': len(cl),
            'status': 'SAT' if ok else 'UNSAT',
            'time': round(dt, 2),
        }
        if ok:
            M = set(l for l in so.get_model() if l > 0)
            C = {'size': s, 'gates': [], 'out': [i for i in range(s) if v('og', i) in M]}
            for i in range(s):
                g = {}
                for side in 'LR':
                    g[side + 'vars'] = [x for x in range(N) if v(side, i, 'var', x) in M]
                    g[side + 'gates'] = [j for j in range(i) if v(side, i, 'gate', j) in M]
                C['gates'].append(g)
            valid, bare = verify_circuit(C, pts)
            assert valid, f'Invalid circuit extracted! bare={bare}'
            res['circuit'] = C
            res['verify_115'] = valid
            res['bare'] = bare
        return res


def self_test():
    r = run_job(('selftest_s7', 7, 'cadical195', None))
    assert r['status'] == 'SAT' and r['verify_115'], f's=7 self-test failed: {r}'
    print(f"Self-test s=7 passed in {r['time']}s (115 pts verified, bare={r['bare']})", flush=True)


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    log_path = sys.argv[2] if len(sys.argv) > 2 else 't7_results.jsonl'

    # Main 6-core jobs: exact 6 requested in T7 first, followed by og=4,5,6 to complete the partition
    jobs = [
        ('s6_glucose4', 6, 'glucose4', None),
        ('s6_maplechrono', 6, 'maplechrono', None),
        ('s6_minisat22', 6, 'minisat22', None),
        ('s6_og1_cadical195', 6, 'cadical195', 1),
        ('s6_og2_cadical195', 6, 'cadical195', 2),
        ('s6_og3_cadical195', 6, 'cadical195', 3),
        ('s6_og4_cadical195', 6, 'cadical195', 4),
        ('s6_og5_cadical195', 6, 'cadical195', 5),
        ('s6_og6_cadical195', 6, 'cadical195', 6),
    ]

    print(f'Launching {len(jobs)} jobs across {workers} cores...', flush=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        p = Pool(workers)
        try:
            for r in p.imap_unordered(run_job, jobs):
                f.write(json.dumps(r) + '\n')
                f.flush()
                print(
                    f"[DONE] {r['label']} -> {r['status']} ({r['time']}s, vars={r['vars']}, clauses={r['clauses']})",
                    flush=True,
                )
                if r['status'] == 'SAT':
                    print('SAT CIRCUIT JSON:', json.dumps(r['circuit']), flush=True)
                    p.terminate()
                    break
        finally:
            p.close()
            p.join()
    print('All T7 runs finished.', flush=True)
