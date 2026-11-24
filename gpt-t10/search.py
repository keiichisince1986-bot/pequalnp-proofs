"""Independent SAT encoding of the Petersen AND-count circuit task."""
import argparse
import json
from pathlib import Path
from time import monotonic

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver


N = 10
EDGES = [(int(e[0]), int(e[1])) for e in "01 12 23 34 40 05 16 27 38 49 57 79 96 68 85".split()]


def rows():
    independent = [u for u in range(1 << N)
                   if all(u & ((1 << a) | (1 << b)) != ((1 << a) | (1 << b)) for a, b in EDGES)]
    pool = set(independent)
    negative = [u for u in independent
                if all(u | (1 << v) not in pool for v in range(N) if not (u >> v & 1))]
    positive = sorted({u | (1 << v) for u in negative for v in range(N) if not (u >> v & 1)})
    assert len(negative) == 15 and len(negative) + len(positive) == 115
    return [(u, False) for u in negative] + [(u, True) for u in positive]


def verify(circuit, examples):
    gates = circuit["gates"]
    for i, sides in enumerate(gates):
        assert len(sides) == 2
        for vs, gs in sides:
            assert all(0 <= v < N for v in vs) and all(0 <= j < i for j in gs)
    for v in range(N):
        assert sum(any(v in vs for vs, _ in sides) for sides in gates) <= 2
    for mask, desired in examples:
        values = []
        for sides in gates:
            values.append(all(any(mask >> v & 1 for v in vs) or any(values[j] for j in gs)
                              for vs, gs in sides))
        actual = any(mask >> v & 1 for v in circuit["out_vars"]) or any(
            values[j] for j in circuit["out_gates"])
        assert actual == desired, (mask, desired, actual)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("size", type=int)
    parser.add_argument("--solver", default="cadical195")
    parser.add_argument("--witness", type=Path)
    args = parser.parse_args()
    start = monotonic()
    examples = rows()
    k = args.size
    ids = IDPool()
    v = ids.id
    with Solver(name=args.solver) as sat:
        add = sat.add_clause

        def define_or(dst, src):
            add([-dst, *src])
            for s in src:
                add([-s, dst])

        def define_and(dst, a, b):
            add([-dst, a])
            add([-dst, b])
            add([dst, -a, -b])

        bare = [[[v(("bare", i, b, p)) for p in range(N)] for b in range(2)] for i in range(k)]
        incoming = [[[v(("read", i, b, j)) for j in range(i)] for b in range(2)] for i in range(k)]
        out_vertices = [v(("output vertex", p)) for p in range(N)]
        out_gates = [v(("output gate", i)) for i in range(k)]
        for p in range(N):
            use = [v(("bare in either side", i, p)) for i in range(k)]
            for i, u in enumerate(use):
                define_or(u, [bare[i][0][p], bare[i][1][p]])
            for c in CardEnc.atmost(use, bound=2, vpool=ids, encoding=EncType.seqcounter):
                add(c)

        for mask, desired in examples:
            true_points = [p for p in range(N) if mask >> p & 1]
            value = [v(("gate value", mask, i)) for i in range(k)]
            for i in range(k):
                sides = [v(("side value", mask, i, b)) for b in range(2)]
                for b, side in enumerate(sides):
                    terms = [bare[i][b][p] for p in true_points]
                    for j, selected in enumerate(incoming[i][b]):
                        term = v(("selected true predecessor", mask, i, b, j))
                        define_and(term, selected, value[j])
                        terms.append(term)
                    define_or(side, terms)
                define_and(value[i], *sides)
            terms = [out_vertices[p] for p in true_points]
            for i, selected in enumerate(out_gates):
                term = v(("selected true output gate", mask, i))
                define_and(term, selected, value[i])
                terms.append(term)
            if desired:
                add(terms)
            else:
                for term in terms:
                    add([-term])

        print(f"size={k} solver={args.solver} rows={len(examples)} variables={sat.nof_vars()}", flush=True)
        result = sat.solve()
        print(f"{'SAT' if result else 'UNSAT'} elapsed={monotonic() - start:.3f}s", flush=True)
        if result:
            positive = {x for x in sat.get_model() if x > 0}
            def chosen(xs):
                return [j for j, x in enumerate(xs) if x in positive]
            circuit = {
                "gates": [[(chosen(bare[i][b]), chosen(incoming[i][b])) for b in range(2)]
                          for i in range(k)],
                "out_vars": chosen(out_vertices),
                "out_gates": chosen(out_gates),
            }
            verify(circuit, examples)
            payload = json.dumps(circuit, indent=2)
            print(f"Verified on all {len(examples)} rows\n{payload}", flush=True)
            if args.witness:
                tmp = args.witness.with_suffix(".tmp")
                tmp.write_text(payload + "\n", encoding="utf-8")
                tmp.replace(args.witness)


if __name__ == "__main__":
    main()
