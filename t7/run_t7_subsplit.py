# Single-core sub-split helper for T7 · L-meta-909 (Antigravity-Win).
# Runs on the 6th core freed after |og|=4,5,6 finished UNSAT, testing exact og bitmasks for |og| in {1, 2, 3}.
# Uses the 100% sound unit symmetry break: when og_4 == False, gate 4 must be read by gate 5, and since
# L_5 <-> R_5 is an exact symmetry of gate 5 (i=5 > 0), we may fix v('L', 5, 'gate', 4) = True.
import itertools, sys, os, time, json
from pysat.solvers import Solver

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_t7 import build_s909s, verify_circuit, N


def run_mask(og_tuple, solver_name='cadical195'):
    s = 6
    pool, cl, pts, v = build_s909s(s, og_exact=None)
    for i in range(s):
        cl.append([v('og', i)] if og_tuple[i] else [-v('og', i)])
    # Sound L_5 <-> R_5 symmetry break when og_4 is False:
    if not og_tuple[4]:
        cl.append([v('L', 5, 'gate', 4)])

    t0 = time.time()
    with Solver(name=solver_name, bootstrap_with=cl) as so:
        ok = so.solve()
        dt = time.time() - t0
        bit_str = ''.join(str(b) for b in og_tuple)
        res = {
            'label': f's6_ogmask_{bit_str}',
            'og_count': sum(og_tuple),
            'og_mask': bit_str,
            'solver': solver_name,
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
            assert valid, f'Invalid circuit! bare={bare}'
            res['circuit'] = C
            res['verify_115'] = valid
            res['bare'] = bare
        return res


if __name__ == '__main__':
    log_path = sys.argv[1] if len(sys.argv) > 1 else 't7_subsplit_results.jsonl'
    # Order: |og|=3 (10 masks, most constrained on I), then |og|=2 (5 masks), then |og|=1 (1 mask)
    masks = []
    for k in [2, 1, 0]:  # number of 1s among og_0..og_4 (since og_5 == 1, total |og| = k + 1)
        for comb in itertools.combinations(range(5), k):
            tup = tuple(1 if i in comb else 0 for i in range(5)) + (1,)
            masks.append(tup)

    print(f'Running {len(masks)} exact og-mask subsplits on 1 core...', flush=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        for tup in masks:
            r = run_mask(tup)
            f.write(json.dumps(r) + '\n')
            f.flush()
            print(f"[SUBSPLIT] {r['label']} (|og|={r['og_count']}) -> {r['status']} ({r['time']}s)", flush=True)
            if r['status'] == 'SAT':
                print('SAT CIRCUIT JSON:', json.dumps(r['circuit']), flush=True)
                sys.exit(0)
    print('All 16 subsplits for |og| in {1, 2, 3} finished UNSAT!', flush=True)
