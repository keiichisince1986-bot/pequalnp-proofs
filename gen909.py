# Build lean/PEqualNP/Outside/L_meta_909.lean from a circuit JSON (as printed by s909*.py).
# usage: python3 gen909.py circuit.json statement.txt out.lean
import json, sys
C = json.load(open(sys.argv[1])); stmt = open(sys.argv[2]).read().strip(); out = sys.argv[3]
s = C['size']; G = C['gates']
def fs(xs): return '∅' if not xs else '{' + ', '.join(str(x) for x in xs) + '}'
def vec(key): return '![' + ', '.join(fs(g[key]) for g in G) + ']'
body = f"""import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_909

open PEqualNP.AndCount

def lv : Fin {s} → Finset (Fin 10) := {vec('Lvars')}
def lg : Fin {s} → Finset (Fin {s}) := {vec('Lgates')}
def rv : Fin {s} → Finset (Fin 10) := {vec('Rvars')}
def rg : Fin {s} → Finset (Fin {s}) := {vec('Rgates')}

def C : AndCountCircuit 10 where
  size := {s}
  leftVars := lv
  leftGates := lg
  rightVars := rv
  rightGates := rg
  outVars := ∅
  outGates := {fs(C['out'])}

def edges : List (ℕ × ℕ) :=
  [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 5), (1, 6), (2, 7), (3, 8), (4, 9), (5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]

theorem wf : C.WellFormed := by
  unfold AndCountCircuit.WellFormed; decide

theorem bare : ∀ v : Fin 10, (Finset.univ.filter (fun i : Fin C.size => v ∈ C.leftVars i ∨ v ∈ C.rightVars i)).card ≤ 2 := by
  decide

set_option synthInstance.maxSize 4096 in
set_option synthInstance.maxHeartbeats 400000 in
theorem correct : ∀ I : Finset (Fin 10),
    (∀ a ∈ I, ∀ c ∈ I, ¬ (a ≠ c ∧ (((a : ℕ), (c : ℕ)) ∈ edges ∨ ((c : ℕ), (a : ℕ)) ∈ edges))) →
    (∀ w : Fin 10, w ∉ I → ∃ a ∈ I, (a ≠ w ∧ (((a : ℕ), (w : ℕ)) ∈ edges ∨ ((w : ℕ), (a : ℕ)) ∈ edges))) →
    C.eval I = false ∧ ∀ w : Fin 10, w ∉ I → C.eval (insert w I) = true := by
  decide +kernel

end PEqualNP.Outside.L_meta_909

theorem PEqualNP.Outside.L_meta_909 : {stmt} := by
  intro G hG
  subst hG
  refine ⟨PEqualNP.Outside.L_meta_909.C, PEqualNP.Outside.L_meta_909.wf, by decide,
    PEqualNP.Outside.L_meta_909.bare, ?_⟩
  intro I hind hmax
  apply PEqualNP.Outside.L_meta_909.correct I
  · intro a ha c hc h
    exact hind a ha c hc (by rw [SimpleGraph.fromRel_adj]; exact h)
  · intro w hw
    obtain ⟨a, ha, hadj⟩ := hmax w hw
    exact ⟨a, ha, by rw [SimpleGraph.fromRel_adj] at hadj; exact hadj⟩
"""
open(out, 'w').write(body)
print('wrote', out)
