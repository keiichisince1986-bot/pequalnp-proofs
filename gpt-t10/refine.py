"""Try local circuit edits from a saved candidate and verify any success."""
import argparse
import json
from pathlib import Path
from random import Random

from search import N, rows, verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("witness", type=Path)
    parser.add_argument("--progress", type=Path)
    parser.add_argument("--saturate-output", action="store_true")
    parser.add_argument("--relocate", action="store_true")
    parser.add_argument("--beam", type=int, default=100)
    parser.add_argument("--depth", type=int, default=12)
    parser.add_argument("--seed", type=int)
    args = parser.parse_args()
    examples = rows()
    point = [sum(1 << i for i, (u, _) in enumerate(examples) if u >> p & 1) for p in range(N)]
    target = sum(1 << i for i, (_, yes) in enumerate(examples) if yes)
    negative = ((1 << len(examples)) - 1) ^ target
    start = json.loads(args.checkpoint.read_text(encoding="utf-8"))["best"]["circuit"]
    k = len(start["gates"])
    mask = lambda indexes: sum(1 << i for i in indexes)
    seed = tuple(mask(vs) | (mask(gs) << N) for sides in start["gates"] for vs, gs in sides)
    seed += (mask(start["out_vars"]) | (mask(start["out_gates"]) << N),)
    options = [N + i // 2 for i in range(2 * k)] + [0 if args.saturate_output else N + k]

    def variables(m):
        while m:
            bit = m & -m
            yield bit.bit_length() - 1
            m ^= bit

    def evaluate(circuit):
        seen = [0, 0]
        for i in range(k):
            bare = (circuit[2 * i] | circuit[2 * i + 1]) & ((1 << N) - 1)
            if bare & seen[1]:
                return None
            seen[1] |= bare & seen[0]
            seen[0] |= bare
        flow = point.copy()
        def any_of(select):
            value = 0
            for p in variables(select):
                value |= flow[p]
            return value
        for i in range(k):
            flow.append(any_of(circuit[2 * i]) & any_of(circuit[2 * i + 1]))
        selectors = circuit[-1]
        if args.saturate_output:
            selectors = sum(1 << i for i, val in enumerate(flow) if not (val & negative))
        return (any_of(selectors) ^ target).bit_count(), selectors

    def count(circuit):
        result = evaluate(circuit)
        return result[0] if result is not None else None

    def split(m):
        return list(variables(m & ((1 << N) - 1))), list(variables(m >> N))

    def decode(c):
        ov, og = split(evaluate(c)[1])
        return {"gates": [[split(c[2 * i]), split(c[2 * i + 1])] for i in range(k)],
                "out_vars": ov, "out_gates": og}

    def save(path, result):
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
        temp.replace(path)

    def neighbors(c):
        for i, width in enumerate(options):
            for bit in range(width):
                yield c[:i] + (c[i] ^ (1 << bit),) + c[i + 1:]
        if args.relocate:
            for g in range(k):
                for v in variables((c[2 * g] | c[2 * g + 1]) & ((1 << N) - 1)):
                    bit = 1 << v
                    for side in range(2 * k):
                        if side // 2 == g or c[side] & bit:
                            continue
                        moved = list(c)
                        moved[2 * g] &= ~bit
                        moved[2 * g + 1] &= ~bit
                        moved[side] |= bit
                        yield tuple(moved)

    beam = [(count(seed), seed)]
    best_score = beam[0][0]
    if args.progress:
        save(args.progress, {"depth": 0, "best": {"failed": best_score, "circuit": decode(seed)}})
    seen = {seed}
    rng = Random(args.seed)
    for depth in range(1, args.depth + 1):
        next_beam = []
        for _, circuit in beam:
            for change in neighbors(circuit):
                if change in seen:
                    continue
                seen.add(change)
                score = count(change)
                if score is None:
                    continue
                if score == 0:
                    result = decode(change)
                    verify(result, examples)
                    save(args.witness, result)
                    print(f"Verified all {len(examples)} rows at depth {depth}.")
                    return
                next_beam.append((score, change))
        if args.seed is None:
            beam = sorted(next_beam)[:args.beam]
        else:
            rng.shuffle(next_beam)
            beam = sorted(next_beam, key=lambda scored: scored[0])[:args.beam]
        if not beam:
            break
        if args.progress and beam[0][0] < best_score:
            best_score, best_circuit = beam[0]
            save(args.progress, {"depth": depth, "best": {"failed": best_score, "circuit": decode(best_circuit)}})
        print(f"depth={depth} best_missing={beam[0][0]} distinct_candidates={len(seen)}", flush=True)


if __name__ == "__main__":
    main()
