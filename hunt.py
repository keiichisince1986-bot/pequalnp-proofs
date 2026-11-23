# Hunt for counterexamples to L-meta-602 over graphs with max degree <= 3 and girth >= 5.
import sys, itertools, random, threading, time, json
import networkx as nx
from multiprocessing import Pool
sys.path.insert(0, '.')
from synth import rows_for, check
from pysat.formula import IDPool, CNF
from pysat.card import CardEnc, EncType
from pysat.solvers import Cadical153

def tau(n, edges):
    for k in range(n + 1):
        for T in itertools.combinations(range(n), k):
            s = set(T)
            if all(u in s or v in s for u, v in edges): return k

def girth_ok(G):
    try:
        return nx.girth(G) >= 5
    except Exception:
        return True

def graphs(nmin, nmax, per_n, seed):
    rnd = random.Random(seed); seen = set()
    for n in range(nmin, nmax + 1):
        tries = 0; got = 0
        while got < per_n and tries < 200000:
            tries += 1
            G = nx.empty_graph(n); cand = list(itertools.combinations(range(n), 2)); rnd.shuffle(cand)
            for u, v in cand:
                if G.degree(u) < 3 and G.degree(v) < 3:
                    G.add_edge(u, v)
                    if nx.girth(G) < 5: G.remove_edge(u, v)
            if G.number_of_edges() == 0 or not nx.is_connected(G): continue
            h = nx.weisfeiler_lehman_graph_hash(G)
            if h in seen: continue
            seen.add(h); got += 1
            yield n, sorted(G.edges())

def run(args):
    n, edges, budget = args
    t = tau(n, edges); s = len(edges) + t - 2
    rows = rows_for(n, edges)
    from synth import synth
    import synth as SY
    res = {'n': n, 'edges': edges, 'tau': t, 's': s}
    # solve with a time budget
    pool = IDPool()
    circ = None; status = 'timeout'
    import multiprocessing as mp
    t0 = time.time()
    try:
        out = SY.synth(n, edges, s)
        circ = out[0]; status = 'UNSAT' if circ is None else 'SAT'
    except Exception as e:
        status = 'error ' + str(e)
    res['status'] = status; res['time'] = round(time.time() - t0, 1)
    if circ is not None:
        res['circ'] = circ; res['check'] = check(n, edges, circ)
    return res

if __name__ == '__main__':
    nmin, nmax, per_n = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    jobs = [(n, e, 0) for n, e in graphs(nmin, nmax, per_n, 1)]
    # Petersen first when n reaches 10
    if nmax >= 10:
        P = nx.petersen_graph(); jobs.insert(0, (10, sorted(P.edges()), 0))
    print('jobs', len(jobs), flush=True)
    with Pool(4) as p:
        for r in p.imap_unordered(run, jobs):
            print(json.dumps(r), flush=True)
            if r.get('status') == 'SAT': print('COUNTEREXAMPLE', flush=True)
