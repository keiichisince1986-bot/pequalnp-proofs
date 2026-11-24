# Antigravity-Win T7 (L-meta-909) Progress

- Updated: 2026-11-24 14:02 JST
- Encoding: `s909s.py` (`s = 6`, 115 points on Petersen graph, bare count `<= 2` per vertex)
  - Verified `s = 1..4` UNSAT in `< 2.5 s` (`s=1`: 0.00s, `s=2`: 0.01s, `s=3`: 0.05s, `s=4`: 2.18s) and `s = 7` SAT verified on all 115 points.
  - Note: `s = 6` in `s909s.py` also subsumes `s <= 5` (adding a gate reading an earlier gate on both sides adds 0 bare occurrences).
- Started `s = 6` 6-core pool: 2026-11-24 12:40 JST (~1h22m wall time elapsed on `s = 6`)
- Jobs queued in 6-core pool (`run_t7_Antigravity_Win.py`):
  1. `s6_glucose4` (full `s909s.py` CNF)
  2. `s6_maplechrono` (full `s909s.py` CNF)
  3. `s6_minisat22` (full `s909s.py` CNF)
  4. `s6_og1_cadical195` (`s909s.py` + exact `|og| = 1`)
  5. `s6_og2_cadical195` (`s909s.py` + exact `|og| = 2`)
  6. `s6_og3_cadical195` (`s909s.py` + exact `|og| = 3`)
  7. `s6_og4_cadical195` (`s909s.py` + exact `|og| = 4`, picked up automatically by pool)
  8. `s6_og5_cadical195` (`s909s.py` + exact `|og| = 5`, queued)
  9. `s6_og6_cadical195` (`s909s.py` + exact `|og| = 6`, queued)
- Active solver workers (6 cores, Ryzen 5 4500U):
  - PID 4392: 3,507.8 CPU s (83.8 MB)
  - PID 20968: 3,481.3 CPU s (72.5 MB)
  - PID 21112: 2,923.0 CPU s (37.4 MB)
  - PID 11792: 2,917.9 CPU s (83.8 MB)
  - PID 6856: 2,910.0 CPU s (66.8 MB)
  - PID 10848: 1,746.5 CPU s (60.9 MB)
- Completed `s = 6` decisions so far: none yet (`t7_results.jsonl` still awaiting first `SAT`/`UNSAT`).
- Continuing without time limit per `CLAIMS.md` rule 9; pushing checkpoints every ~25 minutes.
