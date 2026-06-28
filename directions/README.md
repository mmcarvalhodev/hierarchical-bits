# Testing the "untested directions" (z.ai's §11)

z.ai proposed three future directions for BH and gave each a falsifiable test. We
ran them, with the project's discipline (declare → correctness/baseline → measure
→ vs-naive/vs-SOTA). **The tests did not confirm the claims as stated — they
qualified or refuted them.** That is the method working.

| direction | claim (z.ai) | measured result | verdict |
|---|---|---|---|
| **11.2 Edge transmission** | BH-stream sends far fewer bytes at high recall | 13× fewer than full transmission (recall 1.0) — **but 1.88× MORE bytes than a trivial fixed-threshold filter** (25× vs full). The summary round-trip costs bytes every window. | **partly refuted** — wins vs naive, **loses to the obvious SOTA filter** |
| **11.3 BIM targeted read** | a thermal analysis reads only thermal+geometry → big savings | the flagship example saves only **1.1×** (geometry dominates *and* is needed); real savings appear only for queries that **skip** geometry (cost-only 11.6×) | **qualified** — true only for geometry-skipping queries; ANCHOR (IFC partial-load already does it); and it tests selective-read, not the FCIR angle |
| **11.1 Structural RAG** | structural read reduces hallucination at matched retrieval cost | byte/locate economics confirmed (skeleton = **2.2%** of doc; scoped read **4.6%**) — but the **hallucination claim needs an LLM eval and was NOT tested** | **economics confirmed (ANCHOR); the actual claim remains open/untested** |

## What this says

1. **z.ai's directions are all the substrate-sharing / selective-read mechanism** —
   the part the 20-domain sweep already concluded is mature SOTA (ANCHOR). Testing
   them confirms the mechanism is real but **re-derives the known result**, and in
   one case (11.2) BH is actually *worse* than the trivial baseline once the
   summary round-trip is counted.
2. **The flagship framings were optimistic.** 11.2 "far fewer bytes" omitted the
   round-trip cost; 11.3 picked the example (thermal) that barely saves because
   geometry dominates and is needed.
3. **None of the three engages FCIR** (the rival-interpretation property the
   investigation actually identified as the differentiator). The genuinely
   interesting BIM angle — rival discipline overlays (the sweep's one BUILD) — is
   not what z.ai's test measures.

**Conclusion:** these belong, at most, as honestly-labeled engineering notes
(ANCHOR selective-read), not as BH's exciting frontier — and they should not go
into the master/Zenodo as "directions" without these caveats. Run each test:

```
X:/miniconda3/python.exe directions/edge_test.py   # -> RESULTS_11_2_EDGE.md
X:/miniconda3/python.exe directions/bim_test.py    # -> RESULTS_11_3_BIM.md
X:/miniconda3/python.exe directions/rag_test.py    # -> RESULTS_11_1_RAG.md
```
