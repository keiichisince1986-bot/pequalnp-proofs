# Parallel 6-core exact-mask + cube partition for remaining T7 cases |og| in {1, 2, 3} (Antigravity-Win).
# Already proved UNSAT: s=1..4, |og|=6 (4.35s), |og|=5 (361.6s), |og|=4 (4992.1s),
# and |og|=3 masks 110001 (193.0s) & 101001 (366.4s).
# Deduplicates identical (mask, target) rows in pts (115 -> 85 unique rows, 100% logically equivalent)
# and verifies any SAT model on all 115 original points + bare counts <= 2.
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
    pts_115 = [(m, False) for m in maxind] + [
        (m | (1 << w), True) for m in maxind for w in range(N) if not ((m >> w) & 1)
    ]
    seen = set()
    pts_unique = []
    for item in pts_115:
        if item not in seen:
            seen.add(item)
            pts_unique.append(item)
    return pts_115, pts_unique


def build_cnf(s, og_tuple=None, cube_g3=None):
    pts_115, pts = get_pts()
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

    if og_tuple is not None:
        for i in range(s):
            cl.append([v('og', i)] if og_tuple[i] else [-v('og', i)])
        # Sound L_{s-1} <-> R_{s-1} symmetry break when og_{s-2} == 0:
        if not og_tuple[s - 2]:
            cl.append([v('L', s - 1, 'gate', s - 2)])

    if cube_g3 is not None:
        l_g3, r_g3 = cube_g3
        cl.append([v('L', s - 1, 'gate', s - 3)] if l_g3 else [-v('L', s - 1, 'gate', s - 3)])
        cl.append([v('R', s - 1, 'gate', s - 3)] if r_g3 else [-v('R', s - 1, 'gate', s - 3)])

    return pool, cl, pts_115, pts, v


def verify_115(C, pts_115):
    def ev(U):
        val = []
        for g in C['gates']:
            sl = any((U >> x) & 1 for x in g['Lvars']) or any(val[j] for j in g['Lgates'])
            sr = any((U >> x) & 1 for x in g['Rvars']) or any(val[j] for j in g['Rgates'])
            val.append(sl and sr)
        return any(val[j] for j in C['out'])

    pts_ok = all(ev(m) == t for m, t in pts_115)
    bare = [sum(1 for g in C['gates'] if x in g['Lvars'] or x in g['Rvars']) for x in range(N)]
    wf = all(
        all(0 <= j < i for j in g['Lgates']) and all(0 <= j < i for j in g['Rgates'])
        for i, g in enumerate(C['gates'])
    )
    return pts_ok and wf and all(b <= 2 for b in bare), bare


def worker(job):
    label, s, og_tuple, cube_g3, solver_name = job
    pool, cl, pts_115, pts_uniq, v = build_cnf(s, og_tuple=og_tuple, cube_g3=cube_g3)
    t0 = time.time()
    with Solver(name=solver_name, bootstrap_with=cl) as so:
        ok = so.solve()
        dt = time.time() - t0
        res = {
            'label': label,
            's': s,
            'og_count': sum(og_tuple) if og_tuple else None,
            'og_mask': ''.join(str(b) for b in og_tuple) if og_tuple else None,
            'cube_g3': cube_g3,
            'solver': solver_name,
            'unique_pts': len(pts_uniq),
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
            valid, bare = verify_115(C, pts_115)
            assert valid, f'Verification failed! bare={bare}'
            res['circuit'] = C
            res['verify_115'] = valid
            res['bare'] = bare
        return res


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    log_path = sys.argv[2] if len(sys.argv) > 2 else 't7_resume_results.jsonl'

    pts_115, pts_uniq = get_pts()
    print(f'Original pts: {len(pts_115)}, deduplicated unique pts: {len(pts_uniq)}', flush=True)

    already_unsat = {'110001', '101001'}
    jobs = []
    # Remaining 8 masks of |og| = 3
    for comb in itertools.combinations(range(5), 2):
        tup = tuple(1 if i in comb else 0 for i in range(5)) + (1,)
        bstr = ''.join(str(b) for b in tup)
        if bstr not in already_unsat:
            jobs.append((f's6_ogmask_{bstr}', 6, tup, None, 'cadical195'))

    # All 5 masks of |og| = 2
    for comb in itertools.combinations(range(5), 1):
        tup = tuple(1 if i in comb else 0 for i in range(5)) + (1,)
        bstr = ''.join(str(b) for b in tup)
        jobs.append((f's6_ogmask_{bstr}', 6, tup, None, 'cadical195'))

    # |og| = 1 (000001) partitioned into 4 disjoint exhaustive unit-clause cubes on gate 3 -> gate 5
    tup1 = (0, 0, 0, 0, 0, 1)
    for l3 in (0, 1):
        for r3 in (0, 1):
            jobs.append((f's6_ogmask_000001_g3_{l3}{r3}', 6, tup1, (l3, r3), 'cadical195'))

    print(f'Launching {len(jobs)} disjoint jobs covering all remaining |og| in {{1,2,3}} across {workers} cores...', flush=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        p = Pool(workers)
        try:
            for r in p.imap_unordered(worker, jobs):
                f.write(json.dumps(r) + '\n')
                f.flush()
                print(
                    f"[DONE] {r['label']} (|og|={r['og_count']}) -> {r['status']} "
                    f"({r['time']}s, vars={r['vars']}, clauses={r['clauses']})",
                    flush=True,
                )
                if r['status'] == 'SAT':
                    print('SAT CIRCUIT JSON:', json.dumps(r['circuit']), flush=True)
                    p.terminate()
                    break
        finally:
            p.close()
            p.join()
    print('ALL REMAINING |og| in {1, 2, 3} JOBS COMPLETED!', flush=True)
