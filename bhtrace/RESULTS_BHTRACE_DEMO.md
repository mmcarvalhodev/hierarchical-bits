# bhtrace — distributed trace as .bht (measured demo)

- spans: **269** · services: **10**
- `.bht` file: **391,267 bytes** · flat JSON: **387,520 bytes**

The flat baseline reads the **whole** trace for any query. The `.bht` keeps the span tree as the index and reads heavy attributes only on demand.

| reading | what it returns | bytes read | % of file | vs flat |
|---|---|---|---|---|
| `summary()` | per-service + critical path + slowest (10) | 41,371 B | 10.6% | **9× less** |
| `critical_path()` | root→leaf latency chain (6) | 41,371 B | 10.6% | **9× less** |
| `subtree('s0130')` | a span + its descendants (3) | 44,899 B | 11.5% | **9× less** |
| `service('db')` | all db spans (31) | 83,335 B | 21.3% | **5× less** |
| `full()` | everything (baseline) (269) | 391,267 B | 100.0% | **1× less** |

## What this demonstrates

- **The same envelope as `bhmem`, a different domain.** A trace is a tree; 'which spans are slow' and 'the critical path' are answered from the structure index alone — without loading a single attribute or stack trace.
- **Drill-in is a branch read.** `subtree(span)` and `service(name)` read only the blocks they touch, proportional to the question.
- **Honest boundary.** Full-text search across attributes still delegates to an inverted index; bhtrace makes the structure explicit and routes to the specialist, it does not replace it.
