# Antigravity-Win T7 (L-meta-909) Progress

- Updated: 2026-11-24 14:56 JST
- **New confirmed partial UNSAT results (`s909s.py` at `s = 6` with exact output-gate count `|og|`)**:
  - **`|og| = 6` (`s6_og6_cadical195`): UNSAT in `4.35 s`** (6,621 vars, 26,386 clauses)
  - **`|og| = 5` (`s6_og5_cadical195`): UNSAT in `361.60 s`** (6,626 vars, 26,395 clauses)
  - **`|og| = 4` (`s6_og4_cadical195`): UNSAT in `4,992.08 s`** (6,637 vars, 26,412 clauses)
  - Plus earlier `s = 1..4` UNSAT (`0.00s, 0.01s, 0.05s, 2.18s`).
  - **Consequence**: Any 6-AND circuit for `L-meta-909` (if one exists) **must have `|outGates| in {1, 2, 3}`**!
- Still running (5 active workers from `run_t7_Antigravity_Win.py` pool, ~2h15m wall time, ~28,730 CPU s total):
  - `s6_og1_cadical195` (`|og| = 1`), `s6_og2_cadical195` (`|og| = 2`), `s6_og3_cadical195` (`|og| = 3`), plus unsplit solver runs (`glucose4` / `maplechrono` / `minisat22`):
    - PID 4392: 5,265.7 CPU s (82.2 MB)
    - PID 20968: 5,211.8 CPU s (77.9 MB)
    - PID 11792: 5,041.2 CPU s (65.9 MB)
    - PID 21112: 5,038.5 CPU s (33.7 MB)
    - PID 6856: 5,023.3 CPU s (72.3 MB)
    - (PID 10848 finished `og=4, 5, 6` in 3,149.7 CPU s and is now free)
- Next action on the newly freed 6th core: launching targeted `cadical195` sub-splits of `|og| in {1, 2, 3}` by exact `og` bitmask to accelerate closing `{1, 2, 3}`.
