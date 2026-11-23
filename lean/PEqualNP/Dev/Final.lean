import Mathlib
import PEqualNP.Defs
import PEqualNP.Dev.CaseA

namespace PEqualNP.Outside.L_meta_540_aux

open PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity PEqualNP.MetaComplexity.NestedCover
open PEqualNP.Library.Subdivision

-- Case B (some minimum cover of K2 contains q): placeholders until CaseBBwd and CaseBFwd land.
theorem caseB {n : ℕ} (K K1 K2 : SimpleGraph (Fin n)) [DecidableRel K.Adj]
    [DecidableRel K1.Adj] [DecidableRel K2.Adj] (A : Finset (Fin n)) (l p q : Fin n)
    (hK_tf : ∀ a b c : Fin n, K.Adj a b → K.Adj b c → K.Adj c a → False)
    (hA : ∀ a ∈ A, ∀ v : Fin n, ¬ K.Adj a v) (hlp : ∀ v, K.Adj l v ↔ v = p) (hql : q ≠ l)
    (hpq : ∀ v, K.Adj p v ↔ v = l ∨ v = q)
    (hK1 : ∀ u v, K1.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ v ≠ l)
    (hK2 : ∀ u v, K2.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ u ≠ p ∧ v ≠ l ∧ v ≠ p)
    (hIH1 : ∀ C : Circuit, (IsMinimalCircuit n C ∧ circuitFun n C = graphFun K1 A) ↔
      IsNestedCoverCircuit n K1 A C)
    (hIH2 : ∀ C : Circuit, (IsMinimalCircuit n C ∧ circuitFun n C = graphFun K2 (insert p A)) ↔
      IsNestedCoverCircuit n K2 (insert p A) C)
    (hB : ∃ T2, IsMinCover K2 T2 ∧ q ∈ T2) (C : Circuit) :
    (IsMinimalCircuit n C ∧ circuitFun n C = graphFun K A) ↔ IsNestedCoverCircuit n K A C := by
  sorry

end PEqualNP.Outside.L_meta_540_aux

theorem PEqualNP.Outside.L_meta_540 : ∀ (n : ℕ) (K K1 K2 : SimpleGraph (Fin n)) [DecidableRel K.Adj] [DecidableRel K1.Adj] [DecidableRel K2.Adj] (A : Finset (Fin n)) (l p q : Fin n), ∀ (k m : ℕ) (H : SimpleGraph (Fin m)), 3 ≤ k → Nonempty (K.Adj ↪r (PEqualNP.Library.Subdivision.subdiv k H).Adj) → (∀ a ∈ A, ∀ v : Fin n, ¬ K.Adj a v) → (∀ v : Fin n, K.Adj l v ↔ v = p) → q ≠ l → (∀ v : Fin n, K.Adj p v ↔ v = l ∨ v = q) → (∀ u v : Fin n, K1.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ v ≠ l) → (∀ u v : Fin n, K2.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ u ≠ p ∧ v ≠ l ∧ v ≠ p) → (∀ C : PEqualNP.CircuitLowerBounds.Circuit, (PEqualNP.MetaComplexity.IsMinimalCircuit n C ∧ PEqualNP.MetaComplexity.circuitFun n C = PEqualNP.MetaComplexity.NestedCover.graphFun K1 A) ↔ PEqualNP.MetaComplexity.NestedCover.IsNestedCoverCircuit n K1 A C) → (∀ C : PEqualNP.CircuitLowerBounds.Circuit, (PEqualNP.MetaComplexity.IsMinimalCircuit n C ∧ PEqualNP.MetaComplexity.circuitFun n C = PEqualNP.MetaComplexity.NestedCover.graphFun K2 (insert p A)) ↔ PEqualNP.MetaComplexity.NestedCover.IsNestedCoverCircuit n K2 (insert p A) C) → (∀ C : PEqualNP.CircuitLowerBounds.Circuit, (PEqualNP.MetaComplexity.IsMinimalCircuit n C ∧ PEqualNP.MetaComplexity.circuitFun n C = PEqualNP.MetaComplexity.NestedCover.graphFun K A) ↔ PEqualNP.MetaComplexity.NestedCover.IsNestedCoverCircuit n K A C) := by
  intro n K K1 K2 _ _ _ A l p q k m H hk hemb hA hlp hql hpq hK1 hK2 hIH1 hIH2 C
  have hK_tf := PEqualNP.Outside.L_meta_540_aux.triangle_free_of_subdiv hk hemb
  by_cases hB : ∃ T2, PEqualNP.MetaComplexity.NestedCover.IsMinCover K2 T2 ∧ q ∈ T2
  · exact PEqualNP.Outside.L_meta_540_aux.caseB K K1 K2 A l p q hK_tf hA hlp hql hpq hK1 hK2
      hIH1 hIH2 hB C
  · push Not at hB
    exact PEqualNP.Outside.L_meta_540_aux.caseA K K1 K2 A l p q hK_tf hA hlp hql hpq hK1 hK2
      hIH1 (fun T2 h hq => hB T2 h hq) C
