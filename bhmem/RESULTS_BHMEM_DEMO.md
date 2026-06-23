# bhmem — agent memory as .bh (measured demo)

- memories: **2250** · topics: **60**
- `.bh` file: **654,534 bytes** · flat JSONL: **585,790 bytes**

## Each reading reads only what it needs (REAL bytes read from the file)

The flat baseline reads the **whole** file for any query (585,790 B). The `.bh` reads only the requested branch.

| reading | what it returns | bytes read | % of file | vs flat |
|---|---|---|---|---|
| `summary()` | digest of all topics (60) | 16,504 B | 2.5% | **35× less** |
| `recall('review_07')` | the topic's memories (39) | 26,679 B | 4.1% | **22× less** |
| `since(last 5d)` | recent memories (40) | 63,759 B | 9.7% | **9× less** |
| `provenance('m00000')` | source+path of 1 memory (1) | 70,810 B | 10.8% | **8× less** |
| `full()` | everything (baseline) (2250) | 654,534 B | 100.0% | **1× less** |

## What this demonstrates

- **Not another compression number.** It's the CAPABILITY: the agent reads the summary, a topic, a window or the provenance **without loading the whole memory**. The cost of each reading is proportional to what it asks for.
- **Structure is part of the format.** Belonging (topic), time and provenance are navigable in the file itself — not across four systems bolted on top.
- **Honest boundary.** *Dense semantic* recall (vector) is not done here — it delegates to an HNSW index that the envelope references. The `.bh` calls the specialist; it does not compete with it.
