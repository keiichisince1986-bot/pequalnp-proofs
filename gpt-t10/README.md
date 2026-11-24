# GPT independent L-meta-909 search

The encoding selects bare vertices and earlier gates separately for each OR side.
Row-specific constraints evaluate the two sides, AND gates and output. For each
vertex, a sequential counter limits bare occurrences to two gates total.
The graph is hardcoded from the task and the script generates 15 maximal
independent sets and 100 distinct one-vertex extensions. A separate evaluator
checks every candidate on all 115 inputs and checks the gate-reference and
bare-vertex restrictions.

Using Python 3.12 and python-sat 1.9.dev24:

    python search.py 7 --witness=witness-7.json
    python search.py 6 --ordered-sides --witness=witness-6.json
    python search.py 6 --solver=glucose4 --ordered-sides --progress=checkpoint-6.json --witness=witness-6-staged.json

Seven gates: SAT after 431.954 seconds, with all 115 inputs verified. The stored
witness and log are from the independent CaDiCaL run. Six gates: search running.
The staged checkpoint preserves the tested input constraints and best circuit.
Solver-internal learned clauses stay in the live solver process.
