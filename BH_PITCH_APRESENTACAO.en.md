# Hierarchical Bits — Presentation Pitch

> **In one sentence:** a structure that lets you represent a heterogeneous
> asset, navigate parts of it without loading everything, and delegate each
> region to the best specialist format.

---

## SLIDE 1 — The problem

Every data format today forces you to pick **one**:

- **Compact** (JPEG/WebP/AVIF) → but to see one piece, you decode all of it.
- **Navigable** (indexes, OLAP, vector DB) → but it's structure bolted on top,
  across several systems that must be kept in sync.

Data is born raw, and the rest of the stack spends time, space and complexity
**rediscovering its structure** — indexes, aggregates, previews, caches, proofs,
metadata. All scattered across separate systems.

---

## SLIDE 2 — The idea (not a codec, nor a database)

**Hierarchical Bits (BH)** is a **structural envelope**: data is born carrying
its own structure. Instead of compressing everything onto a single basis, BH:

```
1. makes structure EXPLICIT   — hierarchy, belonging, rules (cost: 0–6%)
2. ROUTES each region          — photo→WebP, gradient→formula, text→PNG
3. allows MULTIPLE readings    — preview / region / aggregate / proof
```

> It doesn't replace codecs. It **orchestrates** codecs per region, inside a
> structure that knows what each region means.

---

## SLIDE 3 — The core capability

The heart of BH is not "being smaller". It's **reading only the part you need,
without decoding the rest** — a capability no compact format has. Size is a
consequence, not the promise.

| | result |
|---|---|
| **Access one region** | **3–55× fewer bytes** than WebP (which decodes the WHOLE file for any piece) |
| ...and still smaller | 2.1× smaller than WebP, in the same file |
| Cost of making structure explicit | only 0–6% of the file |

> **Capability, not benchmark.** "I read only the branch I need" is a property
> of the format — it doesn't depend on which document, which dataset, which
> condition. That's what survives the skeptical engineer. Compact **and**
> navigable, in a single file — today that takes four tools.

---

## SLIDE 4 — Why it's different

BH converges to something that mixes, without being any of them:

```
PDF    → orchestration of specialists
Merkle → verifiable hierarchy
OLAP   → selective reading
AST    → explicit structure
```

Nobody sells **representation + reading + belonging + hierarchy + multiple
views** as a single structure. **That's the new piece.**

---

## SLIDE 5 — Where it wins (honest)

```
WINS       STRUCTURE-DOMINANT data: documents, diagrams, UIs, maps, layered
           data, structured AI outputs, symbolic knowledge.
           At the limit (rule-generated data): the payload becomes the PROGRAM
           that generates it — 800× to 3,600× smaller.
DELEGATES  dense signal (photo, audio, embedding) → WebP/AVIF/HNSW reign, and BH
           CALLS them. It doesn't compete where it shouldn't.
```

The boundary is not entropy — it's **structure recognition**.

---

## SLIDE 6 — Where someone would say "this is different"

```
AGENT MEMORY
   today: documents + embeddings + summaries + cache + indexes + metadata,
          all scattered.
   .bh:   a single navigable envelope.

KNOWLEDGE SYSTEMS (Notion/Obsidian/Roam/Logseq)
   today: they structure information, but the structure is NOT part of the format.
   .bh:   the structure IS the format.

COMPOSITE AI ASSETS
   image + mask + depth + prompt + version + metadata.
   today: a Frankenstein of systems. .bh: native.
```

---

## SLIDE 7 — The state and the ask

- **Validated by measurement**, not by slide: 9 angles tested, 128+ green
  tests, correctness as a gate, honest baselines, public self-corrections.
- **Construction has begun:** `bhmem` — a usable `.bh` for **agent memory**
  (library + tests). The agent reads the summary / a topic / a window / the
  provenance without loading the whole memory: **36× / 22× / 9× / 8× fewer
  bytes** than a flat store. The thesis became a tool.
- **Not a finished product yet** — it's a measured architecture with the first
  executable artifact. The next step is to wire `bhmem` into a real agent loop
  and add the verifiable-provenance face (Merkle over the blocks).

---

> **The value isn't in the compressed block. It's in the structure that knows
> what that block means.**
