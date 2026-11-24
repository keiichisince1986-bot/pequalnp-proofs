# Antigravity-Mac T6 (L-meta-909) Progress

- Updated: 2026-11-24 13:49 JST
- Encoding: `s909s.py 6 dimacs` -> `l909_s6.cnf` (6,621 vars, 26,380 clauses, 115 points)
- Started: 2026-11-24 12:18 JST (~1h30m wall time elapsed)
- Active solvers (7 cores, Apple M1):
  - PID 20858 (92.2% CPU, CPU time 84:15.94): cadical --sat --seed=2
  - PID 20855 (91.6% CPU, CPU time 84:10.88): kissat --sat --seed=4
  - PID 20853 (90.3% CPU, CPU time 84:07.18): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20859 (90.0% CPU, CPU time 84:08.38): kissat --seed=3 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20857 (89.1% CPU, CPU time 84:19.43): /opt/homebrew/Cellar/python@3.12/3.12.13_1/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/s909s.py 6
  - PID 20856 (88.2% CPU, CPU time 84:16.92): cadical --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20854 (88.0% CPU, CPU time 84:08.95): kissat --seed=2 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
- Completed runs so far: none (no SAT/UNSAT decision yet)
- Notes: Tested extra lex symmetry breaking (`L_i <= R_i` + adjacent gate order + `Stab(0)` S_3) on `s=7`; it slowed SAT finding (>7m on `s=7`), so keeping all 7 cores on the original `l909_s6.cnf`. Continuing without time limit per CLAIMS.md rule 9.
