# Exact parallel SAT search for L-meta-997 counterexamples (T5, Antigravity-Win).
# Covers n = 3..6, families of 1..4 nonempty sets with pairwise intersections <= 1,
# all subsets y, and all circuits with <= 7 gates (at most one NOT gate, at index t).
import sys, os, itertools, time, json
from multiprocessing import Pool
from pysat.formula import IDPool, CNF
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

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

    # Also build canonical y orbits under Aut(fam)
    fam_list = sorted(all_canon, key=lambda f: (-sum(x.bit_count() - 1 for x in f), len(f), f))
    result = []
    for fam in fam_list:
        aut = [pm for pm in pmap if tuple(sorted(pm[m] for m in fam)) == fam]
        seen_y = set()
        ys = []
        for y in range(1 << n):
            cy = min(pm[y] for pm in aut)
            if cy not in seen_y:
                seen_y.add(cy)
                ys.append(cy)
        result.append((fam, ys))
    return result


def build_base_circuit_cnf(n, fam, s, allow_not_gates):
    """
    Encodes a circuit of `s` gates on `n` inputs whose wires compute OR(S_i) for all S_i in `fam`.
    `allow_not_gates`: set of gate indices g in 0..s-1 allowed to be NOT, or 'atmost1' for any <=1 NOT.
    Returns (pool, cnf, sel_map, out_map, val_fn).
    """
    pool = IDPool()
    cnf = CNF()
    M = 1 << n
    W = n + s

    def val(w, mask):
        if w < n:
            return bool((mask >> w) & 1)
        return pool.id(('v', w, mask))

    def neg(lit):
        return (not lit) if isinstance(lit, bool) else -lit

    def add(cl):
        out = []
        for l in cl:
            if l is True:
                return
            if l is False:
                continue
            out.append(l)
        cnf.append(out)

    sel_map = {}
    not_lits = []

    for g in range(s):
        w = n + g
        choices = [('and', ()), ('or', ())]
        for j in range(w):
            choices.append(('or', (j,)))
        for j in range(w):
            for k in range(j + 1, w):
                choices.append(('and', (j, k)))
                choices.append(('or', (j, k)))
        can_not = (allow_not_gates == 'atmost1') or (g in allow_not_gates)
        if can_not:
            for j in range(w):
                choices.append(('not', (j,)))

        lits = []
        for ch in choices:
            x = pool.id(('sel', g, ch))
            sel_map[(g, ch)] = x
            lits.append(x)
            if ch[0] == 'not':
                not_lits.append(x)
        enc = CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter)
        cnf.extend(enc.clauses)

        for ch in choices:
            x = sel_map[(g, ch)]
            op, ins = ch
            if op == 'and' and len(ins) == 0:
                for mask in range(M):
                    add([-x, val(w, mask)])
            elif op == 'or' and len(ins) == 0:
                for mask in range(M):
                    add([-x, neg(val(w, mask))])
            elif op == 'or' and len(ins) == 1:
                j = ins[0]
                for mask in range(M):
                    vj = val(j, mask)
                    vw = val(w, mask)
                    add([-x, neg(vw), vj])
                    add([-x, vw, neg(vj)])
            elif op == 'not' and len(ins) == 1:
                j = ins[0]
                for mask in range(M):
                    vj = val(j, mask)
                    vw = val(w, mask)
                    add([-x, neg(vw), neg(vj)])
                    add([-x, vw, vj])
            elif op == 'and' and len(ins) == 2:
                j, k = ins
                for mask in range(M):
                    vj, vk, vw = val(j, mask), val(k, mask), val(w, mask)
                    add([-x, neg(vw), vj])
                    add([-x, neg(vw), vk])
                    add([-x, vw, neg(vj), neg(vk)])
            elif op == 'or' and len(ins) == 2:
                j, k = ins
                for mask in range(M):
                    vj, vk, vw = val(j, mask), val(k, mask), val(w, mask)
                    add([-x, vw, neg(vj)])
                    add([-x, vw, neg(vk)])
                    add([-x, neg(vw), vj, vk])

    if allow_not_gates == 'atmost1' and len(not_lits) > 1:
        enc = CardEnc.atmost(lits=not_lits, bound=1, vpool=pool, encoding=EncType.seqcounter)
        cnf.extend(enc.clauses)

    # Output wires for each S_i in fam
    out_map = {}
    for idx, smask in enumerate(fam):
        olits = []
        for w in range(W):
            # Check if w (< n) can directly match OR(smask)
            if w < n:
                if smask == (1 << w):
                    ow = pool.id(('out', idx, w))
                    out_map[(idx, w)] = ow
                    olits.append(ow)
                continue
            ow = pool.id(('out', idx, w))
            out_map[(idx, w)] = ow
            olits.append(ow)
            for mask in range(M):
                expected = bool(mask & smask)
                vw = val(w, mask)
                add([-ow, vw if expected else neg(vw)])
        if not olits:
            cnf.append([])  # Immediate UNSAT
        else:
            enc = CardEnc.equals(lits=olits, bound=1, vpool=pool, encoding=EncType.seqcounter)
            cnf.extend(enc.clauses)

    return pool, cnf, sel_map, out_map, val


def extract_circuit(n, fam, s, sel_map, out_map, model_set):
    gates = []
    not_idx = 0
    for g in range(s):
        chosen = None
        for (gg, ch), x in sel_map.items():
            if gg == g and x in model_set:
                chosen = ch
                break
        op, ins = chosen
        if op == 'not':
            not_idx = g
        gates.append((op, list(ins)))
    outputs = []
    for idx in range(len(fam)):
        for (ii, w), ow in out_map.items():
            if ii == idx and ow in model_set:
                outputs.append(w)
                break
    return gates, not_idx, outputs


def check_violation_for_y_s_t(n, fam, y, s, t):
    """
    Exact SAT test for whether `(n, fam, y, s, t)` has ANY circuit violating L-meta-997:
    LHS(fam, y) > s + m + R, i.e., R <= LHS - s - m - 1.
    Note `t` in `0..s` (`t == s` means no gate is NOT and wire n+t is out-of-range False).
    """
    m = len(fam)
    yc = y.bit_count()
    lhs = sum(sm.bit_count() if (sm & y) == 0 else min(yc, sm.bit_count()) for sm in fam)
    B_R = lhs - s - m - 1
    if B_R < 0:
        return None

    # Quick check if t == s (out-of-range wire n+t evaluates to False on all inputs)
    if t >= s:
        if yc > 0:
            return None  # False on weight 0 < |y|, invalid y!

    allow = {t} if t < s else set()
    pool, cnf, sel_map, out_map, val = build_base_circuit_cnf(n, fam, s, allow)
    if [] in cnf.clauses:
        return None

    def neg(lit):
        return (not lit) if isinstance(lit, bool) else -lit

    def add(cl):
        out = []
        for l in cl:
            if l is True:
                return
            if l is False:
                continue
            out.append(l)
        cnf.append(out)

    # Wire n+t condition on y
    if t < s:
        wt = n + t
        for mask in range(1 << n):
            if mask.bit_count() < yc:
                add([val(wt, mask)])
        add([neg(val(wt, y))])

    # Encode R <= B_R: for each g in 0..s-1, (cond_a(g) and cond_b(g)) -> r_g
    miss_S = [sm for sm in fam if (sm & y) == 0]
    outside_y = [p for p in range(n) if not ((y >> p) & 1)]

    if B_R < s and miss_S:
        r_lits = []
        for g in range(s):
            w = n + g
            rg = pool.id(('rg', g))
            r_lits.append(rg)
            for si in fam:
                # Literals that are all true iff {p : w(e_p)} == si
                la = [val(w, 1 << p) if ((si >> p) & 1) else neg(val(w, 1 << p)) for p in range(n)]
                for sj in miss_S:
                    lb = [
                        val(w, y | (1 << p)) if ((sj >> p) & 1) else neg(val(w, y | (1 << p)))
                        for p in outside_y
                    ]
                    # (all la and all lb) -> rg  <==>  (~la_0 v ... v ~lb_0 v ... v rg)
                    cl = [neg(lit) for lit in la] + [neg(lit) for lit in lb] + [rg]
                    add(cl)
        if B_R == 0:
            for rg in r_lits:
                cnf.append([-rg])
        else:
            enc = CardEnc.atmost(lits=r_lits, bound=B_R, vpool=pool, encoding=EncType.seqcounter)
            cnf.extend(enc.clauses)
    elif B_R < s and not miss_S:
        # When miss_S is empty, cond_b is always False, so R is always 0 <= B_R automatically!
        pass

    with Cadical153(bootstrap_with=cnf.clauses) as so:
        if not so.solve():
            return None
        model_set = set(l for l in so.get_model() if l > 0)
        gates, _, outputs = extract_circuit(n, fam, s, sel_map, out_map, model_set)
        sets = [[p for p in range(n) if (sm >> p) & 1] for sm in fam]
        yset = [p for p in range(n) if (y >> p) & 1]
        ok_setup, is_viol, details = verify_instance(n, sets, yset, gates, t, outputs)
        assert ok_setup and is_viol, f'Verifier disagreed! ok={ok_setup}, viol={is_viol}, details={details}'
        return {
            'n': n,
            'sets': sets,
            'y': yset,
            's': s,
            't': t,
            'gates': gates,
            'outputs': outputs,
            'details': details,
        }


def search_family_worker(job):
    idx, total, n, fam, ys = job
    t0 = time.time()
    m = len(fam)
    sum_s_minus_1 = sum(sm.bit_count() - 1 for sm in fam)
    max_possible_s = min(7, sum_s_minus_1 - 1)

    stage1_sat_sizes = []
    # Stage 1: Does ANY circuit of size s <= max_possible_s with <=1 NOT gate compute OR(S_1)..OR(S_m)?
    # Note: if s_max >= 0, padding with dummy OR() gates preserves computability, so testing s_max suffices
    # to screen out families where even s_max gates cannot compute OR(fam); if SAT, we test all s=0..max_possible_s!
    if max_possible_s >= 0:
        pool, cnf, sel_map, out_map, _ = build_base_circuit_cnf(n, fam, max_possible_s, 'atmost1')
        can_beat_monotone = False
        if [] not in cnf.clauses:
            with Cadical153(bootstrap_with=cnf.clauses) as so:
                can_beat_monotone = so.solve()
        if can_beat_monotone:
            stage1_sat_sizes.append(max_possible_s)
            # Test every y in ys, every s in 0..max_possible_s, every t in 0..s!
            for y in ys:
                for s in range(max_possible_s + 1):
                    for t in range(s + 1):
                        viol = check_violation_for_y_s_t(n, fam, y, s, t)
                        if viol is not None:
                            return {'status': 'VIOLATION', 'viol': viol, 'time': round(time.time() - t0, 3)}

    return {
        'status': 'OK',
        'idx': idx,
        'total': total,
        'n': n,
        'm': m,
        'fam': fam,
        'sum_s_minus_1': sum_s_minus_1,
        'stage1_sat': stage1_sat_sizes,
        'y_orbits': len(ys),
        'time': round(time.time() - t0, 3),
    }


def self_test():
    # Sanity test 1: S_1={0,1,2} on n=3 needs 2 OR gates; check s=2 is SAT and verifier accepts it!
    fam = (0b111,)
    pool, cnf, sel_map, out_map, _ = build_base_circuit_cnf(3, fam, 2, 'atmost1')
    with Cadical153(bootstrap_with=cnf.clauses) as so:
        assert so.solve(), 'Self-test failed: 3-way OR in 2 gates should be SAT'
        ms = set(l for l in so.get_model() if l > 0)
        gates, _, outputs = extract_circuit(3, fam, 2, sel_map, out_map, ms)
        # With t=2 (out of bounds, y=empty), check verifier says valid setup and NOT a violation
        ok_setup, is_viol, det = verify_instance(3, [[0, 1, 2]], [], gates, 2, outputs)
        assert ok_setup and not is_viol and det['LHS'] == 3 and det['RHS'] == 4, f'Unexpected: {det}'

    # Sanity test 2: 1-NOT circuit with y={0,1} on n=3, S_1={0,1}, S_2={2}:
    # gates = [AND(0,1), NOT(3), OR(0,1)], t=1, y={0,1}, outputs=[5, 2]
    ok_setup, is_viol, det = verify_instance(
        3, [[0, 1], [2]], [0, 1], [('and', [0, 1]), ('not', [3]), ('or', [0, 1])], 1, [5, 2]
    )
    assert ok_setup and not is_viol, f'Self-test 2 failed: {ok_setup}, {det}'
    print('Self-tests passed!', flush=True)


if __name__ == '__main__':
    self_test()
    workers = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    n_min = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    n_max = int(sys.argv[3]) if len(sys.argv) > 3 else 6

    t_start = time.time()
    for n in range(n_min, n_max + 1):
        t_n = time.time()
        fams = canonical_families(n, max_m=4)
        jobs = [(i + 1, len(fams), n, fam, ys) for i, (fam, ys) in enumerate(fams)]
        total_y_orbits = sum(len(ys) for _, ys in fams)
        print(f'=== n={n}: {len(fams)} canonical families ({total_y_orbits} (fam,y) orbits) ===', flush=True)

        stage1_hits = []
        with Pool(workers) as p:
            for res in p.imap_unordered(search_family_worker, jobs):
                if res['status'] == 'VIOLATION':
                    print('COUNTEREXAMPLE FOUND!', json.dumps(res['viol'], indent=2), flush=True)
                    sys.exit(0)
                if res['stage1_sat']:
                    stage1_hits.append(res)
                    print(f"  [interesting] fam={res['fam']} beat monotone in Stage 1, checked all (y,s,t): OK", flush=True)
        print(
            f'n={n} DONE in {time.time() - t_n:.2f}s: 0 violations across all {len(fams)} families '
            f'(Stage-1 1-NOT gate-savers: {len(stage1_hits)})',
            flush=True,
        )
    print(f'ALL n={n_min}..{n_max} COMPLETED in {time.time() - t_start:.2f}s. No counterexample exists.', flush=True)
