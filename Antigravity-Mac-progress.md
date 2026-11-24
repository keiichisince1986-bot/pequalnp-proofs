# Antigravity-Mac T6 (L-meta-909) Progress

- Updated: 2026-11-24 15:43 JST
- Assignment (TASKS.md SPLIT TABLE): exclusively `{5}`, `{4,5}`, `{3,4,5}`, `{2,4,5}` (stopped unsplit runs to focus all 7 cores on our 4 assigned sets without duplicating Claude/Antigravity-Win)
- Active detached solvers (7 cores, Apple M1):
  - PID 27424 (92.8% CPU, CPU time 37:03.32): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_3_4_5.cnf
  - PID 28490 (92.3% CPU, CPU time 10:46.72): cadical --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_5.cnf
  - PID 27426 (92.3% CPU, CPU time 37:02.87): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_4_5.cnf
  - PID 28492 (91.5% CPU, CPU time 10:46.68): cadical --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_3_4_5.cnf
  - PID 28491 (91.3% CPU, CPU time 10:47.00): cadical --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_4_5.cnf
  - PID 27423 (90.6% CPU, CPU time 37:03.74): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_5.cnf
  - PID 27425 (88.8% CPU, CPU time 37:03.06): kissat --seed=1 /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/og_cnfs/l909_s6_og_2_4_5.cnf
  - PID 28488 (0.0% CPU, CPU time 0:00.15): /opt/homebrew/Cellar/python@3.12/3.12.13_1/Frameworks/Python.framework/Versions/3.12/Resources/Python.app/Contents/MacOS/Python /Users/Keiichi/.gemini/antigravity/brain/37365b3d-a260-49cd-87c6-3bb48a2efe1c/scratch/t6/run_t6_assigned_cadical.py 3
- Completed assigned sets so far: 0/4 (no SAT/UNSAT decision yet; `og_2_4_5` queued for cadical once one of the first 3 finishes)
- Notes: Continuing without time limit per CLAIMS.md rule 9.
