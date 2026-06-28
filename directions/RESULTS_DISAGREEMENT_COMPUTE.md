# Meta-critique test: is 'compute over disagreement' a new/impossible class?

- 200 items × 5 annotators · uncollapsed table = 1000 rows

Three stores, the critique's four queries:

| query | gold-collapsed (ANCHOR strawman) | uncollapsed table (honest baseline) | FCIR (bhanno) |
|---|---|---|---|
| low-agreement & majority=cat | ❌ impossible (labels discarded) | ✅ 0 items | ✅ same (=table) |
| most-disagreeing annotator | ❌ impossible | ✅ **carol** (41 disagreements) | ✅ same |
| re-adjudicate weighted (no re-read) | ❌ impossible | ✅ 1 items change | ✅ same |
| mean annotation entropy / item | ❌ impossible | ✅ 0.507 bits | ✅ same |

## Verdict (honest)

- **The critique is right about gold-collapse:** a store that adjudicated on write and kept only the gold label can answer **0/4** — the disagreement is gone.
- **But that is a strawman baseline.** The honest baseline for disagreement computation is the **uncollapsed `(item, annotator, label)` table** — exactly what CrowdTruth, human-label-variation datasets, and any annotation DB already keep. It answers **4/4**, with plain `GROUP BY`. These are **not a new or impossible class of computation** — they are standard queries over data that was simply not collapsed.
- **FCIR ties the uncollapsed table on capability** (4/4). Its only delta is **co-registration to the substrate stored once** — but a per-annotator table also references the substrate by id and does not duplicate it. So FCIR's genuine contribution stays what the project already concluded: a **name + a model** for 'don't collapse on write, co-register the layers' — not a new capability, and not impossible-elsewhere.
- **Net:** the meta-critique sharpened a real bias (we measured properties 1-2, not 3-4) — but its flagship claim ('new class, impossible in ANCHOR') overstates, in the same way the earlier AI critiques did. Tested against the right baseline, it loops back to the existing honest conclusion: FCIR is synthesis + naming.
