import itertools, sys, json
from pysat.formula import IDPool
from pysat.card import CardEnc, EncType
from pysat.solvers import Solver
E=[(0,1),(1,2),(2,3),(3,4),(4,0),(0,5),(1,6),(2,7),(3,8),(4,9),(5,7),(7,9),(9,6),(6,8),(8,5)]
n=10; adj=[[False]*n for _ in range(n)]
for a,b in E: adj[a][b]=adj[b][a]=True
maxind=[]
for m in range(1<<n):
    S=[i for i in range(n) if m>>i&1]
    if any(adj[a][b] for a,b in itertools.combinations(S,2)): continue
    if all(any(adj[a][w] for a in S) for w in range(n) if not m>>w&1): maxind.append(m)
pts=[(m,False) for m in maxind]+[(m|(1<<w),True) for m in maxind for w in range(n) if not m>>w&1]
print("maximal independent sets",len(maxind),"points",len(pts))
s=int(sys.argv[1]); pool=IDPool(); cl=[]
def v(*k): return pool.id(k)
def OR_def(out, lits):
    # out <-> OR(lits)
    cl.append([-out]+lits)
    for l in lits: cl.append([out,-l])
def AND2(out,a,b):
    cl.append([-out,a]); cl.append([-out,b]); cl.append([out,-a,-b])
for i in range(s):
    for side in 'LR':
        for P,(m,_) in enumerate(pts):
            terms=[]
            for x in range(n):
                if m>>x&1: terms.append(v(side,i,'var',x))
            for j in range(i):
                t=v('t',side,i,j,P); AND2(t, v(side,i,'gate',j), v('g',j,P)); terms.append(t)
            OR_def(v('s',side,i,P), terms)
    for P in range(len(pts)): AND2(v('g',i,P), v('s','L',i,P), v('s','R',i,P))
for P,(m,val) in enumerate(pts):
    terms=[]
    for i in range(s):
        t=v('to',i,P); AND2(t, v('og',i), v('g',i,P)); terms.append(t)
    o=v('out',P); OR_def(o, terms); cl.append([o] if val else [-o])
for x in range(n):
    bs=[]
    for i in range(s):
        b=v('bare',i,x); OR_def(b,[v('L',i,'var',x),v('R',i,'var',x)]); bs.append(b)
    cl.extend(CardEnc.atmost(lits=bs,bound=2,vpool=pool,encoding=EncType.seqcounter).clauses)

# symmetry breaking (sound: a smallest circuit can be assumed to have these properties)
for i in range(s):
    # every side nonempty
    for side in 'LR':
        cl.append([v(side,i,'var',x) for x in range(n)] + [v(side,i,'gate',j) for j in range(i)])
    # every gate is used: read by a later side or an output
    users=[v(side,k,'gate',i) for k in range(i+1,s) for side in 'LR']
    cl.append(users+[v('og',i)])
cl.append([v('og',s-1)])
# vertex-transitivity of the Petersen graph: some vertex in the left side of gate 0 is vertex 0
cl.append([v('L',0,'var',0)])

if len(sys.argv) > 2 and sys.argv[2] == 'dimacs':
    from pysat.formula import CNF
    CNF(from_clauses=cl).to_file('l909_s%d.cnf' % s)
    print('wrote l909_s%d.cnf vars %d clauses %d' % (s, pool.top, len(cl)))
    sys.exit(0)
with Solver(name=sys.argv[2],bootstrap_with=cl) as so:
    ok=so.solve(); print("size",s,"SAT" if ok else "UNSAT")
    if ok:
        M=set(l for l in so.get_model() if l>0)
        C={'size':s,'gates':[],'out':[i for i in range(s) if v('og',i) in M]}
        for i in range(s):
            g={}
            for side in 'LR':
                g[side+'vars']=[x for x in range(n) if v(side,i,'var',x) in M]
                g[side+'gates']=[j for j in range(i) if v(side,i,'gate',j) in M]
            C['gates'].append(g)
        print(json.dumps(C))
        # verify
        def ev(U):
            val=[]
            for i,g in enumerate(C['gates']):
                sl=any(U>>x&1 for x in g['Lvars']) or any(val[j] for j in g['Lgates'])
                sr=any(U>>x&1 for x in g['Rvars']) or any(val[j] for j in g['Rgates'])
                val.append(sl and sr)
            return any(val[j] for j in C['out'])
        print("verify", all(ev(m)==t for m,t in pts), "bare", [sum(1 for g in C['gates'] if x in g['Lvars'] or x in g['Rvars']) for x in range(n)])
