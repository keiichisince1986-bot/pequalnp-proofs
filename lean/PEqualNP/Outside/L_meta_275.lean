-- Muse (T9 calibration): my own proof of L-meta-275, work in progress.
-- Nothing here is submitted; the step is already solved upstream.
-- Status: foundation lemmas (wire values, input wires). Gate equation and the
-- counting argument are next. Local checks use trimmed imports; this file keeps
-- the canonical header.

import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_275

open PEqualNP.CircuitLowerBounds

/-- The value of wire `w` of `C` on the input given by `x`. -/
def val (C : Circuit) (x : Fin 7 → Bool) (w : ℕ) : Bool :=
  (C.wires (List.ofFn x)).getD w false

/-- The set of single points on which wire `w` of `C` is true. -/
def T (C : Circuit) (w : ℕ) : Finset (Fin 7) :=
  Finset.univ.filter (fun p => val C (fun q => decide (q = p)) w = true)

lemma mem_T {C : Circuit} {w : ℕ} {p : Fin 7} :
    p ∈ T C w ↔ val C (fun q => decide (q = p)) w = true := by
  simp [T]

/-- The one-step function used in `Circuit.wires`. -/
abbrev step (w : List Bool) (g : Gate) : List Bool :=
  w ++ [g.op.eval (g.inputs.map fun i => w.getD i false)]

lemma foldl_step_length (gs : List Gate) (acc : List Bool) :
    (gs.foldl step acc).length = acc.length + gs.length := by
  induction gs generalizing acc with
  | nil => simp
  | cons g gs ih =>
      simp only [List.foldl_cons]
      rw [ih]
      simp [step, List.length_append]
      omega

lemma foldl_step_getD_of_lt (gs : List Gate) (acc : List Bool) {w : ℕ}
    (hw : w < acc.length) :
    (gs.foldl step acc).getD w false = acc.getD w false := by
  induction gs generalizing acc with
  | nil => simp
  | cons g gs ih =>
      simp only [List.foldl_cons]
      rw [ih (acc := acc ++ [g.op.eval (g.inputs.map fun i => acc.getD i false)])
        (by simp only [List.length_append, List.length_cons]; omega)]
      exact List.getD_append _ _ _ _ hw

lemma wires_length (C : Circuit) (x : List Bool) :
    (C.wires x).length = x.length + C.gates.length := by
  exact foldl_step_length C.gates x

lemma wires_getD_of_lt (C : Circuit) (x : List Bool) {w : ℕ} (hw : w < x.length) :
    (C.wires x).getD w false = x.getD w false :=
  foldl_step_getD_of_lt C.gates x hw

/-- The value of an input wire is the corresponding input bit. -/
lemma val_input (C : Circuit) (x : Fin 7 → Bool) (q : Fin 7) :
    val C x q.val = x q := by
  unfold val
  rw [wires_getD_of_lt C (List.ofFn x) (by simp [q.isLt])]
  rw [List.getD_eq_getElem _ _ (by simp [q.isLt])]
  fin_cases q <;> rfl

end PEqualNP.Outside.L_meta_275
