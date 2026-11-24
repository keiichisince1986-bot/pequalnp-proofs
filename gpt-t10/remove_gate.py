import json
from pathlib import Path
from search import rows, verify
base = json.loads(Path("run7/witness.json").read_text())
items = []
for j in range(7):
    def renumber(gs):
        return [i - (i > j) for i in gs if i != j]
    candidate = {
        "gates": [[(vs, renumber(gs)) for vs, gs in gate]
                  for i, gate in enumerate(base["gates"]) if i != j],
        "out_vars": base["out_vars"], "out_gates": renumber(base["out_gates"]),
    }
    failures = 0
    for row in rows():
        try:
            verify(candidate, [row])
        except AssertionError:
            failures += 1
    items.append((failures, j, candidate))
for failures, j, _ in sorted(items):
    print("removed", j, "errors", failures)
failures, j, candidate = min(items)
Path("removed-gate-seed.json").write_text(
    json.dumps({"best": {"failed": failures, "circuit": candidate}}), encoding="utf-8")
