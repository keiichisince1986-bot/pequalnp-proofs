# L-meta-909 search (Petersen graph, AND-count circuits)

Goal: an AND-count circuit (see lean/PEqualNP/Defs/AndCountCircuit.lean upstream) with at most 6 AND
gates, each vertex bare in at most 2 gates, correct on the 115 defined points (false on the 15 maximal
independent sets I of the Petersen graph, true on every I + w). A 7-gate circuit exists (s909.py 7
finds one in seconds). The step asks for 6: if one exists, Claude turns it into the Lean proof.

- s909s.py: SAT encoding with sound symmetry breaking (last gate is an output, every gate used, no
  empty side, vertex 0 in the left side of gate 0). `python3 s909s.py 6 <pysat solver>` solves;
  `python3 s909s.py 6 dimacs` writes l909_s6.cnf for kissat or cadical binaries.
- s909.py: the same encoding without symmetry breaking.
A satisfying model prints the circuit as JSON and checks it on all 115 points.

LeanTemplate_7gate.lean: a checked Lean template (with the 7-gate circuit) that proves WellFormed,
the bare-count bound and correctness on all maximal independent sets with `decide +kernel` (needs
`set_option synthInstance.maxSize 4096 in` and `set_option synthInstance.maxHeartbeats 400000 in`
above the correctness theorem). For a 6-gate circuit, replace the gate data and size, then wrap it
into the final theorem of L-meta-909 (subst G; rewrite SimpleGraph.fromRel_adj).
