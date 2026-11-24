# Antigravity-Win T7 (L-meta-909) Progress (SPLIT TABLE Assignment)

- Updated: 2026-11-24 16:25 JST
- **Assigned output-gate sets (`{1,2,5}`, `{1,3,5}`, `{1,4,5}`, `{2,3,5}`)**:
  - **`og = {1,2,5}`: UNSAT in `1,668.06 s`** (`cadical195`, 6,621 vars, 26,387 clauses)
  - **`og = {1,3,5}`: UNSAT in `1,815.54 s`** (`cadical195`, 6,621 vars, 26,387 clauses)
  - `og = {2,3,5}`: **running** (~1,721 CPU s on main worker + 2-way split launched on the 2 freed cores)
  - `og = {1,4,5}`: **running** (3 workers: full ~1,710 CPU s + branch A ~1,293 CPU s + branch B ~1,287 CPU s)
- **All previously completed & verified UNSAT results by Antigravity-Win**:
  - `s = 1..4`: UNSAT (`0.00s, 0.01s, 0.05s, 2.18s`); `s = 7`: SAT verified on all 115 points (`822.43s`)
  - `s = 6, |og| = 6`: **UNSAT** (`4.35 s`)
  - `s = 6, |og| = 5`: **UNSAT** (`361.60 s`)
  - `s = 6, |og| = 4`: **UNSAT** (`4,992.08 s`)
  - `s = 6, og = {0,1,5}`: **UNSAT** (`193.04 s`)
  - `s = 6, og = {0,2,5}`: **UNSAT** (`366.39 s`)
