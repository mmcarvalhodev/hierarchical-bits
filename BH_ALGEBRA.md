# An algebra of interpretations (FCIR)

> Written in response to a fair external critique: *"without a formal algebra of
> how interpretations interact — composition, conflict, resolution, precedence —
> the proposal stays at the level of a design pattern, not a model."* This is the
> attempt to answer it. It is a **specification**, not a mechanized or proven
> theory (see *Honest limits*).

The whole point of FCIR is that adjudication is **deferred and optional**. An
algebra makes that precise: it says exactly which operators a representation must
provide, and which law makes it FCIR rather than something adjacent.

## Objects

- **Substrate** `S` — an immutable set of addressable elements. `A` is its
  address space (ids, offsets, node paths, coordinates). `S` is never written.
- **Value/claim space** `V` — what an interpretation can assert about an address
  (a label, a value, a mask, a relation, a fact).
- **Interpretation** `I = (id, src, t, π)` — a first-class entity with identity
  `id`, provenance `src`, time `t`, and a **partial** map `π : A ⇀ V` (defined
  only on the addresses it speaks about).
- **Interpretation set** `𝓘(S)` — the interpretations currently co-registered
  to `S`. This set is the stored state.

## Operators

1. **Coexistence** `⊕` (the primary operator) — `𝓘 ⊕ I = 𝓘 ∪ {I}`.
   Non-destructive union. Adding an interpretation never alters or removes
   another. This is the operator most systems *lack* in non-destructive form.

2. **Restriction** `I|_{A'}` — `I` narrowed to addresses `A' ⊆ A`.

3. **Conflict** `Δ` (a query, not a mutation) — for two interpretations,
   `Δ(I₁, I₂) = { a ∈ dom π₁ ∩ dom π₂ : π₁(a) ≠ π₂(a) }`;
   over a set, `Δ(𝓘) = ⋃_{i<j} Δ(Iᵢ, Iⱼ)`. Detects disagreement **without
   resolving it**.

4. **Projection / lens** `σ` (read-only view) — `σ_φ(𝓘)` reads `S` through the
   interpretations selected by filter `φ` (one `id`, one `src`, a time window).
   `σ` returns a view; it does not change `𝓘`.

5. **Adjudication** `α_p` (read-time, **optional**, policy-parameterized) — at an
   address `a`, `α_p(𝓘, a)` maps the multiset of claims `{ π_i(a) }` to a single
   value **or** the explicit symbol `⊥` ("undecided"). Policies `p`:
   `majority`, `priority(<)` (a precedence order over sources), `latest`,
   `trust(w)`, `unanimous` (returns `⊥` iff there is conflict). `α_p` is a
   **function over the stored set**; it never mutates `𝓘`.

6. **Precedence / override** `▷` (derived view, non-commutative) — `I₁ ▷ I₂` is
   the reading in which `I₁` wins where the two overlap. It is sugar for
   `α_{priority(I₁ < I₂)}`; both interpretations remain in `𝓘`.

7. **Composition / stacking** `∘` — an interpretation may take **another
   interpretation as its substrate** (a review of annotator A's labels; a meta
   layer). `I_meta : dom(I_A) ⇀ V`. This yields a finite stack; it is the least
   developed operator (see limits).

8. **Provenance** `prov(I) = (src, t)` — carried by every interpretation,
   preserved by `⊕`, `σ`, `α`, `▷`.

## Laws and invariants

- **(L1) Substrate immutability.** No operator writes to `S`.
- **(L2) `⊕` is a commutative, associative monoid** with identity `∅` (the empty
  interpretation), and idempotent on identical `id` (set semantics).
- **(L3) Non-destruction.** `σ`, `α`, `▷`, `Δ` are read-only: the stored set is
  invariant under them. `view(𝓘) ⇒ 𝓘 unchanged`.
- **(L4) Conflict monotonicity.** `Δ(𝓘 ⊕ I) ⊇ Δ(𝓘)` — adding interpretations can
  only add conflicts, never silently erase them.
- **(L5) Adjudication separability.** `α_p` is definable as a pure function of
  `(𝓘, a, p)`. The stored set does **not** depend on `p`; changing the policy
  changes only the view. This is the heart.

## The FCIR test, made formal

> A representation `R` is **FCIR** iff its coexistence `⊕` is non-destructive
> (L3) **and** its adjudication `α` is separable (L5) — i.e. **`⊕` and `α` are
> independent operators**.

Equivalently: *you can add a contradicting interpretation and still read every
prior one unchanged, and you can change how you resolve conflicts without
rewriting anything.*

This turns the earlier prose test ("can two readings of the same element both
remain until a reader chooses to adjudicate?") into an algebraic property, and it
**explains the prior-art verdicts as facts about coupling**:

| system | `⊕` and `α` | FCIR? |
|---|---|---|
| **RDF named graphs + PROV** | decoupled: `⊕` = add a graph; `α` = query-time choice | **yes** |
| **Standoff annotation** | decoupled: `⊕` = add a layer; `α` = optional gold/consensus pass | **yes** |
| Git / branches | coupled: a branch defers `α`, but the model drives toward `merge` (= `α` at integration time); unmerged = divergent copies | no |
| CRDTs | coupled: `α` is **baked into** `⊕` (deterministic auto-convergence) | no |
| Event sourcing | single truth: projections are `σ` over one history; no rival `α` | no |
| Bitemporal / Datomic | coupled to time: `α` = temporal order; supersession, not co-equal rivals | partial |

So FCIR is not "we invented coexistence." It is: **the property is exactly the
decoupling of `⊕` from `α`, and that decoupling already exists in named graphs
and standoff annotation — but is absent from the systems people reach for by
default** (Git, CRDTs, event sourcing, bitemporal stores).

## What the algebra buys

- It moves FCIR from *pattern* to *model*: a named set of operators with laws and
  a single defining property (L3 ∧ L5).
- It makes the test **mechanically checkable**: implement `⊕`, `Δ`, `α_p`; verify
  L3 (views don't mutate) and L5 (policy is a read-time parameter).
- It **predicts**, rather than asserts, which systems qualify — and why.

## Honest limits

- This is a **specification, not a verified theory.** There are no consistency,
  soundness, or complexity results here, and no mechanized proofs.
- **Composition (`∘`) is under-specified** — interpretation-of-interpretation
  needs a typing discipline to avoid paradox; only the finite-stack case is
  sketched.
- **No implementation realizes the full algebra.** `bhanno` implements a
  fragment: `⊕`, `Δ`, and `α_majority` / `α_unanimous`. The other prototypes use
  even less of it.
- The algebra **does not establish novelty.** Named graphs and standoff
  annotation satisfy L3 ∧ L5 already; the algebra's contribution is to *state the
  property precisely and cross-domain*, not to claim it is new.

In short: this answers *"is there a model, or just a pattern?"* with **"here is a
model, written as a specification"** — while being explicit that a specification
is not yet a proven theory, and that the property it formalizes is, in two
domains, already implemented.
