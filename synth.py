# Exact synthesis: is there a monotone fan-in-2 AND/OR circuit with s gates for the edge function of G?
import sys, itertools, time
from pysat.formula import IDPool, CNF
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

def rows_for(n, edges):
    adj = [[False]*n for _ in range(n)]
    for u, v in edges: adj[u][v] = adj[v][u] = True
    pos = [frozenset(e) for e in edges]
    ind = []
    for m in range(1 << n):
        S = [i for i in range(n) if m >> i & 1]
        if all(not adj[a][b] for a, b in itertools.combinations(S, 2)): ind.append(m)
    indset = set(ind)
    maxi = [m for m in ind if all((m | (1 << i)) not in indset for i in range(n) if not m >> i & 1)]
    rows = [(sum(1 << i for i in e), True) for e in pos] + [(m, False) for m in maxi]
    return rows

def synth(n, edges, s, timeout=None):
    rows = rows_for(n, edges)
    pool = IDPool(); cnf = CNF()
    W = n + s
    def val(w, r):
        if w < n: return bool(rows[r][0] >> w & 1)
        return pool.id(('v', w, r))
    sel = {}
    for i in range(n, W):
        lits = []
        for j in range(i):
            for k in range(j + 1, i):
                x = pool.id(('s', i, j, k)); sel[(i, j, k)] = x; lits.append(x)
        enc = CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter)
        cnf.extend(enc.clauses)
    def add(cl):
        out = []
        for l in cl:
            if l is True: return
            if l is False: continue
            out.append(l)
        cnf.append(out)
    def neg(l): return (not l) if isinstance(l, bool) else -l
    for i in range(n, W):
        op = pool.id(('op', i))
        for (ii, j, k), x in sel.items():
            if ii != i: continue
            for r in range(len(rows)):
                vi, vj, vk = val(i, r), val(j, r), val(k, r)
                add([-x, -op, neg(vi), vj]); add([-x, -op, neg(vi), vk]); add([-x, -op, vi, neg(vj), neg(vk)])
                add([-x, op, vi, neg(vj)]); add([-x, op, vi, neg(vk)]); add([-x, op, neg(vi), vj, vk])
    for r, (m, t) in enumerate(rows):
        add([val(W - 1, r) if t else neg(val(W - 1, r))])
    # every gate but the last is read by a later gate
    for w in range(n, W - 1):
        cnf.append([x for (i, j, k), x in sel.items() if j == w or k == w])
    with Cadical153(bootstrap_with=cnf.clauses) as so:
        t0 = time.time(); ok = so.solve(); dt = time.time() - t0
        if not ok: return None, dt, len(rows)
        model = set(l for l in so.get_model() if l > 0)
        circ = []
        for i in range(n, W):
            for (ii, j, k), x in sel.items():
                if ii == i and x in model:
                    circ.append(('and' if pool.id(('op', i)) in model else 'or', j, k))
        return circ, dt, len(rows)

def check(n, edges, circ):
    E = set(frozenset(e) for e in edges)
    for m in range(1 << n):
        w = [bool(m >> i & 1) for i in range(n)]
        for op, j, k in circ: w.append((w[j] and w[k]) if op == 'and' else (w[j] or w[k]))
        f = any(m >> u & 1 and m >> v & 1 for u, v in edges)
        if w[-1] != f: return False
    return True

if __name__ == '__main__':
    n = int(sys.argv[1]); edges = [tuple(int(c) for c in e.split('-')) for e in sys.argv[2].split(',')]; s = int(sys.argv[3])
    circ, dt, nr = synth(n, edges, s)
    print('n=%d |E|=%d s=%d rows=%d time=%.1fs ->' % (n, len(edges), s, nr, dt), 'UNSAT' if circ is None else ('SAT check=%s %s' % (check(n, edges, circ), circ)))
