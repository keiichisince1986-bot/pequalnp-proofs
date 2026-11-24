# Antigravity-Mac T6 (L-meta-909) Final Snapshot (Stopped per Coordination Ended 2026-11-24 18:21 JST)

- Updated: 2026-11-24 18:53 JST
- Stopped all solvers per TASKS.md COORDINATION ENDED notice.
- **Completed UNSAT results (all 10/10 `|og| = 3` masks confirmed UNSAT by `kissat 4.0.4`)**:
  - `{2,4,5}`: **UNSAT** in 5,348.08 s (`kissat 4.0.4`)
  - `{3,4,5}`: **UNSAT** in 8,390.40 s (`kissat 4.0.4`) AND independently **UNSAT** in 11,021.32 s (`cadical 3.1.0`)
  - `{2,3,5}`: **UNSAT** in 1,221.50 s (`kissat 4.0.4`)
  - `{1,4,5}`: **UNSAT** in 1,792.08 s (`kissat 4.0.4`)
  - `{1,2,5}`: **UNSAT** in 257.94 s (`kissat 4.0.4`)
  - `{1,3,5}`: **UNSAT** in 578.70 s (`kissat 4.0.4`)
  - `{0,3,5}`: **UNSAT** in 323.91 s (`kissat 4.0.4`)
  - `{0,2,5}`: **UNSAT** in 132.45 s (`kissat 4.0.4`)
  - `{0,1,5}`: **UNSAT** in 153.18 s (`kissat 4.0.4`)
  - `{0,4,5}`: **UNSAT** in 979.34 s (`kissat 4.0.4`)
- **In progress when stopped** (no SAT/UNSAT decision yet):
  - `{4,5}`: `kissat` 216m CPU, `cadical` 190m CPU
  - `{5}`: `kissat` 216m CPU, `cadical` 190m CPU
  - `{3,5}`: `kissat` 66m CPU
  - `{2,5}`: `kissat` 65m CPU (already UNSAT by Claude)
