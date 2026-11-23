# Exact synthesis of a joint AND/OR/NOT fan-in-2 circuit with s gates for the three cyclic matchings of K(3,3).
import sys, time, random
from pysat.formula import IDPool, CNF
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver

N = 6
def fs(m):
    x = [bool(m >> i & 1) for i in range(N)]
    return [(x[0] and x[3]) or (x[1] and x[4]) or (x[2] and x[5]),
            (x[0] and x[4]) or (x[1] and x[5]) or (x[2] and x[3]),
            (x[0] and x[5]) or (x[1] and x[3]) or (x[2] and x[4])]

def build(s, seed):
    pool = IDPool(); cl = []
    W = N + s; R = 1 << N
    def val(w, r):
        if w < N: return bool(r >> w & 1)
        return pool.id(('v', w, r))
    def neg(l): return (not l) if isinstance(l, bool) else -l
    def add(c):
        out = []
        for l in c:
            if l is True: return
            if l is False: continue
            out.append(l)
        cl.append(out)
    users = {w: [] for w in range(W)}
    for i in range(N, W):
        lits = []
        op = pool.id(('op', i))
        for j in range(i):
            x = pool.id(('u', i, j)); lits.append(x); users[j].append(x)
            for r in range(R):
                vi, vj = val(i, r), val(j, r)
                add([-x, vi, vj]); add([-x, neg(vi), neg(vj)])
            for k in range(j + 1, i):
                y = pool.id(('b', i, j, k)); lits.append(y); users[j].append(y); users[k].append(y)
                for r in range(R):
                    vi, vj, vk = val(i, r), val(j, r), val(k, r)
                    add([-y, -op, neg(vi), vj]); add([-y, -op, neg(vi), vk]); add([-y, -op, vi, neg(vj), neg(vk)])
                    add([-y, op, vi, neg(vj)]); add([-y, op, vi, neg(vk)]); add([-y, op, neg(vi), vj, vk])
        # no NOT of a NOT
        cl.extend(CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses)
    outs = []
    for o in range(3):
        lits = []
        for w in range(N, W):
            z = pool.id(('o', o, w)); lits.append(z)
            for r in range(R):
                t = fs(r)[o]; v = val(w, r)
                add([-z, v if t else neg(v)])
        cl.extend(CardEnc.equals(lits=lits, bound=1, vpool=pool, encoding=EncType.seqcounter).clauses)
        outs.append(lits)
    for w in range(N, W):
        cl.append(users[w] + [pool.id(('o', o, w)) for o in range(3)])
    rnd = random.Random(seed); rnd.shuffle(cl)
    return pool, cl

def decode(pool, model, s):
    m = set(l for l in model if l > 0); gates = []
    for i in range(N, N + s):
        for j in range(i):
            if pool.id(('u', i, j)) in m: gates.append(('not', [j]))
            for k in range(j + 1, i):
                if pool.id(('b', i, j, k)) in m:
                    gates.append(('and' if pool.id(('op', i)) in m else 'or', [j, k]))
    outs = [w for o in range(3) for w in range(N, N + s) if pool.id(('o', o, w)) in m]
    return gates, outs

def check(gates, outs):
    for r in range(1 << N):
        w = [bool(r >> i & 1) for i in range(N)]
        for op, ins in gates:
            if op == 'not': w.append(not w[ins[0]])
            elif op == 'and': w.append(w[ins[0]] and w[ins[1]])
            else: w.append(w[ins[0]] or w[ins[1]])
        if [w[o] for o in outs] != fs(r): return False
    return True

if __name__ == '__main__':
    s, solver, seed = int(sys.argv[1]), sys.argv[2], int(sys.argv[3])
    pool, cl = build(s, seed)
    print('s=%d solver=%s seed=%d vars=%d clauses=%d' % (s, solver, seed, pool.top, len(cl)), flush=True)
    t0 = time.time()
    with Solver(name=solver, bootstrap_with=cl) as so:
        ok = so.solve()
        dt = time.time() - t0
        if not ok:
            print('UNSAT s=%d time=%.0fs' % (s, dt), flush=True)
        else:
            gates, outs = decode(pool, so.get_model(), s)
            print('SAT s=%d time=%.0fs check=%s' % (s, dt, check(gates, outs)), flush=True)
            print('GATES', gates, 'OUTS', outs, flush=True)
