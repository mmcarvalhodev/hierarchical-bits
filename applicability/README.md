# applicability/ — where does BH actually apply?

A research-grounded sweep of **20 data domains**, each scored against the
Hierarchical Bits law and ranked. The honest answer to *"what is BH good for?"*

- **[`APPLICABILITY_SCORECARD.md`](APPLICABILITY_SCORECARD.md)** — the ranked
  table + the findings + the recommendation.
- **`applicability_map.png`** — the visual map (composite score × verdict).
- **[`SURVEY_SOURCES.md`](SURVEY_SOURCES.md)** — the citations behind the scores.
- **[`scorecard.py`](scorecard.py)** — recomputes the composite from the raw
  scores (transparent weights) and regenerates the chart + report.

## The one-paragraph result

The BH *shape* (a heavy shared substrate + many co-registered layers + selective
read) is **everywhere** — but in almost every big-data domain the
store-once + selective-read pattern is **already mature SOTA** (DICOM, COG/STAC,
lakeFS, CRAM/tabix, MAM, S-LoRA…), so BH lands as `ANCHOR` (credibility, not
novelty). The sweep *suggests* the still-under-explored contribution is
**narrower and sharper** than "a universal format": treating **rival /
conflicting interpretations as first-class entities** (what existing tools treat
as noise to adjudicate) — exactly what `bhanno` models. Among the 20 domains
surveyed, the only one classified `BUILD` was **CAD/BIM**, where federation
duplicates and no tool unifies substrate-once + rival overlays + selective branch
reads. See **[`BH_PRINCIPLE.md`](../BH_PRINCIPLE.md)** for the formalization the
sweep points to.

```
Run:  python scorecard.py   ->  APPLICABILITY_SCORECARD.md + applicability_map.png
```
