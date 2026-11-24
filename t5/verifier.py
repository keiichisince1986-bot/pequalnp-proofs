# Standalone independent verifier for L-meta-997 (T5, Antigravity-Win).
# Directly implements Lean's CircuitLowerBounds.Circuit semantics and the T5 statement.


def eval_all_wires(n, gates, x_bits):
    w = list(x_bits)
    for op, ins in gates:
        vals = [w[idx] if 0 <= idx < len(w) else False for idx in ins]
        if op == 'and':
            res = all(vals)
        elif op == 'or':
            res = any(vals)
        elif op == 'not':
            res = not (vals[0] if vals else False)
        else:
            raise ValueError(f'Unknown op: {op}')
        w.append(res)
    return w


def verify_instance(n, sets, y, gates, t, outputs):
    """
    Returns (is_valid_setup, is_violation, details_dict).
    - sets: list of sets/frozensets of ints in 0..n-1
    - y: set/frozenset of ints in 0..n-1
    - gates: list of (op, inputs_list)
    - t: int (gate index allowed to be NOT; wire n+t tested against y)
    - outputs: list of int wire indices, len == len(sets)
    """
    S = [frozenset(s) for s in sets]
    Y = frozenset(y)
    m = len(S)
    s = len(gates)

    if not (1 <= m):
        return False, False, {'reason': 'm < 1'}
    for si in S:
        if len(si) < 1 or not si.issubset(range(n)):
            return False, False, {'reason': 'invalid S_i'}
    for i in range(m):
        for j in range(i + 1, m):
            if len(S[i] & S[j]) > 1:
                return False, False, {'reason': f'|S_{i} & S_{j}| > 1'}
    if not Y.issubset(range(n)):
        return False, False, {'reason': 'invalid y'}

    for g_idx, (op, ins) in enumerate(gates):
        if op in ('and', 'or'):
            if len(ins) > 2:
                return False, False, {'reason': f'gate {g_idx} fanin > 2'}
        elif op == 'not':
            if g_idx != t:
                return False, False, {'reason': f'NOT at gate {g_idx} != t={t}'}
            if len(ins) > 1:
                return False, False, {'reason': f'NOT gate {g_idx} fanin > 1'}
        else:
            return False, False, {'reason': f'bad op {op}'}
        for u in ins:
            if not (0 <= u < n + g_idx):
                return False, False, {'reason': f'gate {g_idx} reads non-earlier wire {u}'}

    if len(outputs) != m:
        return False, False, {'reason': 'outputs length != m'}

    # Evaluate on all 2^n inputs
    all_w = {}
    for mask in range(1 << n):
        xb = [bool((mask >> p) & 1) for p in range(n)]
        all_w[mask] = eval_all_wires(n, gates, xb)

    def get_wire(mask, w_idx):
        w = all_w[mask]
        return w[w_idx] if 0 <= w_idx < len(w) else False

    # Check outputs compute OR(S_i) on all 2^n inputs
    for i in range(m):
        oi = outputs[i]
        for mask in range(1 << n):
            expected = any(((mask >> p) & 1) for p in S[i])
            if get_wire(mask, oi) != expected:
                return False, False, {'reason': f'output {i} (wire {oi}) mismatch at mask {mask}'}

    # Check wire n+t on y
    y_mask = sum(1 << p for p in Y)
    y_card = len(Y)
    for mask in range(1 << n):
        if mask.bit_count() < y_card:
            if not get_wire(mask, n + t):
                return False, False, {'reason': f'wire n+t false on mask {mask} of weight < |y|'}
    if get_wire(y_mask, n + t):
        return False, False, {'reason': 'wire n+t true on y'}

    # Compute LHS
    lhs = 0
    for si in S:
        if len(si & Y) == 0:
            lhs += len(si)
        else:
            lhs += min(y_card, len(si))

    # Compute R
    S_set = set(S)
    miss_S = [si for si in S if len(si & Y) == 0]
    outside_y = [p for p in range(n) if p not in Y]

    r_gates = []
    for g_idx in range(s):
        w_idx = n + g_idx
        tset = frozenset(p for p in range(n) if get_wire(1 << p, w_idx))
        cond_a = tset in S_set
        cond_b = False
        if cond_a:
            for sj in miss_S:
                if all(get_wire(y_mask | (1 << p), w_idx) == (p in sj) for p in outside_y):
                    cond_b = True
                    break
        if cond_a and cond_b:
            r_gates.append(g_idx)

    R = len(r_gates)
    rhs = s + m + R
    details = {
        'n': n,
        'm': m,
        's': s,
        't': t,
        'LHS': lhs,
        'RHS': rhs,
        'R': R,
        'r_gates': r_gates,
    }
    return True, (lhs > rhs), details
