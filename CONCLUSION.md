# Conclusion (provisional)

This project began as a strong hypothesis and is reported here at the honest size
the evidence supports — no larger.

**Initial hypothesis.** BH introduces a new, general paradigm of representation.

**Result of the investigation.** That hypothesis was **not confirmed**. The
principles it leaned on — a shared substrate stored once, and selective reading
over it — already appear, in mature form, across many domains (DICOM, COG/STAC,
lakeFS, CRAM/tabix, S-LoRA, MAM, …). As a *general paradigm*, BH is not novel.

**What remained.** A recurring property around the representation of
**concurrent, possibly contradictory interpretations** over one shared substrate.
It appears in some specific domains — notably **RDF named graphs (+ provenance)**
and **standoff annotation** — but has no uniform, named treatment across them. We
give it a working name: the *First-Class Interpretation Representation (FCIR)*.

**Current status.** There is **not yet sufficient evidence** that this property
constitutes a *new* concept. The most defensible contribution at this moment is
to treat it as a proposal of **synthesis and classification** — a cross-domain
name plus a falsifiable test — subject to further validation. Where existing
systems already implement it, this report says so (see
[`BH_PRINCIPLE.md`](BH_PRINCIPLE.md#how-fcir-relates-to-adjacent-systems)).

---

## The conclusion, in three lines

> - BH **as a universal paradigm of representation** was **not confirmed**;
> - BH surfaced a **recurring representation property** worth study, whose
>   **novelty is not established**;
> - the work remains valid **as investigation and as method**, independent of
>   whether the property turns out to be novel.

This is a strong conclusion precisely because it is compatible with everything
observed. It does not overstate what was found, and it does not discard the work
done.

## What the research is, regardless

A hypothesis was pursued, pressure-tested, and cut down to what survived:
hypotheses tested, counter-examples sought, scope reduced when the evidence
demanded it, contrary evidence incorporated rather than explained away. The
honest win is **the method** as much as any single finding — and a measured trail
with its boundaries and its prior art named in public.

## Responding to external critique (DeepSeek review, 2026-06)

An external model-based review raised five points. Two were already addressed in
this repo (immutability is not new → the prior-art confrontation in
[`BH_PRINCIPLE.md`](BH_PRINCIPLE.md#how-fcir-relates-to-adjacent-systems); the
20-domain method → [`applicability/`](applicability/)). Three were fair and are
addressed here:

**(a) "No formal algebra → a pattern, not a model."** Addressed in
[`BH_ALGEBRA.md`](BH_ALGEBRA.md): the operators (`⊕` coexistence, `Δ` conflict,
`σ` projection, `α` adjudication, `▷` precedence, `∘` composition), the laws, and
**FCIR stated formally as the decoupling of coexistence from adjudication**
(`⊕ ⊥ α`). It is a specification, not yet a verified theory.

**(b) Trade-offs (the costs, honestly).** The family is not free:
immutability → monotonic storage growth, needing compaction/GC and
content-addressing; co-registration → interpretations must address substrate
elements stably, so substrate re-addressing breaks layers (the standoff
"offset-drift" problem); preserving conflict → read-time adjudication is
`O(layers)` per address. None of these are solved here — they are the known costs
of the immutable-substrate family.

**(c) Comparison to real tools, not naive baselines.** The prototype numbers are
vs a *naive flat store*, not vs SOTA. Said plainly: **against the real tools the
prototypes do not win.** `bhanno` is standoff annotation (brat / Label Studio /
Web Annotation do it better and at scale); `bhckpt`'s selective load is what
`safetensors` / S-LoRA already ship; `bhmem` sits below Mem0 / Zep. The
prototypes are **illustrations of the property, not competitors**; the claim is
the property + the test, not the implementations.

**(d) Where it would actually help.** The most defensible use case is
**preserving and learning from disagreement** — *human label variation* in ML.
Pipelines today collapse many annotators into one gold label and discard the
disagreement, which a growing literature argues is real signal (ambiguity,
subjectivity, uncertainty) being thrown away. FCIR's narrow but concrete value:
keep every annotator's reading first-class and adjudicate **at read-time, per
consumer** (one model trains on majority, another on the full distribution, an
auditor inspects the conflict) — without forking the dataset. The usual gap is
not storage (standoff already stores layers) but the *pipeline* collapsing them
to gold. That gap, not the bytes, is the opportunity.

This does not make FCIR novel (see the prior-art confrontation). It makes the
critique part of the record.

## Paths from here (open)

None of these requires the original hypothesis to have been right:

- **Conclude** — report the investigation as-is; a finished inquiry.
- **Reposition** — treat BH as a *lens for studying representation properties*,
  not a format or an invention.
- **Use it** — take the parts that work and put them in software; not every
  concept needs to become a paper.

---

*Companion to [`BH_MASTER.md`](BH_MASTER.md) (the measured study),
[`applicability/`](applicability/) (the domain sweep) and
[`BH_PRINCIPLE.md`](BH_PRINCIPLE.md) (the FCIR confrontation). Provisional — it
should be revised if stronger evidence, for or against, appears.*
