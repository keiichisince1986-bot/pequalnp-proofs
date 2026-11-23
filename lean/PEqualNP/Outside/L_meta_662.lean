import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_662

open CircuitLowerBounds MetaComplexity
open scoped Sym2

private def edges : Finset (Sym2 (Fin 6)) :=
  {s(0,4), s(1,5), s(2,3), s(3,4), s(3,5), s(4,5)}

private def graph : SimpleGraph (Fin 6) where
  Adj a b := s(a,b) ∈ edges
  symm := ⟨fun a b h => by rwa [Sym2.eq_swap]⟩
  loopless := ⟨by decide⟩

private def circuit : Circuit :=
  ⟨[⟨.and, [2,3]⟩, ⟨.or, [1,4]⟩, ⟨.or, [4,5]⟩, ⟨.or, [0,5]⟩,
    ⟨.or, [6,8]⟩, ⟨.and, [7,9]⟩, ⟨.or, [3,11]⟩, ⟨.and, [10,12]⟩], 13⟩

private def andGates : Finset ℕ := {0,5,7}
private def wideGates : Finset ℕ := {1,2,3,4}
private def narrowGates : Finset ℕ := {6}

private def wide (j : ℕ) : Prop :=
  ∃ u v : Fin 6, u ≠ v ∧
    (circuit.wires (List.ofFn (fun i : Fin 6 => decide (i = u)))).getD (6+j) false = true ∧
    (circuit.wires (List.ofFn (fun i : Fin 6 => decide (i = v)))).getD (6+j) false = true

private theorem sixEdges : graph.edgeSet.ncard = 6 := by
  have he : graph.edgeSet = (edges : Set (Sym2 (Fin 6))) := by
    ext e
    induction e using Sym2.inductionOn with
    | _ a b => rfl
  rw [he, Set.ncard_coe_finset]
  decide

private theorem validGate (g : Gate) (h : g ∈ circuit.gates) :
    g.op ∈ ({GateOp.and, GateOp.or} : Set GateOp) ∧ g.inputs.length ≤ 2 := by
  simp [circuit] at h
  rcases h with h | h | h | h | h | h | h | h <;> subst g <;> simp

private theorem indexBound (j : ℕ) (g : Gate) (h : circuit.gates[j]? = some g) : j < 8 := by
  by_contra! hn
  have hlen : circuit.gates.length ≤ j := by simpa [circuit] using hn
  simp [List.getElem?_eq_none hlen] at h

private theorem andClass (j : ℕ) (g : Gate) (h : circuit.gates[j]? = some g)
    (op : g.op = GateOp.and) : j ∈ andGates := by
  have hj := indexBound j g h
  interval_cases j <;> simp [circuit] at h <;> subst g <;> first | contradiction | decide

private theorem wideClass (j : ℕ) (g : Gate) (h : circuit.gates[j]? = some g)
    (op : g.op = GateOp.or) (w : wide j) : j ∈ wideGates := by
  have hj := indexBound j g h
  interval_cases j <;> simp [circuit] at h <;> subst g <;>
    first | contradiction | decide | exact False.elim ((by unfold wide; decide : ¬ wide 6) w)

private theorem narrowClass (j : ℕ) (g : Gate) (h : circuit.gates[j]? = some g)
    (op : g.op = GateOp.or) (w : ¬ wide j) : j ∈ narrowGates := by
  have hj := indexBound j g h
  interval_cases j <;> simp [circuit] at h <;> subst g <;>
    first | contradiction | decide | exact False.elim (w (by unfold wide; decide))

end PEqualNP.Outside.L_meta_662

open PEqualNP.Outside.L_meta_662
open scoped Sym2

-- A triangle with one pendant edge at each vertex has six edges.
-- The three disjoint pendant edges force at least three cover vertices.
-- The circuit has three AND gates, four wide OR gates and one narrow OR gate.
set_option maxRecDepth 16000 in
set_option maxHeartbeats 2000000 in
theorem PEqualNP.Outside.L_meta_662 :
    ¬ (∀ (n k : ℕ) (G : SimpleGraph (Fin n)) (C : PEqualNP.CircuitLowerBounds.Circuit) (A B D : Finset ℕ),
      (∀ a b c e : Fin n, G.Adj a b → G.Adj b c → G.Adj c e → G.Adj e a → a = c ∨ b = e) →
      (∀ T : Finset (Fin n), (∀ i j : Fin n, G.Adj i j → i ∈ T ∨ j ∈ T) → k ≤ T.card) →
      PEqualNP.MetaComplexity.Monotone2 C →
      (∀ x : Fin n → Bool, C.eval (List.ofFn x) = true ↔ ∃ u v : Fin n, G.Adj u v ∧ x u = true ∧ x v = true) →
      (∀ (j : ℕ) (g : PEqualNP.CircuitLowerBounds.Gate), C.gates[j]? = some g → g.op = PEqualNP.CircuitLowerBounds.GateOp.and → j ∈ A) →
      (∀ (j : ℕ) (g : PEqualNP.CircuitLowerBounds.Gate), C.gates[j]? = some g → g.op = PEqualNP.CircuitLowerBounds.GateOp.or → (∃ u v : Fin n, u ≠ v ∧ (C.wires (List.ofFn (fun i : Fin n => decide (i = u)))).getD (n + j) false = true ∧ (C.wires (List.ofFn (fun i : Fin n => decide (i = v)))).getD (n + j) false = true) → j ∈ B) →
      (∀ (j : ℕ) (g : PEqualNP.CircuitLowerBounds.Gate), C.gates[j]? = some g → g.op = PEqualNP.CircuitLowerBounds.GateOp.or → ¬ (∃ u v : Fin n, u ≠ v ∧ (C.wires (List.ofFn (fun i : Fin n => decide (i = u)))).getD (n + j) false = true ∧ (C.wires (List.ofFn (fun i : Fin n => decide (i = v)))).getD (n + j) false = true) → j ∈ D) →
      G.edgeSet.ncard + 2 * k ≤ A.card + B.card + 2 * D.card + 2) := by
  intro conjecture
  let : DecidableRel graph.Adj := fun i j => inferInstanceAs (Decidable (s(i,j) ∈ edges))
  have bad := conjecture 6 3 graph circuit andGates wideGates narrowGates
    (by decide) (by decide) (fun g hg => validGate g hg) (by decide)
    andClass wideClass narrowClass
  rw [sixEdges] at bad
  have hf : ¬ (6 + 2 * 3 ≤ andGates.card + wideGates.card + 2 * narrowGates.card + 2) := by decide
  exact hf bad
