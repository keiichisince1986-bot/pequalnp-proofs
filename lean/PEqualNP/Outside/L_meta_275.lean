import Mathlib
import PEqualNP.Defs

namespace PEqualNP.Outside.L_meta_275

open PEqualNP.CircuitLowerBounds

-- The four lines.
def L : Fin 4 → Finset (Fin 7) :=
  ![{0, 1, 2}, {0, 3, 4}, {0, 5, 6}, {1, 3, 5}]

-- Running a list of gates on a list of wire values: the fold inside the circuit.
def run (gs : List Gate) (w : List Bool) : List Bool :=
  gs.foldl (fun w g => w ++ [g.op.eval (g.inputs.map fun i => w.getD i false)]) w

theorem run_append (gs gs' : List Gate) (w : List Bool) :
    run (gs ++ gs') w = run gs' (run gs w) := by
  simp [run, List.foldl_append]

theorem run_prefix (gs : List Gate) : ∀ w : List Bool,
    ∃ t : List Bool, run gs w = w ++ t ∧ t.length = gs.length := by
  induction gs with
  | nil => intro w; exact ⟨[], by simp [run], rfl⟩
  | cons g gs ih =>
    intro w
    obtain ⟨t, ht, hl⟩ := ih (w ++ [g.op.eval (g.inputs.map fun i => w.getD i false)])
    refine ⟨g.op.eval (g.inputs.map fun i => w.getD i false) :: t, ?_, by simp [hl]⟩
    have : run (g :: gs) w
        = run gs (w ++ [g.op.eval (g.inputs.map fun i => w.getD i false)]) := rfl
    rw [this, ht]; simp

theorem length_run (gs : List Gate) (w : List Bool) :
    (run gs w).length = w.length + gs.length := by
  obtain ⟨t, ht, hl⟩ := run_prefix gs w
  rw [ht]; simp [hl]

theorem getD_run_lt (gs : List Gate) (w : List Bool) (i : ℕ) (h : i < w.length) :
    (run gs w).getD i false = w.getD i false := by
  obtain ⟨t, ht, _⟩ := run_prefix gs w
  rw [ht]; exact List.getD_append _ _ _ _ h

-- The value of wire `k` on input `x`.
def val (C : Circuit) (x : Fin 7 → Bool) (k : ℕ) : Bool :=
  (C.wires (List.ofFn x)).getD k false

theorem wires_eq (C : Circuit) (y : List Bool) : C.wires y = run C.gates y := rfl

theorem val_input (C : Circuit) (x : Fin 7 → Bool) (k : ℕ) (hk : k < 7) :
    val C x k = x ⟨k, hk⟩ := by
  unfold val
  rw [wires_eq, getD_run_lt _ _ _ (by simpa using hk),
    List.getD_eq_getElem _ _ (by simpa using hk), List.getElem_ofFn]

theorem val_beyond (C : Circuit) (x : Fin 7 → Bool) (k : ℕ) (hk : 7 + C.gates.length ≤ k) :
    val C x k = false := by
  unfold val
  rw [wires_eq]
  apply List.getD_eq_default
  rw [length_run]; simpa using hk

-- What a gate reads: earlier wires, and false elsewhere.
def rd (C : Circuit) (x : Fin 7 → Bool) (m i : ℕ) : Bool :=
  if i < m then val C x i else false

theorem val_gate (C : Circuit) (x : Fin 7 → Bool) (j : ℕ) (hj : j < C.gates.length) :
    val C x (7 + j) = (C.gates[j]).op.eval ((C.gates[j]).inputs.map (rd C x (7 + j))) := by
  have hsplit : C.gates = C.gates.take j ++ (C.gates[j] :: C.gates.drop (j + 1)) := by
    simp
  set P := run (C.gates.take j) (List.ofFn x) with hP
  have hPl : P.length = 7 + j := by
    rw [hP, length_run]; simp [List.length_take]; omega
  set g := C.gates[j]
  set v := g.op.eval (g.inputs.map fun i => P.getD i false) with hv
  have hW : C.wires (List.ofFn x) = run (C.gates.drop (j + 1)) (P ++ [v]) := by
    have h0 : run C.gates (List.ofFn x)
        = run (C.gates.take j ++ (g :: C.gates.drop (j + 1))) (List.ofFn x) := by
      rw [← hsplit]
    rw [wires_eq, h0, run_append]
    rfl
  have hread : ∀ i, P.getD i false = rd C x (7 + j) i := by
    intro i
    unfold rd
    split_ifs with hi
    · unfold val
      rw [hW, getD_run_lt (C.gates.drop (j + 1)) (P ++ [v]) i (by simp; omega),
        List.getD_append _ _ _ _ (by omega)]
    · exact List.getD_eq_default _ _ (by omega)
  have hval : val C x (7 + j) = v := by
    unfold val
    rw [hW, getD_run_lt (C.gates.drop (j + 1)) (P ++ [v]) (7 + j) (by simp; omega), ← hPl]
    simp
  rw [hval, hv]
  congr 2
  funext i
  exact hread i

-- An AND/OR gate of fan-in two.
def AO (C : Circuit) : Prop :=
  ∀ g ∈ C.gates, (g.op = GateOp.and ∨ g.op = GateOp.or) ∧ g.inputs.length = 2

theorem two_inputs (g : Gate) (h : g.inputs.length = 2) : ∃ a b, g.inputs = [a, b] := by
  match hi : g.inputs, h with
  | [a, b], _ => exact ⟨a, b, rfl⟩

theorem eval_and (g : Gate) (a b : ℕ) (hi : g.inputs = [a, b]) (hop : g.op = GateOp.and)
    (F : ℕ → Bool) : g.op.eval (g.inputs.map F) = (F a && F b) := by
  rw [hi, hop]; simp [GateOp.eval]

theorem eval_or (g : Gate) (a b : ℕ) (hi : g.inputs = [a, b]) (hop : g.op = GateOp.or)
    (F : ℕ → Bool) : g.op.eval (g.inputs.map F) = (F a || F b) := by
  rw [hi, hop]; simp [GateOp.eval]

theorem rd_mono (C : Circuit) (x y : Fin 7 → Bool) (m : ℕ)
    (ih : ∀ i < m, val C x i = true → val C y i = true) (i : ℕ) :
    rd C x m i = true → rd C y m i = true := by
  unfold rd
  split_ifs with h
  · exact ih i h
  · exact id

theorem val_mono (C : Circuit) (hC : AO C) (x y : Fin 7 → Bool)
    (hxy : ∀ q, x q = true → y q = true) :
    ∀ k, val C x k = true → val C y k = true := by
  intro k
  induction k using Nat.strong_induction_on with
  | _ k ih =>
    intro hk
    by_cases h1 : k < 7
    · rw [val_input _ _ _ h1] at hk ⊢; exact hxy _ hk
    by_cases h2 : 7 + C.gates.length ≤ k
    · rw [val_beyond _ _ _ h2] at hk; exact absurd hk (by simp)
    obtain ⟨j, rfl⟩ : ∃ j, k = 7 + j := ⟨k - 7, by omega⟩
    have hj : j < C.gates.length := by omega
    rw [val_gate _ _ _ hj] at hk ⊢
    obtain ⟨hop, hl⟩ := hC _ (List.getElem_mem hj)
    obtain ⟨a, b, hab⟩ := two_inputs _ hl
    have hm := rd_mono C x y (7 + j) ih
    rcases hop with hop | hop
    · rw [eval_and _ _ _ hab hop] at hk ⊢
      simp only [Bool.and_eq_true] at hk ⊢
      exact ⟨hm _ hk.1, hm _ hk.2⟩
    · rw [eval_or _ _ _ hab hop] at hk ⊢
      simp only [Bool.or_eq_true] at hk ⊢
      exact hk.imp (hm _) (hm _)

-- The unit vector at `p`.
def e (p : Fin 7) : Fin 7 → Bool := fun q => decide (q = p)

theorem val_e_input (C : Circuit) (p : Fin 7) (k : ℕ) (hk : k < 7) :
    val C (e p) k = true ↔ (⟨k, hk⟩ : Fin 7) = p := by
  rw [val_input _ _ _ hk]; simp [e]

-- Finite facts about the four lines.
theorem lines_meet : ∀ i i' : Fin 4, ∀ p q : Fin 7, p ≠ q → p ∈ L i → q ∈ L i →
    p ∈ L i' → q ∈ L i' → i = i' := by
  decide

theorem line_three : ∀ i : Fin 4, ∃ p q r : Fin 7, p ≠ q ∧ p ≠ r ∧ q ≠ r ∧
    p ∈ L i ∧ q ∈ L i ∧ r ∈ L i := by
  decide

-- A wire is good for line `i`: a gate whose single points lie in the line, at least two of them.
def Good (C : Circuit) (i : Fin 4) (m : ℕ) : Prop :=
  7 ≤ m ∧ m < 7 + C.gates.length ∧ (∀ p, val C (e p) m = true → p ∈ L i) ∧
    ∃ p q, p ≠ q ∧ val C (e p) m = true ∧ val C (e q) m = true

theorem good_of (C : Circuit) (i : Fin 4) (m : ℕ) (hm : m < 7 + C.gates.length)
    (hin : ∀ p, val C (e p) m = true → p ∈ L i)
    (htwo : ∃ p q, p ≠ q ∧ val C (e p) m = true ∧ val C (e q) m = true) : Good C i m := by
  refine ⟨?_, hm, hin, htwo⟩
  by_contra h
  push Not at h
  obtain ⟨p, q, hpq, hp, hq⟩ := htwo
  rw [val_e_input _ _ _ h] at hp hq
  exact hpq (hp.symm.trans hq)

theorem good_unique (C : Circuit) (i i' : Fin 4) (m : ℕ) (h : Good C i m) (h' : Good C i' m) :
    i = i' := by
  obtain ⟨-, -, hin, p, q, hpq, hp, hq⟩ := h
  obtain ⟨-, -, hin', -⟩ := h'
  exact lines_meet i i' p q hpq (hin p hp) (hin q hq) (hin' p hp) (hin' q hq)

-- Pigeonhole for an OR gate: three points of the line, two operands.
theorem or_split (i : Fin 4) (ra rb : Fin 7 → Bool)
    (h : ∀ p, (ra p || rb p) = true ↔ p ∈ L i) :
    (∃ p q, p ≠ q ∧ ra p = true ∧ ra q = true) ∨ (∃ p q, p ≠ q ∧ rb p = true ∧ rb q = true) := by
  obtain ⟨p, q, r, hpq, hpr, hqr, hp, hq, hr⟩ := line_three i
  have hp' := (h p).2 hp
  have hq' := (h q).2 hq
  have hr' := (h r).2 hr
  simp only [Bool.or_eq_true] at hp' hq' hr'
  cases hap : ra p <;> cases haq : ra q <;> cases har : ra r <;>
    simp only [hap, haq, har, false_or, Bool.false_eq_true] at hp' hq' hr'
  · exact Or.inr ⟨p, q, hpq, hp', hq'⟩
  · exact Or.inr ⟨p, q, hpq, hp', hq'⟩
  · exact Or.inr ⟨p, r, hpr, hp', hr'⟩
  · exact Or.inl ⟨q, r, hqr, haq, har⟩
  · exact Or.inr ⟨q, r, hqr, hq', hr'⟩
  · exact Or.inl ⟨p, r, hpr, hap, har⟩
  · exact Or.inl ⟨p, q, hpq, hap, haq⟩
  · exact Or.inl ⟨p, q, hpq, hap, haq⟩

-- The output of line `i` and a second good wire below it.
theorem two_good (C : Circuit) (hC : AO C) (i : Fin 4) (o : ℕ)
    (hone : ∀ p, val C (e p) o = true ↔ p ∈ L i)
    (hlight : ∀ x : Fin 7 → Bool, (Finset.univ.filter (fun q => x q = true)).card ≤ 2 →
      (∀ q ∈ L i, x q = false) → val C x o = false) :
    Good C i o ∧ ∃ m, m < o ∧ Good C i m := by
  obtain ⟨p0, q0, r0, hpq0, -, -, hp0, hq0, -⟩ := line_three i
  have hlt : o < 7 + C.gates.length := by
    by_contra h
    push Not at h
    have := (hone p0).2 hp0
    rw [val_beyond _ _ _ h] at this
    exact absurd this (by simp)
  have hgood : Good C i o :=
    good_of C i o hlt (fun p hp => (hone p).1 hp)
      ⟨p0, q0, hpq0, (hone p0).2 hp0, (hone q0).2 hq0⟩
  refine ⟨hgood, ?_⟩
  obtain ⟨j, rfl⟩ : ∃ j, o = 7 + j := ⟨o - 7, by have := hgood.1; omega⟩
  have hj : j < C.gates.length := by omega
  obtain ⟨hop, hl⟩ := hC _ (List.getElem_mem hj)
  obtain ⟨a, b, hab⟩ := two_inputs _ hl
  -- an operand read true somewhere is an earlier wire
  have hread : ∀ (c : ℕ) (x : Fin 7 → Bool), rd C x (7 + j) c = true →
      c < 7 + j ∧ val C x c = true := by
    intro c x h
    unfold rd at h
    split_ifs at h with hc
    · exact ⟨hc, h⟩
  have hgood_c : ∀ c : ℕ, (∀ p, rd C (e p) (7 + j) c = true → p ∈ L i) →
      (∃ p q, p ≠ q ∧ rd C (e p) (7 + j) c = true ∧ rd C (e q) (7 + j) c = true) →
      ∃ m, m < 7 + j ∧ Good C i m := by
    intro c hin htwo
    obtain ⟨p, q, hpq, hp, hq⟩ := htwo
    obtain ⟨hc, hp'⟩ := hread c _ hp
    obtain ⟨-, hq'⟩ := hread c _ hq
    refine ⟨c, hc, good_of C i c (by omega) ?_ ⟨p, q, hpq, hp', hq'⟩⟩
    intro r hr
    apply hin r
    unfold rd; simp only [hc, ↓reduceIte]; exact hr
  rcases hop with hop | hop
  · -- AND: both operands cover the line
    have hval : ∀ x, val C x (7 + j) = (rd C x (7 + j) a && rd C x (7 + j) b) := by
      intro x; rw [val_gate _ _ _ hj, eval_and _ _ _ hab hop]
    have hA : ∀ p ∈ L i, rd C (e p) (7 + j) a = true := by
      intro p hp; have := (hone p).2 hp; rw [hval] at this
      simp only [Bool.and_eq_true] at this; exact this.1
    have hB : ∀ p ∈ L i, rd C (e p) (7 + j) b = true := by
      intro p hp; have := (hone p).2 hp; rw [hval] at this
      simp only [Bool.and_eq_true] at this; exact this.2
    by_cases ha : ∀ p, rd C (e p) (7 + j) a = true → p ∈ L i
    · exact hgood_c a ha ⟨p0, q0, hpq0, hA p0 hp0, hA q0 hq0⟩
    by_cases hb : ∀ p, rd C (e p) (7 + j) b = true → p ∈ L i
    · exact hgood_c b hb ⟨p0, q0, hpq0, hB p0 hp0, hB q0 hq0⟩
    exfalso
    push Not at ha hb
    obtain ⟨x, hxa, hxL⟩ := ha
    obtain ⟨y, hyb, hyL⟩ := hb
    by_cases hxy : x = y
    · subst hxy
      apply hxL
      apply (hone x).1
      rw [hval]; simp [hxa, hyb]
    -- the light input with the two points x and y
    let z : Fin 7 → Bool := fun q => decide (q = x) || decide (q = y)
    have hz := hlight z ?_ ?_
    · rw [hval] at hz
      obtain ⟨hca, hva⟩ := hread a _ hxa
      obtain ⟨hcb, hvb⟩ := hread b _ hyb
      have hza : val C z a = true :=
        val_mono C hC (e x) z (fun q hq => by simp [e] at hq; simp [z, hq]) a hva
      have hzb : val C z b = true :=
        val_mono C hC (e y) z (fun q hq => by simp [e] at hq; simp [z, hq]) b hvb
      unfold rd at hz
      simp only [hca, hcb, ↓reduceIte, hza, hzb] at hz
      exact absurd hz (by simp)
    · have hsub : Finset.univ.filter (fun q => z q = true) ⊆ {x, y} := by
        intro q hq
        simp only [Finset.mem_filter, Finset.mem_univ, true_and, z, Bool.or_eq_true,
          decide_eq_true_eq] at hq
        rcases hq with hq | hq <;> simp [hq]
      exact (Finset.card_le_card hsub).trans (Finset.card_le_two)
    · intro q hq
      simp only [z, Bool.or_eq_false_iff, decide_eq_false_iff_not]
      exact ⟨fun h => hxL (h ▸ hq), fun h => hyL (h ▸ hq)⟩
  · -- OR: one operand holds two points of the line
    have hval : ∀ x, val C x (7 + j) = (rd C x (7 + j) a || rd C x (7 + j) b) := by
      intro x; rw [val_gate _ _ _ hj, eval_or _ _ _ hab hop]
    have hiff : ∀ p, (rd C (e p) (7 + j) a || rd C (e p) (7 + j) b) = true ↔ p ∈ L i := by
      intro p; rw [← hval]; exact hone p
    have hinA : ∀ p, rd C (e p) (7 + j) a = true → p ∈ L i := by
      intro p hp; exact (hiff p).1 (by simp [hp])
    have hinB : ∀ p, rd C (e p) (7 + j) b = true → p ∈ L i := by
      intro p hp; exact (hiff p).1 (by simp [hp])
    rcases or_split i _ _ hiff with h | h
    · exact hgood_c a hinA h
    · exact hgood_c b hinB h

end PEqualNP.Outside.L_meta_275

theorem PEqualNP.Outside.L_meta_275 : ¬ ∃ (C : PEqualNP.CircuitLowerBounds.Circuit) (o : Fin 4 → ℕ), C.size ≤ 7 ∧ (∀ g ∈ C.gates, (g.op = PEqualNP.CircuitLowerBounds.GateOp.and ∨ g.op = PEqualNP.CircuitLowerBounds.GateOp.or) ∧ g.inputs.length = 2) ∧ ∀ i : Fin 4, (∀ p : Fin 7, (C.wires (List.ofFn (fun q : Fin 7 => decide (q = p)))).getD (o i) false = true ↔ p ∈ (![{0, 1, 2}, {0, 3, 4}, {0, 5, 6}, {1, 3, 5}] : Fin 4 → Finset (Fin 7)) i) ∧ ∀ x : Fin 7 → Bool, (Finset.univ.filter (fun q : Fin 7 => x q = true)).card ≤ 2 → (∀ q ∈ (![{0, 1, 2}, {0, 3, 4}, {0, 5, 6}, {1, 3, 5}] : Fin 4 → Finset (Fin 7)) i, x q = false) → (C.wires (List.ofFn x)).getD (o i) false = false := by
  rintro ⟨C, o, hsize, hC, hout⟩
  have hgood : ∀ i : Fin 4, PEqualNP.Outside.L_meta_275.Good C i (o i) ∧
      ∃ m, m < o i ∧ PEqualNP.Outside.L_meta_275.Good C i m :=
    fun i => PEqualNP.Outside.L_meta_275.two_good C hC i (o i) (hout i).1 (hout i).2
  choose hg m hm hgm using hgood
  -- eight distinct good wires among the gates
  let f : Fin 4 × Bool → ℕ := fun ib => if ib.2 then o ib.1 else m ib.1
  have hf : ∀ ib, PEqualNP.Outside.L_meta_275.Good C ib.1 (f ib) := by
    rintro ⟨i, b⟩; cases b
    · exact hgm i
    · exact hg i
  have hinj : Function.Injective f := by
    rintro ⟨i, b⟩ ⟨i', b'⟩ h
    have hii : i = i' := PEqualNP.Outside.L_meta_275.good_unique C i i' _ (hf ⟨i, b⟩)
      (h ▸ hf ⟨i', b'⟩)
    subst hii
    have hlt := hm i
    cases b <;> cases b' <;> simp [f] at h ⊢ <;> omega
  have hrange : ∀ ib, f ib ∈ Finset.Ico 7 (7 + C.gates.length) := by
    intro ib
    obtain ⟨h1, h2, -⟩ := hf ib
    exact Finset.mem_Ico.2 ⟨h1, h2⟩
  have hcard := Finset.card_le_card_of_injOn (s := (Finset.univ : Finset (Fin 4 × Bool)))
    f (fun ib _ => hrange ib) hinj.injOn
  simp at hcard
  have : C.size = C.gates.length := rfl
  omega
