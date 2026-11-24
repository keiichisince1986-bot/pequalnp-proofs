# Antigravity-Win T7 (L-meta-909) Progress (SPLIT TABLE Assignment)

- Updated: 2026-11-24 15:56 JST
- **Assigned output-gate sets from `TASKS.md` SPLIT TABLE**: `{1,2,5}`, `{1,3,5}`, `{1,4,5}`, `{2,3,5}` (running exclusively on 6 cores with `cadical195`, `run_t7_assigned_Antigravity_Win.py`).
  - Core 1: `og = {1,2,5}` (+ sound unit break `v('L', 5, 'gate', 4)` since `og_4 == 0`)
  - Core 2: `og = {1,3,5}` (+ `v('L', 5, 'gate', 4)`)
  - Core 3: `og = {2,3,5}` (+ `v('L', 5, 'gate', 4)`)
  - Core 4: `og = {1,4,5}` full
  - Core 5: `og = {1,4,5}` branch A (`v('L', 5, 'gate', 4)` — gate 5 reads gate 4, WLOG on `L_5`)
  - Core 6: `og = {1,4,5}` branch B (`-v('L', 5, 'gate', 4), -v('R', 5, 'gate', 4)` — gate 5 does not read gate 4)
- Active workers (~23m wall time on assigned sets, ~3,643 CPU s on this phase / ~39,600 CPU s cumulative on T7):
  - PIDs `10620` (771.6s), `13036` (770.3s), `24072` (769.0s), `11612` (448.3s), `17616` (442.9s), `24132` (440.9s)
- **Previously completed & verified UNSAT results by Antigravity-Win**:
  - `s = 1..4`: UNSAT (`0.00s, 0.01s, 0.05s, 2.18s`); `s = 7`: SAT verified on all 115 points (`822.43s`).
  - `s = 6, |og| = 6`: **UNSAT** (`4.35 s`)
  - `s = 6, |og| = 5`: **UNSAT** (`361.60 s`)
  - `s = 6, |og| = 4`: **UNSAT** (`4,992.08 s`)
  - `s = 6, og = {0,1,5}` (`110001`): **UNSAT** (`193.04 s`)
  - `s = 6, og = {0,2,5}` (`101001`): **UNSAT** (`366.39 s`)
- Completed decisions on `{1,2,5}, {1,3,5}, {1,4,5}, {2,3,5}` so far: none yet (`t7_assigned_results.jsonl` awaiting first completion).
