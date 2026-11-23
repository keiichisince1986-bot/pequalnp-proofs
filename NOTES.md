# Search notes (Claude, night of 2026-11-23/24)

- L-meta-618 (prism, monotone, at most 8 gates): exhaustive search (s.c) finds none at sizes 5 to 8;
  released as statement_seems_false.
- L-meta-652 shard 0 (three cyclic matchings of K(3,3), joint AND/OR/NOT circuit):
  multi.py finds a 15-gate circuit in about 150 s; at 14 gates four solvers
  (cadical153, cadical195, glucose4, maplechrono) ran from 01:25 to 05:00 JST without an answer.
  Next: add symmetry breaking (gate order, no double NOT) or try kissat.
- L-meta-602 (degree at most 3, girth at least 5): synth.py agrees with |E| + tau - 1 for C5, C6,
  C5 plus a pendant edge, and a 7-vertex graph.
