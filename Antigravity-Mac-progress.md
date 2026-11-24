# Antigravity-Mac T6 (L-meta-909) Progress

- Updated: 2026-11-24 15:21 JST
- Encoding: `s909s.py 6 dimacs` -> `l909_s6.cnf` (6,621 vars, 26,380 clauses, 115 points)
- Started: 2026-11-24 12:18 JST (~3h02m wall time elapsed)
- Strategy (7 cores total, Apple M1):
  - 3 cores continuing original unsplit `l909_s6.cnf` (~169m CPU each: `kissat --seed=1`, `cadical --seed=1`, `s909s.py 6 cadical195`)
  - 4 cores running detached `nohup` `kissat 4.0.4` exact `og`-bitmask split (`run_t6_og_split_Antigravity_Mac.py`) targeting the remaining 16 masks with `|og| in {1,2,3}` first (currently `og={5}`, `{4,5}`, `{3,4,5}`, `{2,4,5}`, ~15m CPU each), followed by `|og|=4,5,6` independent re-verification.
- Active solvers:
  - PID 20857 (94.2% CPU, CPU time 169:55.51): /opt/homebrew/Cellar/python@3.12/3.12.13_1/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/s909s.py 6
  - PID 27424 (90.3% CPU, CPU time 15:41.04): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_3_4_5.cnf
  - PID 20853 (90.0% CPU, CPU time 169:34.72): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 27426 (88.0% CPU, CPU time 15:40.14): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_4_5.cnf
  - PID 27423 (87.7% CPU, CPU time 15:41.25): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_5.cnf
  - PID 27425 (87.6% CPU, CPU time 15:40.93): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_2_4_5.cnf
  - PID 20856 (87.2% CPU, CPU time 169:52.18): cadical --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
- Completed runs so far: none (no SAT/UNSAT decision yet)
- Notes: Continuing without time limit per CLAIMS.md rule 9.
