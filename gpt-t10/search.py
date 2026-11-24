"""Independent SAT encoding of the Petersen AND-count circuit task."""
import argparse
import json
from pathlib import Path
from random import Random
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
    parser.add_argument("--ordered-sides", action="store_true")
    parser.add_argument("--max-refs", type=int)
    parser.add_argument("--progress", type=Path, help="Use staged constraints and save progress here")
    parser.add_argument("--seed", type=int, default=909)
    parser.add_argument("--phases", type=Path, help="Prefer the wiring in this checkpoint without constraining it")
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
        if args.max_refs is not None:
            refs = [selected for gate in incoming for side in gate for selected in side]
            for c in CardEnc.atmost(refs, bound=args.max_refs, vpool=ids, encoding=EncType.seqcounter):
                add(c)
        if args.ordered_sides:
            for i in range(k):
                prefix = v(("equal side prefix", i, 0))
                add([prefix])
                for j, (a, b) in enumerate(zip(bare[i][0] + incoming[i][0], bare[i][1] + incoming[i][1])):
                    after = v(("equal side prefix", i, j + 1))
                    for clause in ([-prefix, -a, b], [-after, prefix], [-after, -a, b],
                                   [-after, a, -b], [-prefix, -a, -b, after],
                                   [-prefix, a, b, after]):
                        add(clause)
                    prefix = after
        out_vertices = [v(("output vertex", p)) for p in range(N)]
        out_gates = [v(("output gate", i)) for i in range(k)]
        if args.phases:
            preferred = json.loads(args.phases.read_text(encoding="utf-8"))["best"]["circuit"]
            if len(preferred["gates"]) != k:
                raise ValueError("Phase circuit has a different gate count")
            phases = []
            for i, sides in enumerate(preferred["gates"]):
                for b, (points, predecessors) in enumerate(sides):
                    for choices, selected in ((bare[i][b], points), (incoming[i][b], predecessors)):
                        phases.extend(lit if j in selected else -lit for j, lit in enumerate(choices))
            for choices, selected in ((out_vertices, preferred["out_vars"]),
                                      (out_gates, preferred["out_gates"])):
                phases.extend(lit if j in selected else -lit for j, lit in enumerate(choices))
            sat.set_phases(phases)
        for p in range(N):
            use = [v(("bare in either side", i, p)) for i in range(k)]
            for i, u in enumerate(use):
                define_or(u, [bare[i][0][p], bare[i][1][p]])
            for c in CardEnc.atmost(use, bound=2, vpool=ids, encoding=EncType.seqcounter):
                add(c)

        def add_example(mask, desired):
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

        def decode():
            positive = {x for x in sat.get_model() if x > 0}
            def chosen(xs):
                return [j for j, x in enumerate(xs) if x in positive]
            return {
                "gates": [[(chosen(bare[i][b]), chosen(incoming[i][b])) for b in range(2)]
                          for i in range(k)],
                "out_vars": chosen(out_vertices),
                "out_gates": chosen(out_gates),
            }

        def save(path, data):
            temp = path.with_suffix(path.suffix + ".tmp")
            temp.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
            temp.replace(path)

        rng = Random(args.seed)
        best = None
        chosen_rows = set(examples)
        if args.progress:
            chosen_rows = {(u, yes) for u, yes in examples if not yes}
            chosen_rows.update(rng.sample([e for e in examples if e[1]], 24))
            if args.progress.exists():
                previous = json.loads(args.progress.read_text(encoding="utf-8"))
                config = (k, args.ordered_sides, args.max_refs)
                if tuple(previous["config"]) != config:
                    raise ValueError("Different search configuration in progress file")
                chosen_rows.update(tuple(row) for row in previous["rows"])
                best = previous["best"]

        for e in sorted(chosen_rows):
            add_example(*e)
        while True:
            if args.progress:
                save(args.progress, {"config": [k, args.ordered_sides, args.max_refs],
                                     "rows": sorted(chosen_rows), "best": best})
            print(f"size={k} solver={args.solver} rows={len(chosen_rows)} variables={sat.nof_vars()}", flush=True)
            if not sat.solve():
                print(f"UNSAT elapsed={monotonic() - start:.3f}s", flush=True)
                return
            circuit = decode()
            failed = []
            for e in examples:
                try:
                    verify(circuit, [e])
                except AssertionError:
                    failed.append(e)
            assert not (set(failed) & chosen_rows)
            if not failed:
                print(f"SAT elapsed={monotonic() - start:.3f}s", flush=True)
                print(f"Verified on all {len(examples)} rows\n{json.dumps(circuit, indent=2)}", flush=True)
                if args.witness:
                    save(args.witness, circuit)
                return
            assert args.progress
            if best is None or len(failed) < best["failed"]:
                best = {"failed": len(failed), "circuit": circuit}
            print(f"Candidate fails {len(failed)} of {len(examples)} rows", flush=True)
            batch = rng.sample(failed, min(8, len(failed)))
            for e in batch:
                add_example(*e)
            chosen_rows.update(batch)


if __name__ == "__main__":
    main()
