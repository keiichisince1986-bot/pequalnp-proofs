"""Try local circuit edits from a saved candidate and verify any success."""
import argparse
import json
from pathlib import Path

from search import N, rows, verify


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint", type=Path)
    parser.add_argument("witness", type=Path)
    args = parser.parse_args()
    examples = rows()
    point = [sum(1 << i for i, (u, _) in enumerate(examples) if u >> p & 1) for p in range(N)]
    target = sum(1 << i for i, (_, yes) in enumerate(examples) if yes)
    start = json.loads(args.checkpoint.read_text(encoding="utf-8"))["best"]["circuit"]
    k = len(start["gates"])
    mask = lambda indexes: sum(1 << i for i in indexes)
    seed = tuple(mask(vs) | (mask(gs) << N) for sides in start["gates"] for vs, gs in sides)
    seed += (mask(start["out_vars"]) | (mask(start["out_gates"]) << N),)
    options = [N + i // 2 for i in range(2 * k)] + [N + k]

    def variables(m):
        while m:
            bit = m & -m
            yield bit.bit_length() - 1
            m ^= bit

    def count(circuit):
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
        return (any_of(circuit[-1]) ^ target).bit_count()

    def split(m):
        return list(variables(m & ((1 << N) - 1))), list(variables(m >> N))

    beam = [(count(seed), seed)]
    seen = {seed}
    for depth in range(1, 13):
        next_beam = []
        for _, circuit in beam:
            for i, width in enumerate(options):
                for bit in range(width):
                    change = circuit[:i] + (circuit[i] ^ (1 << bit),) + circuit[i + 1:]
                    if change in seen:
                        continue
                    seen.add(change)
                    score = count(change)
                    if score is None:
                        continue
                    if score == 0:
                        ov, og = split(change[-1])
                        result = {"gates": [[split(change[2 * i]), split(change[2 * i + 1])]
                                            for i in range(k)], "out_vars": ov, "out_gates": og}
                        verify(result, examples)
                        args.witness.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
                        print(f"Verified all {len(examples)} rows at depth {depth}.")
                        return
                    next_beam.append((score, change))
        beam = sorted(next_beam)[:100]
        if not beam:
            break
        print(f"depth={depth} best_missing={beam[0][0]} distinct_candidates={len(seen)}", flush=True)


if __name__ == "__main__":
    main()
