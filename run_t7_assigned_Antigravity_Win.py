# Exact 4-set assignment for Antigravity-Win from TASKS.md SPLIT TABLE (L-meta-909, s = 6):
# Assigned sets: {1,2,5}, {1,3,5}, {1,4,5}, {2,3,5}.
# Uses 6 cores:
#   Core 1: {1,2,5} (cadical195)
#   Core 2: {1,3,5} (cadical195)
#   Core 3: {2,3,5} (cadical195)
#   Core 4: {1,4,5} full (cadical195)
#   Core 5: {1,4,5} branch A: gate 5 reads gate 4 (WLOG on L_5 by L_5 <-> R_5 symmetry)
#   Core 6: {1,4,5} branch B: gate 5 does not read gate 4 on either side
import sys, os, time, json
from multiprocessing import Pool
from pysat.solvers import Solver

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_t7_resume import build_cnf, verify_115, N


def run_assigned_job(job):
    label, og_set, extra_mode = job
    s = 6
    og_tuple = tuple(1 if i in og_set else 0 for i in range(s))
    pool, cl, pts_115, pts_uniq, v = build_cnf(s, og_tuple=og_tuple, cube_g3=None)
    if extra_mode == 'g5_reads_g4':
        cl.append([v('L', 5, 'gate', 4)])
    elif extra_mode == 'g5_no_g4':
        cl.append([-v('L', 5, 'gate', 4)])
        cl.append([-v('R', 5, 'gate', 4)])

    t0 = time.time()
    with Solver(name='cadical195', bootstrap_with=cl) as so:
        ok = so.solve()
        dt = time.time() - t0
        res = {
            'label': label,
            'og_set': sorted(og_set),
            'extra_mode': extra_mode,
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
    log_path = sys.argv[1] if len(sys.argv) > 1 else 't7_assigned_results.jsonl'
    jobs = [
        ('og_{1,2,5}', [1, 2, 5], None),
        ('og_{1,3,5}', [1, 3, 5], None),
        ('og_{2,3,5}', [2, 3, 5], None),
        ('og_{1,4,5}_full', [1, 4, 5], None),
        ('og_{1,4,5}_branchA_reads4', [1, 4, 5], 'g5_reads_g4'),
        ('og_{1,4,5}_branchB_no4', [1, 4, 5], 'g5_no_g4'),
    ]

    decided = set()
    branch_145 = set()
    print('Launching 6-core run on assigned sets {1,2,5}, {1,3,5}, {1,4,5}, {2,3,5}...', flush=True)
    with open(log_path, 'w', encoding='utf-8') as f:
        p = Pool(6)
        try:
            for r in p.imap_unordered(run_assigned_job, jobs):
                f.write(json.dumps(r) + '\n')
                f.flush()
                print(f"[DONE] {r['label']} -> {r['status']} ({r['time']}s)", flush=True)
                if r['status'] == 'SAT':
                    print('SAT CIRCUIT JSON:', json.dumps(r['circuit']), flush=True)
                    p.terminate()
                    break
                key = tuple(r['og_set'])
                if r['extra_mode'] is None:
                    decided.add(key)
                else:
                    branch_145.add(r['extra_mode'])
                    if len(branch_145) == 2:
                        decided.add((1, 4, 5))
                if len(decided) == 4:
                    print('ALL 4 ASSIGNED SETS DECIDED UNSAT! Terminating redundant helper.', flush=True)
                    p.terminate()
                    break
        finally:
            p.close()
            p.join()
    print('Assigned T7 run complete.', flush=True)
