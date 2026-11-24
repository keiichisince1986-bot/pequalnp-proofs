import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_909

open PEqualNP.AndCount

def lv : Fin 7 → Finset (Fin 10) := ![{7, 8}, {4}, {3, 7}, {8, 9}, {4, 5}, {1}, {1}]
def lg : Fin 7 → Finset (Fin 7) := ![∅, ∅, ∅, ∅, {3}, {2, 3, 4}, {4}]
def rv : Fin 7 → Finset (Fin 10) := ![{3, 9}, {5}, {2}, {6}, {0}, {2}, {0, 6}]
def rg : Fin 7 → Finset (Fin 7) := ![∅, ∅, {0, 1}, {1, 2}, {0, 2, 3}, {4}, {5}]

def C : AndCountCircuit 10 where
  size := 7
  leftVars := lv
  leftGates := lg
  rightVars := rv
  rightGates := rg
  outVars := ∅
  outGates := {5, 6}

def edges : List (ℕ × ℕ) :=
  [(0, 1), (1, 2), (2, 3), (3, 4), (4, 0), (0, 5), (1, 6), (2, 7), (3, 8), (4, 9), (5, 7), (7, 9), (9, 6), (6, 8), (8, 5)]

theorem wf : C.WellFormed := by
  unfold AndCountCircuit.WellFormed; decide

theorem bare : ∀ v : Fin 10, (Finset.univ.filter (fun i : Fin C.size => v ∈ C.leftVars i ∨ v ∈ C.rightVars i)).card ≤ 2 := by
  decide

example : ∀ I : Finset (Fin 10), C.eval I = false ∨ True := by decide +kernel
example : ∀ I : Finset (Fin 10), (∀ a ∈ I, ∀ c ∈ I, ¬ (a ≠ c ∧ (((a : ℕ), (c : ℕ)) ∈ edges ∨ ((c : ℕ), (a : ℕ)) ∈ edges))) → True := by decide +kernel

set_option synthInstance.maxSize 4096 in
set_option synthInstance.maxHeartbeats 400000 in
theorem correct : ∀ I : Finset (Fin 10),
    (∀ a ∈ I, ∀ c ∈ I, ¬ (a ≠ c ∧ (((a : ℕ), (c : ℕ)) ∈ edges ∨ ((c : ℕ), (a : ℕ)) ∈ edges))) →
    (∀ w : Fin 10, w ∉ I → ∃ a ∈ I, (a ≠ w ∧ (((a : ℕ), (w : ℕ)) ∈ edges ∨ ((w : ℕ), (a : ℕ)) ∈ edges))) →
    C.eval I = false ∧ ∀ w : Fin 10, w ∉ I → C.eval (insert w I) = true := by
  decide +kernel

end PEqualNP.Outside.L_meta_909

