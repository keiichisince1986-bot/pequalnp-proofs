# Extended & unscreened checks for L-meta-997 (T5, Antigravity-Win):
# 1. Direct unscreened SAT check of every feasible (fam, y, s, t) tuple on n=3..6, m=1..4, s<=7.
# 2. Extended 1-NOT gate-saving & violation search on n=6 (all m up to 7, s<=10) and n=7 (Fano plane & subfamilies, s<=13).
import sys, os, itertools, time
from multiprocessing import Pool
from pysat.solvers import Cadical153

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sat_search import canonical_families, check_violation_for_y_s_t, build_base_circuit_cnf


def unscreened_worker(job):
    n, fam, ys = job
    m = len(fam)
    checked = 0
    for y in ys:
        yc = y.bit_count()
        lhs = sum(sm.bit_count() if (sm & y) == 0 else min(yc, sm.bit_count()) for sm in fam)
        k_miss2 = sum(1 for sm in fam if (sm & y) == 0 and sm.bit_count() >= 2)
        min_s = sum(1 for sm in fam if sm.bit_count() >= 2) + (1 if yc >= 1 else 0)
        max_s = min(7, lhs - m - 1 - k_miss2)
        for s in range(min_s, max_s + 1):
            for t in range(s + 1):
                checked += 1
                viol = check_violation_for_y_s_t(n, fam, y, s, t)
                if viol is not None:
                    return ('VIOLATION', viol, checked)
    return ('OK', None, checked)


def fano_job(job):
    label, n, fam, s_target = job
    t0 = time.time()
    pool, cnf, _, _, _ = build_base_circuit_cnf(n, fam, s_target, 'atmost1')
    ok = False
    if [] not in cnf.clauses:
        with Cadical153(bootstrap_with=cnf.clauses) as so:
            ok = so.solve()
    return (label, n, len(fam), s_target, ok, round(time.time() - t0, 2))


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6

    print('=== Part 1: Direct unscreened (fam, y, s, t) SAT verification on n=3..6, m=1..4, s<=7 ===', flush=True)
    t0 = time.time()
    for n in range(3, 7):
        tn = time.time()
        fams = canonical_families(n, max_m=4)
        jobs = [(n, fam, ys) for fam, ys in fams]
        tot_checked = 0
        with Pool(workers) as p:
            for status, viol, cnt in p.imap_unordered(unscreened_worker, jobs):
                tot_checked += cnt
                if status == 'VIOLATION':
                    print('VIOLATION FOUND:', viol, flush=True)
                    sys.exit(0)
        print(f'  n={n}: directly solved {tot_checked:,} (fam, y, s, t) SAT instances -> 0 violations ({time.time()-tn:.2f}s)', flush=True)
    print(f'Part 1 done in {time.time()-t0:.2f}s.\n', flush=True)

    print('=== Part 2: Extended n=6 (m=5..7, up to s=10) & n=7 Fano subfamilies (m=3..7, up to s=13) ===', flush=True)
    ext_jobs = []
    # Pasch + up to 3 matching edges on n=6:
    pasch = [0b000111, 0b011001, 0b101010, 0b110100]  # {0,1,2}, {0,3,4}, {1,3,5}, {2,4,5}
    matching = [0b100001, 0b010010, 0b001100]          # {0,5}, {1,4}, {2,3}
    for r in range(1, 4):
        fam = tuple(sorted(pasch + matching[:r]))
        s_tgt = sum(x.bit_count() - 1 for x in fam) - 1
        ext_jobs.append((f'n6_Pasch+{r}edges', 6, fam, s_tgt))

    # Fano plane on n=7:
    fano_lines = [
        (1 << 0) | (1 << 1) | (1 << 3),
        (1 << 1) | (1 << 2) | (1 << 4),
        (1 << 2) | (1 << 3) | (1 << 5),
        (1 << 3) | (1 << 4) | (1 << 6),
        (1 << 4) | (1 << 5) | (1 << 0),
        (1 << 5) | (1 << 6) | (1 << 1),
        (1 << 6) | (1 << 0) | (1 << 2),
    ]
    for k in range(3, 8):
        # All subsets of k lines of Fano are isomorphic for k=1,2,5,6,7; for k=3,4 there are 2 orbits (concurrent vs non-concurrent)
        if k in (3, 4):
            # Pick both orbits: lines sharing point 0 vs general
            with_0 = [L for L in fano_lines if L & 1]
            without_0 = [L for L in fano_lines if not (L & 1)]
            if k == 3:
                orbits = [('Fano_3_concurrent', with_0), ('Fano_3_triangle', without_0[:3])]
            else:
                orbits = [('Fano_4_star+1', with_0 + without_0[:1]), ('Fano_4_pasch', without_0)]
            for lbl, sub in orbits:
                fam = tuple(sorted(sub))
                ext_jobs.append((lbl, 7, fam, 2 * k - 1))
        else:
            fam = tuple(sorted(fano_lines[:k]))
            ext_jobs.append((f'Fano_{k}lines', 7, fam, 2 * k - 1))

    with Pool(workers) as p:
        for lbl, n, m, stgt, ok, dt in p.imap_unordered(fano_job, ext_jobs):
            print(f'  {lbl}: n={n}, m={m}, s={stgt} (1 gate below monotone {stgt+1}) -> {"SAT!" if ok else "UNSAT"} ({dt}s)', flush=True)
