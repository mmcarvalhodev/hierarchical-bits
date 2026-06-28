# Disagreement-aware ML — does *not collapsing on write* add predictive value?

**Status: positive, scoped.** Preserving annotator disagreement as a soft training
target (FCIR's "do not collapse on write") predicts the human label distribution
**measurably better** than collapsing to a gold label — and better than generic
label smoothing — on ChaosNLI. The effect is modest (~7% JSD) and concentrated
where disagreement is highest. This is evidence the discipline carries predictive
signal, not only provenance.

This is the §3.2 test from the second external critique, run with one design
correction made **before** the experiment.

## The correction (declared before running)

The critique proposed *disagreement entropy as an input feature*. That is an
**oracle feature**: entropy is a function of the human annotation distribution,
whose majority *is* the gold label; a fresh example at deployment has no
annotations, so the feature cannot exist. A gain from it would not survive review.

We instead test what FCIR actually claims. "Collapse on write" has a direct ML
translation — discard the distribution, keep the majority:

| condition | training target | meaning |
|---|---|---|
| **HARD** | one-hot(majority) | collapse on write (the baseline) |
| **SMOOTH** | hard + ε=0.1 uniform smoothing | generic regularizer — the control |
| **SOFT** | full human label distribution | FCIR: keep the disagreement |

All three see **only premise + hypothesis** at test time — no oracle feature. The
only thing that differs is whether training kept or destroyed the disagreement.
`SMOOTH` is there so a win for `SOFT` cannot be dismissed as "any smoothing helps."

## Setup

- **Data:** ChaosNLI (Nie et al., 2020) — SNLI 1514 + MNLI-m 1599 = 3113 examples,
  ~100 human annotations each, examples *selected because* they cause disagreement
  (a hard test on purpose). Real disagreement → closes the "synthetic is circular"
  objection.
- **Base (identical across conditions):** frozen `all-MiniLM-L6-v2` embeddings of
  premise & hypothesis → features `[u, v, |u−v|, u·v]` → small MLP head. Freezing
  the base isolates the variable: *only the training target changes.*
- **Protocol:** 5-fold CV × 5 seeds. Metrics: majority-label accuracy; **JSD to the
  human distribution** (ChaosNLI's own metric); broken out by entropy quartile.

## Pre-registered criteria (written before the run, no post-hoc changes)

- **H1** — SOFT has lower mean JSD than **both** HARD and SMOOTH, paired Wilcoxon p<0.05.
- **H2** — no accuracy tax: SOFT majority-accuracy ≥ HARD − 1.0 pt.
- **Success = H1 ∧ H2.** Null/failure (H1 false or accuracy drops materially) would
  mean FCIR's value here is provenance/auditability, **not** predictive signal.

## Result

```
cond       maj-acc   JSD(mean)
hard        50.14%      0.1526
smooth      50.04%      0.1513
soft        51.10%      0.1416
```

| test | outcome |
|---|---|
| H1: soft vs hard | dJSD = −0.0110, p ≈ 1e-30 → **SOFT better** |
| H1: soft vs smooth | dJSD = −0.0098, p ≈ 2e-37 → **SOFT better** (beats generic smoothing) |
| H2: accuracy tax | hard − soft = **−0.96 pt** (soft is *higher*) → no tax |
| effect by quartile | dJSD(soft−smooth): Q1 −0.005 · Q2 −0.007 · Q3 −0.013 · **Q4 −0.015** |

**VERDICT: H1 PASS, H2 PASS** — preserving disagreement adds predictive value, and
the value grows monotonically with how contested the example is.

## Honest boundary (the same discipline as the rest of the repo)

- **Effect size is modest.** JSD 0.1526 → 0.1416 is ~7% relative. The p-values are
  tiny because n = 3113 paired, not because the effect is large — read the effect
  size, not the stars. It is real, monotonic in disagreement, and beats the
  smoothing control; it is not a landslide.
- **What this proves, scoped:** *the signal* preserved by not collapsing has
  predictive value on a disagreement-rich NLI benchmark. **What it does not prove:**
  that *FCIR the mechanism* is necessary — soft-label / learning-with-disagreement
  is known in the literature (Pavlick & Kwiatkowski 2019; Nie et al. 2020; Uma et
  al. 2021). What this adds is tying it explicitly to "don't collapse on write,"
  showing it beats *generic* smoothing, and that the gain tracks disagreement.
- **Base is deliberately weak** (frozen bi-encoder, ~50% on hard ChaosNLI) to
  isolate the supervision variable — not a SOTA accuracy claim. A fine-tuned
  cross-encoder would raise all three conditions; the *contrast* is the result.
- **Train and test are both ChaosNLI** (high-disagreement-selected) via CV;
  generalization to the ordinary NLI distribution is untested.

## Reproduce

```
X:/miniconda3/python.exe X:/bitH/directions/disagreement_ml/run.py
# downloads ChaosNLI on first run (~0.5 MB); embeddings cached to _emb_cache.npz
```

*Reference: Nie, Zhou & Bansal, "What Can We Learn from Collective Human Opinions
on Natural Language Inference Data?" (EMNLP 2020) — the ChaosNLI dataset.*
