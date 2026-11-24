-- Muse (T9 calibration): my own proof of L-meta-275, work in progress.
-- Nothing here is submitted; the step is already solved upstream.
-- Status: infrastructure complete and compiling (wire values, gate equation);
-- the counting argument and the main theorem are next. Local checks use trimmed
-- imports; this file keeps the canonical header.

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

lemma step_length (w : List Bool) (g : Gate) : (step w g).length = w.length + 1 := by
  simp [step]

lemma foldl_step_split (gs : List Gate) (acc : List Bool) (j : ℕ) :
    gs.foldl step acc = (gs.drop j).foldl step ((gs.take j).foldl step acc) := by
  conv_lhs => rw [← List.take_append_drop j gs]
  rw [List.foldl_append]

/-- A wire that does not exist reads `false`. -/
lemma val_missing (C : Circuit) (x : Fin 7 → Bool) {w : ℕ} (hw : 7 + C.size ≤ w) :
    val C x w = false := by
  show (C.wires (List.ofFn x)).getD w false = false
  apply List.getD_eq_default
  have h1 := wires_length C (List.ofFn x)
  simp only [List.length_ofFn] at h1
  rw [h1]
  have h2 : C.size = C.gates.length := rfl
  omega

/-- The value of a gate wire: the gate's operation applied to the values of the
wires it reads, where a read of a wire that does not exist yet contributes `false`. -/
lemma val_gate (C : Circuit) (x : Fin 7 → Bool) {j : ℕ} (hj : j < C.gates.length)
    (g : Gate) (hg : C.gates[j]'hj = g) :
    val C x (7 + j) = g.op.eval
      (g.inputs.map (fun r => if r < 7 + j then val C x r else false)) := by
  set earlier := (C.gates.take j).foldl step (List.ofFn x) with hearlier
  have hlen : earlier.length = 7 + j := by
    rw [hearlier, foldl_step_length]
    simp [Nat.min_eq_left hj.le]
  have hsplit : C.wires (List.ofFn x)
      = (g :: C.gates.drop (j + 1)).foldl step earlier := by
    show C.gates.foldl step (List.ofFn x) = _
    rw [foldl_step_split C.gates (List.ofFn x) j, List.drop_eq_getElem_cons hj, hg]
  have hread (r : ℕ) : earlier.getD r false
      = if r < 7 + j then val C x r else false := by
    by_cases hr : r < 7 + j
    · rw [ite_eq_left hr]
      show earlier.getD r false = (C.wires (List.ofFn x)).getD r false
      rw [hsplit]
      exact (foldl_step_getD_of_lt _ earlier (by omega)).symm
    · rw [ite_eq_right hr]
      exact List.getD_eq_default _ _ (by omega)
  show (C.wires (List.ofFn x)).getD (7 + j) false = _
  rw [hsplit]
  simp only [List.foldl_cons]
  rw [foldl_step_getD_of_lt _ _ (by rw [step_length, hlen]; omega)]
  show (earlier ++ [g.op.eval (g.inputs.map fun i => earlier.getD i false)]).getD
      (7 + j) false = _
  rw [List.getD_append_right _ _ _ _ (by rw [hlen])]
  rw [hlen]
  simp only [Nat.sub_self, List.getD_cons_zero]
  simp only [hread]

lemma eval_and_two (u v : Bool) : GateOp.eval GateOp.and [u, v] = (u && v) := by
  cases u <;> cases v <;> rfl

lemma eval_or_two (u v : Bool) : GateOp.eval GateOp.or [u, v] = (u || v) := by
  cases u <;> cases v <;> rfl

end PEqualNP.Outside.L_meta_275
