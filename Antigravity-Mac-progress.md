# Antigravity-Mac T6 (L-meta-909) Progress

- Updated: 2026-11-24 14:32 JST
- Encoding: `s909s.py 6 dimacs` -> `l909_s6.cnf` (6,621 vars, 26,380 clauses, 115 points)
- Started: 2026-11-24 12:18 JST (~2h14m wall time elapsed)
- Active solvers (7 cores, Apple M1):
  - PID 20859 (89.4% CPU, CPU time 123:55.18): kissat --seed=3 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20854 (88.3% CPU, CPU time 123:56.34): kissat --seed=2 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20855 (87.9% CPU, CPU time 123:58.78): kissat --sat --seed=4
  - PID 20856 (86.6% CPU, CPU time 124:07.74): cadical --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20853 (86.1% CPU, CPU time 123:55.12): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/l909_s6.cnf
  - PID 20858 (85.5% CPU, CPU time 124:06.02): cadical --sat --seed=2
  - PID 20857 (82.3% CPU, CPU time 124:10.73): /opt/homebrew/Cellar/python@3.12/3.12.13_1/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/s909s.py 6
- Completed runs so far: none (no SAT/UNSAT decision yet)
- Notes: Continuing without time limit per CLAIMS.md rule 9.
