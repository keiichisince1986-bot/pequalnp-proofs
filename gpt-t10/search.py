"""Independent SAT encoding of the Petersen AND-count circuit task."""
import argparse
from itertools import combinations
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


def check_vertex_transitivity():
    edges = {frozenset(e) for e in EDGES}
    def adjacent(a, b):
        return frozenset((a, b)) in edges
    def extend(mapping, free):
        if not free:
            return True
        i = len(mapping)
        return any(extend(mapping + [u], free - {u}) for u in free
                   if all(adjacent(i, j) == adjacent(u, v) for j, v in enumerate(mapping)))
    return all(extend([u], set(range(N)) - {u}) for u in range(N))


def minimal_positive_basis(examples):
    positives = {u for u, desired in examples if desired}
    minimal = {u for u in positives if not any(v != u and v & u == v for v in positives)}
    assert len(minimal) == 70
    assert all(any(v & u == v for v in minimal) for u in positives)
    return [(u, desired) for u, desired in examples if not desired or u in minimal]


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
    parser.add_argument("--distance", type=int, help="Bound the number of wiring edits from --phases")
    parser.add_argument("--min-distance", type=int, help="Skip already excluded wiring distances")
    parser.add_argument("--fix-bare-except", type=int, nargs="+",
                        help="Keep bare selectors from --phases except for these vertices")
    parser.add_argument("--focus-sweep", type=int,
                        help="Sweep that many movable bare vertices, always including vertex 5")
    parser.add_argument("--focus-checkpoint", type=Path,
                        help="Save completed sweep subcases here")
    parser.add_argument("--maximal-output", action="store_true",
                        help="Select all gates that are false on every negative input")
    parser.add_argument("--last-output", action="store_true",
                        help="Search the subclass where only the last gate is selected as output")
    parser.add_argument("--anchor", action="store_true",
                        help="Use Petersen vertex symmetry to fix one vertex of the first gate")
    parser.add_argument("--minimal-positive", action="store_true",
                        help="Encode only inclusion-minimal positive rows; verify on all rows")
    args = parser.parse_args()
    if any(x is not None for x in (args.distance, args.min_distance, args.fix_bare_except, args.focus_sweep)) and args.phases is None:
        parser.error("Distance bounds and fixed bare selectors require --phases")
    if args.focus_sweep is not None and (
        not 1 <= args.focus_sweep <= N or args.progress or args.fix_bare_except is not None
    ):
        parser.error("Sweep needs 1-10 movable vertices and cannot use staged or fixed-bare mode")
    if args.last_output and (args.size < 1 or args.maximal_output):
        parser.error("--last-output requires at least one gate and excludes --maximal-output")
    if args.anchor and (args.size < 1 or not check_vertex_transitivity()):
        parser.error("Anchor needs a nonempty circuit and a vertex-transitive graph")
    start = monotonic()
    examples = rows()
    basis = minimal_positive_basis(examples) if args.minimal_positive else examples
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
        if args.anchor:
            add(bare[0][0])
            add([bare[0][1][0]])
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
        if args.last_output:
            for selector in out_vertices + out_gates[:-1]:
                add([-selector])
            add([out_gates[-1]])
        if args.maximal_output:
            negatives = [mask for mask, desired in examples if not desired]
            for i, selected in enumerate(out_gates):
                add([selected, *(v(("gate value", mask, i)) for mask in negatives)])
        if args.phases:
            preferred = json.loads(args.phases.read_text(encoding="utf-8"))["best"]["circuit"]
            if len(preferred["gates"]) != k:
                raise ValueError("Phase circuit has a different gate count")
            phases = []
            bare_phases = [[] for _ in range(N)]
            for i, sides in enumerate(preferred["gates"]):
                for b, (points, predecessors) in enumerate(sides):
                    for p, lit in enumerate(bare[i][b]):
                        bare_phases[p].append(lit if p in points else -lit)
                    if args.fix_bare_except is not None:
                        for p, lit in enumerate(bare[i][b]):
                            if p not in args.fix_bare_except:
                                add([lit if p in points else -lit])
                    for choices, selected in ((bare[i][b], points), (incoming[i][b], predecessors)):
                        phases.extend(lit if j in selected else -lit for j, lit in enumerate(choices))
            for choices, selected in ((out_vertices, preferred["out_vars"]),
                                      (out_gates, preferred["out_gates"])):
                phases.extend(lit if j in selected else -lit for j, lit in enumerate(choices))
            sat.set_phases(phases)
            if args.distance is not None:
                for c in CardEnc.atmost([-p for p in phases], bound=args.distance,
                                        vpool=ids, encoding=EncType.seqcounter):
                    add(c)
            if args.min_distance is not None:
                for c in CardEnc.atleast([-p for p in phases], bound=args.min_distance,
                                         vpool=ids, encoding=EncType.seqcounter):
                    add(c)
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
        chosen_rows = set(basis)
        if args.progress:
            chosen_rows = {(u, yes) for u, yes in basis if not yes}
            if not args.progress.exists():
                chosen_rows.update(rng.sample([e for e in basis if e[1]], 24))
            if args.progress.exists():
                previous = json.loads(args.progress.read_text(encoding="utf-8"))
                config = (k, args.ordered_sides, args.max_refs)
                if tuple(previous["config"]) != config:
                    raise ValueError("Different search configuration in progress file")
                chosen_rows.update(tuple(row) for row in previous["rows"])
                best = previous["best"]

        for e in sorted(chosen_rows):
            add_example(*e)
        if args.focus_sweep is not None:
            config = {"size": k, "sweep": args.focus_sweep, "basis_rows": sorted(chosen_rows),
                      "baseline": preferred, "ordered_sides": args.ordered_sides,
                      "maximal_output": args.maximal_output, "max_refs": args.max_refs,
                      "distance": args.distance, "min_distance": args.min_distance,
                      "last_output": args.last_output, "anchor": args.anchor}
            config = json.loads(json.dumps(config))
            completed = set()
            if args.focus_checkpoint and args.focus_checkpoint.exists():
                data = json.loads(args.focus_checkpoint.read_text(encoding="utf-8"))
                if data["config"] != config:
                    raise ValueError("Different sweep configuration in progress file")
                completed.update(tuple(case) for case in data["unsat"])
            others = [p for p in range(N) if p != 5]
            for case in combinations(others, args.focus_sweep - 1):
                if case in completed:
                    continue
                movable = {5, *case}
                fixed = [lit for p, literals in enumerate(bare_phases) if p not in movable for lit in literals]
                print(f"Checking movable vertices {sorted(movable)}", flush=True)
                if sat.solve(assumptions=fixed):
                    circuit = decode()
                    verify(circuit, examples)
                    print(f"SAT elapsed={monotonic() - start:.3f}s; verified on all {len(examples)} rows", flush=True)
                    print(json.dumps(circuit, indent=2), flush=True)
                    if args.witness:
                        save(args.witness, circuit)
                    return
                completed.add(case)
                print(f"UNSAT subcase {sorted(movable)}; {len(completed)} completed", flush=True)
                if args.focus_checkpoint:
                    save(args.focus_checkpoint, {"config": config, "unsat": sorted(completed)})
            print(f"UNSAT sweep only: {len(completed)} subcases; elapsed={monotonic() - start:.3f}s", flush=True)
            return
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
