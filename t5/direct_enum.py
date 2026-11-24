# Independent zero-SAT bit-vector DFS search for L-meta-997 (T5, Antigravity-Win).
# Uses native Python integer truth tables (2^n bits) without pysat or any external solver.
import sys, os, itertools, time
from multiprocessing import Pool

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verifier import verify_instance


def canonical_families(n, max_m=4):
    perms = list(itertools.permutations(range(n)))
    pmap = [[0] * (1 << n) for _ in perms]
    for pi, p in enumerate(perms):
        for mask in range(1 << n):
            pmap[pi][mask] = sum(1 << p[i] for i in range(n) if (mask >> i) & 1)

    def canon_fam(fam):
        return min(tuple(sorted(pm[m] for m in fam)) for pm in pmap)

    subs = [m for m in range(1, 1 << n)]
    level = {canon_fam((m,)) for m in subs}
    all_canon = set(level)
    for _ in range(2, max_m + 1):
        nxt = set()
        for fam in level:
            for m in subs:
                if m not in fam and all((m & prev).bit_count() <= 1 for prev in fam):
                    nxt.add(canon_fam(fam + (m,)))
        all_canon |= nxt
        level = nxt
    return sorted(all_canon, key=lambda f: (-sum(x.bit_count() - 1 for x in f), len(f), f))


def check_family_dfs(job):
    """
    Pure bit-vector DFS: checks whether `fam` on `n` inputs has ANY circuit of size
    `s <= min(7, sum(|S_i|-1) - 1)` with at most 1 NOT gate computing OR(S_1)..OR(S_m).
    If any such circuit exists, checks all y in 0..2^n-1 and all t with `verify_instance`.
    """
    n, fam = job
    t0 = time.time()
    sum_s_minus_1 = sum(sm.bit_count() - 1 for sm in fam)
    s_max = min(7, sum_s_minus_1 - 1)
    if s_max <= 0:
        # With 0 gates, only singleton sets S_i = {p} are computable (already sum_s_minus_1 == 0 if all singletons)
        return {'n': n, 'fam': fam, 's_max': s_max, 'nodes': 0, 'found_1not': 0, 'viol': None, 'time': 0.0}

    M = 1 << n
    full_mask = (1 << M) - 1

    # Input wire truth tables
    in_tts = []
    for i in range(n):
        tt = 0
        for mask in range(M):
            if (mask >> i) & 1:
                tt |= (1 << mask)
        in_tts.append(tt)

    # Target truth tables for sets of size >= 2 (singletons are already in in_tts)
    targets = set()
    all_target_tts = []
    for sm in fam:
        tt = 0
        for mask in range(M):
            if mask & sm:
                tt |= (1 << mask)
        all_target_tts.append(tt)
        if sm.bit_count() >= 2:
            targets.add(tt)

    nodes = 0
    found_1not = 0
    sets_list = [[p for p in range(n) if (sm >> p) & 1] for sm in fam]

    def dfs(wires, wire_set, gates, used_not, missing):
        nonlocal nodes, found_1not
        nodes += 1
        rem = s_max - len(gates)
        m_cnt = len(missing)
        if m_cnt == 0:
            found_1not += 1
            # Test this circuit (and padded/unpadded t, y) against L-meta-997!
            s_cur = len(gates)
            outputs = [wires.index(tt) for tt in all_target_tts]
            t_candidates = [used_not] if used_not is not None else list(range(s_cur + 1))
            for t_idx in t_candidates:
                for y_mask in range(1 << n):
                    yset = [p for p in range(n) if (y_mask >> p) & 1]
                    ok_setup, is_viol, det = verify_instance(n, sets_list, yset, gates, t_idx, outputs)
                    if ok_setup and is_viol:
                        return {
                            'n': n, 'sets': sets_list, 'y': yset,
                            'gates': list(gates), 't': t_idx, 'outputs': outputs, 'details': det
                        }
            return None

        if m_cnt > rem:
            return None

        W = len(wires)
        must_hit_target = (m_cnt == rem)

        # Enumerate candidate next truth tables (deduplicated at this depth: if two gate choices
        # at the same step produce the exact same truth table, keeping one representative per
        # (truth_table, is_not) is 100% lossless!)
        mono_candidates = {}
        if not must_hit_target:
            if 0 not in wire_set:
                mono_candidates[0] = ('or', [])
            if full_mask not in wire_set:
                mono_candidates[full_mask] = ('and', [])
        else:
            if 0 in missing:
                mono_candidates[0] = ('or', [])
            if full_mask in missing:
                mono_candidates[full_mask] = ('and', [])

        for j in range(W):
            wj = wires[j]
            for k in range(j + 1, W):
                wk = wires[k]
                a = wj & wk
                if must_hit_target:
                    if a in missing and a not in mono_candidates:
                        mono_candidates[a] = ('and', [j, k])
                else:
                    if a not in wire_set and a not in mono_candidates:
                        mono_candidates[a] = ('and', [j, k])
                o = wj | wk
                if must_hit_target:
                    if o in missing and o not in mono_candidates:
                        mono_candidates[o] = ('or', [j, k])
                else:
                    if o not in wire_set and o not in mono_candidates:
                        mono_candidates[o] = ('or', [j, k])

        # Try monotone steps first
        for tt, g_spec in mono_candidates.items():
            wires.append(tt)
            wire_set.add(tt)
            gates.append(g_spec)
            nxt_missing = missing - {tt} if tt in missing else missing
            res = dfs(wires, wire_set, gates, used_not, nxt_missing)
            if res is not None:
                return res
            gates.pop()
            wire_set.remove(tt)
            wires.pop()

        # Try NOT step if not yet used
        if used_not is None:
            not_candidates = {}
            for j in range(W):
                nt = full_mask ^ wires[j]
                if must_hit_target:
                    if nt in missing and nt not in not_candidates:
                        not_candidates[nt] = ('not', [j])
                else:
                    if nt not in wire_set and nt not in not_candidates:
                        not_candidates[nt] = ('not', [j])
            g_idx = len(gates)
            for tt, g_spec in not_candidates.items():
                wires.append(tt)
                wire_set.add(tt)
                gates.append(g_spec)
                nxt_missing = missing - {tt} if tt in missing else missing
                res = dfs(wires, wire_set, gates, g_idx, nxt_missing)
                if res is not None:
                    return res
                gates.pop()
                wire_set.remove(tt)
                wires.pop()

        return None

    viol = dfs(list(in_tts), set(in_tts), [], None, frozenset(targets))
    return {
        'n': n,
        'fam': fam,
        's_max': s_max,
        'nodes': nodes,
        'found_1not': found_1not,
        'viol': viol,
        'time': round(time.time() - t0, 3),
    }


if __name__ == '__main__':
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    n_min = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    t_all = time.time()
    for n in range(n_min, n_max + 1):
        t_n = time.time()
        fams = canonical_families(n, max_m=4)
        jobs = [(n, fam) for fam in fams]
        tot_nodes = 0
        tot_1not = 0
        with Pool(workers) as p:
            for r in p.imap_unordered(check_family_dfs, jobs):
                tot_nodes += r['nodes']
                tot_1not += r['found_1not']
                if r['viol'] is not None:
                    print('COUNTEREXAMPLE FOUND BY DFS!', r['viol'], flush=True)
                    sys.exit(0)
        print(
            f'n={n} DFS DONE in {time.time() - t_n:.2f}s: {len(fams)} families, '
            f'nodes={tot_nodes:,}, circuits_beating_monotone={tot_1not}, violations=0',
            flush=True,
        )
    print(f'ALL DFS n={n_min}..{n_max} COMPLETED in {time.time() - t_all:.2f}s. Zero violations.', flush=True)
