"""Keep a known near-witness as a baseline for a bounded family of searches."""
from pathlib import Path
from itertools import combinations
import subprocess
import sys

from search import N

baseline, folder, *count = sys.argv[1:]
others = (p for p in range(N) if p != 5)
for selected in combinations(others, int(count[0]) - 1 if count else 1):
    vertices = list(map(str, (5, *selected)))
    witness = Path(folder) / f"witness-{'-'.join(vertices)}.json"
    print(f"Allowing bare vertices {', '.join(vertices)} to move", flush=True)
    subprocess.run([sys.executable, "search.py", "6", "--minimal-positive",
                    f"--phases={baseline}", "--fix-bare-except", *vertices,
                    f"--witness={witness}"], check=True)
    if witness.exists():
        break
