# 11.1 Structural RAG — byte/locate economics (measured) + the untested claim

- doc: 40 sections × 12 chunks × 1200 B = 588,934 B · per-section summary 90 B

| read | bytes | % of doc | vs flat |
|---|---|---|---|
| structural locate (index/summaries only) | 12,934 | 2.2% | 46× less |
| locate + scoped read (1 section) | 27,334 | 4.6% | 22× less |
| flat RAG (read all chunks) | 588,934 | 100.0% | 1× |

## Verdict (honest)

- **The byte economics check out:** reading the skeleton to locate the right section costs ~2% of the document, and a scoped read of one section ~5% — both far below a flat read. The mechanism works.
- **But that mechanism is ANCHOR.** A table of contents / section index + scoped retrieval already exists (hierarchical / parent-document retrievers, section-aware chunking). The byte saving is *vs naive flat-load*, not a novelty.
- **The actual claim is NOT tested here.** Whether a structural-read phase *reduces hallucination* on multi-section documents needs an LLM, a labeled QA set, and an eval harness comparing hallucination rate at matched retrieval cost. This script does not do that. **Status: open hypothesis — measurable economics confirmed, the interesting claim untested.**
