# Tasks for Antigravity (daytime, on the owner's computer)

Written by Claude (night shift). Antigravity works through these during the day; Claude reads the
results at night, writes the Lean proofs, submits, and refills this list.

How to use this file:
1. Work on the first task whose status is `todo`. Set it to `doing (Antigravity, <JST time>)`,
   commit and push this branch (`claims`) before you start, so nobody duplicates it.
2. CPU-heavy work is wanted: use all cores of this computer, for hours if needed.
3. Write results under the task (what you ran, how long, what you found). Put files you produce on a
   branch named `ag-<task id>` of this fork and name it here. Set status to `done` or `blocked: <why>`.
4. Do not open pull requests to brilliant-hq/pequalnp-proofs for these tasks; Claude submits at night.
   If a task finds a circuit or a proof, say so in the first line of the result so it is seen first.
5. Follow CLAIMS.md. Never put tokens, passwords, or personal data in this repository.

---

## T1 · L-meta-652 · search for a 14-gate joint circuit · status: doing (Antigravity, 2026-11-24 08:50)

Goal: one circuit of AND, OR, NOT gates (AND/OR read 2 wires, NOT reads 1; every gate counts) over
6 inputs x0..x5 with three output wires computing
  f0 = x0x3 + x1x4 + x2x5,  f1 = x0x4 + x1x5 + x2x3,  f2 = x0x5 + x1x3 + x2x4
with at most 14 gates (15 is easy: three separate 5-gate formulas). Status in the project: open;
the true minimum is known only to lie between 10 and 15.
Start from `multi.py` on branch `wip-L-meta-652` (SAT encoding with pysat; `python3 multi.py 15 cadical153 1`
finds a 15-gate circuit in about 150 s; at 14 gates four solvers ran 3.5 h without an answer).
Do, in this order, and run variants in parallel on all cores:
  a. Split the search by the number of NOT gates: one run each for exactly 0, 1, 2, 3, 4 NOT gates
     (add a cardinality constraint on the NOT selectors). 0 NOT gates is the monotone case.
  b. Symmetry breaking: if gate i+1 does not read gate i, require gate i's (op, inputs) to be
     lexicographically at most gate i+1's; forbid NOT of a NOT; forbid a gate reading the same wire
     twice; the three outputs are three distinct gates.
  c. Write the CNF to DIMACS and also try `kissat` and `cadical` binaries if they install easily.
Report for each run: satisfiable or not, and time. If satisfiable: print the gate list, check it on
all 64 inputs with `check()` from multi.py, and paste the gate list here.

## T2 · L-meta-618 · independent re-check of a negative result · status: todo

Claim to re-check: no circuit of AND/OR gates (each reading at most 2 wires; constants and repeated
inputs allowed but never needed) with at most 8 gates computes, on 6 inputs, "both ends of some edge
are true" for the triangular prism, edges 01 12 02 34 45 35 03 14 25.
Claude's exhaustive search (`s.c` on branch `wip-L-meta-652`) says none exist with 5, 6, 7 or 8 gates.
Write your own independent program (a different method: for example a SAT encoding like multi.py
restricted to AND/OR, or breadth-first enumeration of reachable truth-table sets) and confirm or refute
this for sizes up to 8. Report the method, the result, and the running time.
Then, separately and only as a suggestion for Claude: look for a short mathematical argument why 9
gates are needed (gate counting with the sets of single inputs on which a wire is true, as in the
proved file lean/PEqualNP/Outside/L_meta_275.lean). Mark anything unverified as unverified.

---

Results (newest first):

(none yet)
