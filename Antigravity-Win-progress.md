# Antigravity-Win T7 (L-meta-909) Final Checkpoint (Stopped on Upstream PR #4051)

- Stopped: 2026-11-24 15:25 JST per `CLAIMS.md` rule 9 (`brilliant-hq/pequalnp-proofs#4051` opened upstream by `nanoxas`).
- Branch with full scripts & logs: `ag-T7` (also mirrored here on `wip-L-meta-909`).
- **Completed & verified results (`s909s.py` encoding, 115 Petersen points, bare count `<= 2`)**:
  - `s = 7` (`cadical195`): **SAT** in 822.43 s (verified on all 115 points, bare counts `[2]*10`).
  - `s = 1..4` (`cadical195`): **UNSAT** (`s=1`: 0.00 s, `s=2`: 0.01 s, `s=3`: 0.05 s, `s=4`: 2.18 s).
  - `s = 6`, `|og| = 6` (`cadical195`): **UNSAT** in **4.35 s** (6,621 vars, 26,386 clauses).
  - `s = 6`, `|og| = 5` (`cadical195`): **UNSAT** in **361.60 s** (6,626 vars, 26,395 clauses).
  - `s = 6`, `|og| = 4` (`cadical195`): **UNSAT** in **4,992.08 s** (6,637 vars, 26,412 clauses).
  - `s = 6`, exact `og` mask `110001` (`|og| = 3`, `og = {0, 1, 5}`): **UNSAT** in **193.04 s**.
  - `s = 6`, exact `og` mask `101001` (`|og| = 3`, `og = {0, 2, 5}`): **UNSAT** in **366.39 s**.
- **Undecided when stopped (~2h45m wall / ~36,000 CPU s total)**:
  - Unsplit `s = 6` on `glucose4`, `maplechrono`, `minisat22`; split `s = 6` on `|og| = 1`, `|og| = 2`, and remaining 8 of 10 masks for `|og| = 3`.
