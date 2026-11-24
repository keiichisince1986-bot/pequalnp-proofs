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

Partial six-gate results: an incremental SAT candidate missed 8 rows; a
separate bit-vector beam search improved it to 4 errors. Neither is a
witness. The exact and staged SAT runs continue. An additional exact run
selects all gates that are false on every negative row. This choice preserves
satisfiability because adding such output gates cannot change a negative
row or turn a positive row false. Its starting phases prefer a saved candidate
without imposing it as a hard constraint.

The second saved SAT candidate missed 6 rows. Local rewiring with automatic
selection of negative-safe outputs reduced that to 3 missed rows. See the
relocate checkpoint for the circuit. Exact size-six runs are still unresolved.

Removing each gate from the verified seven-gate circuit gives minimum 10
missed rows before local rewiring and 4 afterward. Independently, the exact
search within eight selector edits of the three-error candidate returned
UNSAT in 32.984 seconds. This excludes that neighborhood only. Radius 12
and the exact unrestricted searches are still running.

Radius 12 also returned UNSAT in 456.234 seconds. Radius 16 and a last-gate-
only output subclass were started independently; unrestricted searches
remain active. The last-output switch and symmetry anchor were checked
against the known seven-gate witness with all selectors fixed. The anchor
checks that the input graph is vertex-transitive before restricting the
first nonzero gate to contain vertex 0 on one side.

Paused after upstream PR #4051 appeared. It proposes an 85-row reduction,
and explicitly leaves the six-gate synthesis child open. GPT's six-gate
runs ended without an unrestricted SAT or UNSAT result. The best stored
candidate fails three of the 115 rows. The saved options and checkpoints
can resume the public search inputs and best candidates; no solver process
or in-memory learned clause database remains after the stop.

Resumed T10 after verifying that PR #4051 adds only R_meta_909_1.lean,
whereas the own-file criterion for stopping is L_meta_909.lean. The
staged solver starts from the 69 saved input constraints, and the
three-error circuit supplies initial wiring phases. The original
solver's learned clauses cannot be recovered from these files.

A separate run independently computes the inclusion-minimal positive
basis: 70 positive masks plus 15 negative masks. It checks that every
positive mask contains a retained mask. Since the gates are monotone,
these rows suffice; any witness is still verified on all 115 rows.
A third run searches 13 through 16 selector edits from the saved
three-error circuit, skipping the previously excluded radius 12.
