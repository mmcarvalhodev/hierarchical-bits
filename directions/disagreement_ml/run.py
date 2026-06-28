"""Disagreement-aware ML — does preserving disagreement (FCIR's 'do not collapse
on write') add *predictive* value over collapsing to a gold label?

This is the §3.2 test from the second external critique, with one methodological
correction stated BEFORE running:

  The critique proposed "disagreement entropy as an input feature." That is an
  ORACLE feature — entropy is a function of the human annotation distribution,
  whose majority IS the gold label; at deployment a fresh example has no
  annotations, so the feature does not exist. Reporting a gain from it is not
  defensible. We instead test the thing FCIR actually claims:

      COLLAPSE (hard) : train on majority label only      (one-hot target)
      SMOOTH   (ctrl) : hard label + fixed eps smoothing   (generic regularizer)
      PRESERVE (soft) : train on the full human label dist (FCIR: keep disagreement)

  Both models see ONLY premise+hypothesis at test time (no oracle feature). The
  only thing that differs is whether training kept or destroyed the disagreement.
  SMOOTH exists so a win for SOFT cannot be dismissed as "any label smoothing".

PRE-REGISTERED CRITERIA (written before the run, no post-hoc changes):
  Dataset : ChaosNLI (SNLI 1514 + MNLI_m 1599), ~100 annotations/example.
  Base    : frozen all-MiniLM-L6-v2 embeddings of premise & hypothesis,
            features [u, v, |u-v|, u*v]; identical across the 3 conditions.
            Only the training TARGET changes -> isolates the variable.
  Head    : small MLP (-> 3-class softmax). 5-fold CV x 5 seeds.
  Metrics : majority-label accuracy; JSD(model || human dist) [ChaosNLI's metric];
            broken out by entropy quartile.
  SUCCESS (H1 and H2):
    H1  SOFT has lower mean JSD than BOTH hard and smooth, paired Wilcoxon p<0.05.
    H2  no accuracy tax: SOFT majority-acc >= HARD - 1.0 pt.
  NULL/FAIL: H1 false, or accuracy drops materially. Then FCIR's value here is
    provenance/auditability, not predictive signal -- reported as such.

Run:  X:/miniconda3/python.exe X:/bitH/directions/disagreement_ml/run.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from scipy.spatial.distance import jensenshannon
from scipy.stats import wilcoxon

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "chaosNLI_v1.0"
CACHE = HERE / "_emb_cache.npz"           # gitignored
CLASSES = ["e", "n", "c"]                  # ChaosNLI label_dist order: [entail, neutral, contra]
N_FOLDS, N_SEEDS = 5, 5
EPS_SMOOTH = 0.1
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


def load_examples() -> list[dict]:
    rows = []
    for fn in ("chaosNLI_snli.jsonl", "chaosNLI_mnli_m.jsonl"):
        for line in (DATA / fn).read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            rows.append({
                "premise": d["example"]["premise"],
                "hypothesis": d["example"]["hypothesis"],
                "dist": np.asarray(d["label_dist"], dtype=np.float64),   # [e,n,c]
                "majority": CLASSES.index(d["majority_label"]),
                "entropy": float(d["entropy"]),
            })
    return rows


def build_features(rows: list[dict]) -> np.ndarray:
    if CACHE.exists():
        return np.load(CACHE)["X"]
    from sentence_transformers import SentenceTransformer
    m = SentenceTransformer("all-MiniLM-L6-v2", device=DEVICE)
    prem = m.encode([r["premise"] for r in rows], batch_size=128,
                    convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    hyp = m.encode([r["hypothesis"] for r in rows], batch_size=128,
                   convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False)
    X = np.concatenate([prem, hyp, np.abs(prem - hyp), prem * hyp], axis=1).astype(np.float32)
    np.savez_compressed(CACHE, X=X)
    return X


class Head(nn.Module):
    def __init__(self, d: int) -> None:
        super().__init__()
        self.net = nn.Sequential(nn.Linear(d, 256), nn.ReLU(), nn.Dropout(0.3), nn.Linear(256, 3))

    def forward(self, x):
        return self.net(x)


def _targets(rows, idx, kind):
    if kind == "hard":
        t = np.zeros((len(idx), 3))
        t[np.arange(len(idx)), [rows[i]["majority"] for i in idx]] = 1.0
    elif kind == "smooth":
        t = np.full((len(idx), 3), EPS_SMOOTH / 3)
        for r, i in enumerate(idx):
            t[r, rows[i]["majority"]] += 1.0 - EPS_SMOOTH
    else:  # soft = human distribution
        t = np.stack([rows[i]["dist"] for i in idx])
        t = t / t.sum(1, keepdims=True)
    return torch.tensor(t, dtype=torch.float32, device=DEVICE)


def train_eval(X, rows, tr, te, kind, seed):
    torch.manual_seed(seed)
    Xtr = torch.tensor(X[tr], device=DEVICE)
    Xte = torch.tensor(X[te], device=DEVICE)
    Ttr = _targets(rows, tr, kind)
    model = Head(X.shape[1]).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=1e-3, weight_decay=1e-4)
    logsm = nn.LogSoftmax(dim=1)
    model.train()
    for _ in range(60):                       # KL/cross-entropy to (soft) target
        opt.zero_grad()
        loss = -(Ttr * logsm(model(Xtr))).sum(1).mean()
        loss.backward()
        opt.step()
    model.eval()
    with torch.no_grad():
        pred = torch.softmax(model(Xte), dim=1).cpu().numpy()
    maj = np.array([rows[i]["majority"] for i in te])
    acc = float((pred.argmax(1) == maj).mean())
    human = np.stack([rows[i]["dist"] for i in te])
    human = human / human.sum(1, keepdims=True)
    jsd = np.array([jensenshannon(pred[k], human[k], base=2) ** 2 for k in range(len(te))])
    return acc, jsd


def main():
    rows = load_examples()
    X = build_features(rows)
    n = len(rows)
    ent = np.array([r["entropy"] for r in rows])
    q = np.digitize(ent, np.quantile(ent, [0.25, 0.5, 0.75]))   # 0..3, 3=highest disagreement
    print(f"ChaosNLI: {n} examples (SNLI+MNLI), device={DEVICE}, feat dim={X.shape[1]}")
    print(f"5-fold x 5 seeds; conditions: hard / smooth(eps={EPS_SMOOTH}) / soft\n")

    conds = ["hard", "smooth", "soft"]
    acc = {c: [] for c in conds}
    jsd_per = {c: np.zeros(n) for c in conds}     # one held-out JSD per example (last seed avg)
    jsd_seed = {c: [] for c in conds}

    for seed in range(N_SEEDS):
        rng = np.random.default_rng(seed)
        order = rng.permutation(n)
        folds = np.array_split(order, N_FOLDS)
        per = {c: np.full(n, np.nan) for c in conds}
        for f in range(N_FOLDS):
            te = folds[f]
            tr = np.concatenate([folds[g] for g in range(N_FOLDS) if g != f])
            for c in conds:
                a, j = train_eval(X, rows, tr, te, c, seed)
                acc[c].append(a)
                per[c][te] = j
        for c in conds:
            jsd_seed[c].append(np.nanmean(per[c]))
            jsd_per[c] += per[c] / N_SEEDS

    print(f"{'cond':8s} {'maj-acc':>9s} {'JSD(mean)':>11s}")
    for c in conds:
        print(f"{c:8s} {np.mean(acc[c])*100:8.2f}% {np.mean(jsd_seed[c]):11.4f}")

    # Pre-registered tests
    print("\n-- H1: SOFT lower JSD than HARD and SMOOTH (paired Wilcoxon, per-example) --")
    for c in ("hard", "smooth"):
        stat, p = wilcoxon(jsd_per["soft"], jsd_per[c])
        delta = np.mean(jsd_per["soft"]) - np.mean(jsd_per[c])
        print(f"  soft vs {c:7s}: dJSD={delta:+.4f}  p={p:.2e}  "
              f"{'SOFT better' if delta<0 and p<0.05 else 'NOT sig / worse'}")

    print("\n-- H2: accuracy tax --")
    tax = (np.mean(acc['hard']) - np.mean(acc['soft'])) * 100
    print(f"  hard-acc - soft-acc = {tax:+.2f} pt  ({'OK (<=1pt)' if tax <= 1.0 else 'MATERIAL TAX'})")

    print("\n-- Where the effect lives: dJSD(soft - smooth) by entropy quartile --")
    for qq in range(4):
        mask = q == qq
        d = np.mean(jsd_per["soft"][mask]) - np.mean(jsd_per["smooth"][mask])
        tag = ["Q1 low-disagree", "Q2", "Q3", "Q4 high-disagree"][qq]
        print(f"  {tag:18s} n={mask.sum():4d}  dJSD={d:+.4f}")

    h1 = all(np.mean(jsd_per["soft"]) < np.mean(jsd_per[c]) and
             wilcoxon(jsd_per["soft"], jsd_per[c])[1] < 0.05 for c in ("hard", "smooth"))
    h2 = tax <= 1.0
    print(f"\nVERDICT: H1={'PASS' if h1 else 'FAIL'}  H2={'PASS' if h2 else 'FAIL'}  "
          f"-> {'PRESERVING DISAGREEMENT ADDS PREDICTIVE VALUE' if h1 and h2 else 'NULL: value is provenance, not predictive signal'}")


if __name__ == "__main__":
    sys.exit(main())
