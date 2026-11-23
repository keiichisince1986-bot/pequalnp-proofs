import Mathlib
import PEqualNP.Defs
import PEqualNP.Dev.S539

namespace PEqualNP.Outside.L_meta_540_aux

open PEqualNP.CircuitLowerBounds PEqualNP.MetaComplexity PEqualNP.MetaComplexity.NestedCover
open PEqualNP.Library.Subdivision

-- If q lies in no minimum cover of K2, then l lies in no minimum cover of K.
lemma free_of_caseA {n : ℕ} {K K2 : SimpleGraph (Fin n)} {l p q : Fin n}
    (hlp : ∀ v, K.Adj l v ↔ v = p) (hql : q ≠ l)
    (hpq : ∀ v, K.Adj p v ↔ v = l ∨ v = q)
    (hK2 : ∀ u v, K2.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ u ≠ p ∧ v ≠ l ∧ v ≠ p)
    (hqA : ∀ T2, IsMinCover K2 T2 → q ∉ T2) :
    ∀ T, IsMinCover K T → l ∉ T := by
  classical
  intro T hT hlT
  have hlpadj : K.Adj l p := (hlp p).2 rfl
  have hlp_ne : l ≠ p := hlpadj.ne
  obtain ⟨S, hS⟩ := exists_minCover K2
  have hcovSp : K.IsVertexCover ((insert p S : Finset (Fin n)) : Set (Fin n)) := by
    intro u v huv
    simp only [Finset.coe_insert, Set.mem_insert_iff, Finset.mem_coe]
    by_cases hu : u = l
    · subst hu; right; left; exact (hlp v).1 huv
    by_cases hv : v = l
    · subst hv; left; left; exact ((hlp u).1 huv.symm)
    by_cases hup : u = p
    · left; left; exact hup
    by_cases hvp : v = p
    · right; left; exact hvp
    have h2 : K2.Adj u v := (hK2 u v).2 ⟨huv, hu, hup, hv, hvp⟩
    rcases hS.1 h2 with h | h
    · left; right; exact h
    · right; right; exact h
  have hTle : T.card ≤ S.card + 1 :=
    (hT.2 _ hcovSp).trans (Finset.card_insert_le _ _)
  by_cases hpT : p ∈ T
  · -- removing l and p leaves a cover of K2 that is too small
    have hcov : K2.IsVertexCover (((T.erase l).erase p : Finset (Fin n)) : Set (Fin n)) := by
      intro u v huv
      obtain ⟨huv', hu, hup, hv, hvp⟩ := (hK2 u v).1 huv
      simp only [Finset.mem_coe, Finset.mem_erase]
      rcases hT.1 huv' with h | h
      · left; exact ⟨hup, hu, h⟩
      · right; exact ⟨hvp, hv, h⟩
    have hc := hS.2 _ hcov
    have hcard : ((T.erase l).erase p).card + 2 = T.card := by
      rw [Finset.card_erase_of_mem (Finset.mem_erase.2 ⟨hlp_ne.symm, hpT⟩),
        Finset.card_erase_of_mem hlT]
      have : 2 ≤ T.card := by
        have hsub : ({l, p} : Finset (Fin n)) ⊆ T := by
          intro x hx; simp only [Finset.mem_insert, Finset.mem_singleton] at hx
          rcases hx with rfl | rfl <;> assumption
        have := Finset.card_le_card hsub
        rw [Finset.card_pair hlp_ne] at this; exact this
      omega
    omega
  · -- p is out, so q is in, and T without l is a minimum cover of K2 containing q
    have hpqadj : K.Adj p q := (hpq q).2 (Or.inr rfl)
    have hqT : q ∈ T := by
      rcases hT.1 hpqadj with h | h
      · exact absurd h hpT
      · exact h
    have hcov : K2.IsVertexCover ((T.erase l : Finset (Fin n)) : Set (Fin n)) := by
      intro u v huv
      obtain ⟨huv', hu, _, hv, _⟩ := (hK2 u v).1 huv
      simp only [Finset.mem_coe, Finset.mem_erase]
      rcases hT.1 huv' with h | h
      · left; exact ⟨hu, h⟩
      · right; exact ⟨hv, h⟩
    have hcard : (T.erase l).card + 1 = T.card := Finset.card_erase_add_one hlT
    have hmin : IsMinCover K2 (T.erase l) := by
      refine ⟨hcov, fun T'' h => ?_⟩
      have := hS.2 T'' h
      have := hS.2 _ hcov
      omega
    exact hqA _ hmin (Finset.mem_erase.2 ⟨hql, hqT⟩)

-- Case A: the free-leaf step of L-meta-539 applies with K' = K1.
theorem caseA {n : ℕ} (K K1 K2 : SimpleGraph (Fin n)) [DecidableRel K.Adj]
    [DecidableRel K1.Adj] [DecidableRel K2.Adj] (A : Finset (Fin n)) (l p q : Fin n)
    (hK_tf : ∀ a b c : Fin n, K.Adj a b → K.Adj b c → K.Adj c a → False)
    (hA : ∀ a ∈ A, ∀ v : Fin n, ¬ K.Adj a v) (hlp : ∀ v, K.Adj l v ↔ v = p) (hql : q ≠ l)
    (hpq : ∀ v, K.Adj p v ↔ v = l ∨ v = q)
    (hK1 : ∀ u v, K1.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ v ≠ l)
    (hK2 : ∀ u v, K2.Adj u v ↔ K.Adj u v ∧ u ≠ l ∧ u ≠ p ∧ v ≠ l ∧ v ≠ p)
    (hIH1 : ∀ C : Circuit, (IsMinimalCircuit n C ∧ circuitFun n C = graphFun K1 A) ↔
      IsNestedCoverCircuit n K1 A C)
    (hqA : ∀ T2, IsMinCover K2 T2 → q ∉ T2) (C : Circuit) :
    (IsMinimalCircuit n C ∧ circuitFun n C = graphFun K A) ↔ IsNestedCoverCircuit n K A C := by
  have hfree := free_of_caseA hlp hql hpq hK2 hqA
  exact ⟨fun ⟨hmin, hfun⟩ => main_dir_fwd K K1 A l p hK_tf hA hlp hfree hK1 hIH1 C hmin hfun,
    fun hC => main_dir_bwd K K1 A l p hA hlp hfree hK1 hIH1 C hC⟩

end PEqualNP.Outside.L_meta_540_aux
