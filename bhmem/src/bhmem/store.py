"""bhmem — agent memory as a navigable .bh envelope.

The BH thesis applied to an agent's memory: instead of scattering memory across
documents + embeddings + summaries + cache + indexes (separate systems that
must be kept in sync), you write ONE hierarchical envelope where the STRUCTURE
is part of the format.

The value is not "being smaller". It's **reading only the part you need**:

    summary()        reads only the index (per-topic summaries)   — cheap
    recall(topic)    jumps to ONE branch and reads only it        — cheap
    since(t)         reads only the branches touching the window  — cheap
    provenance(id)   reads only the block holding the memory      — cheap
    full()           reads everything                              — the baseline

Every reading reports the bytes it ACTUALLY read from the file (real seeks), so
the gain is measured, not claimed. The honest baseline is the flat store
(JSON/JSONL) that loads the whole file for any query.

Honest scope (the BH boundary, same as the rest of the study):
  - .bh wins on STRUCTURAL access: by topic (belonging), by time, by
    provenance. Selective reading over an explicit hierarchy.
  - DENSE semantic (vector) recall is NOT done here — it delegates to a vector
    index (HNSW) that the envelope can reference. BH calls the specialist; it
    does not compete with it. See README.
"""
from __future__ import annotations

import json
import os
import struct
from dataclasses import asdict, dataclass, field

MAGIC = b"BHM1"
_U32 = struct.Struct("<I")


@dataclass
class Memory:
    """One structured agent memory."""

    id: str
    ts: float  # unix time (seconds)
    kind: str  # fact | event | relation | observation
    topic: str  # belonging — the branch of the hierarchy
    text: str
    source: str = ""  # provenance (where it came from: tool, url, turn...)
    meta: dict = field(default_factory=dict)


def _topic_summary(topic: str, mems: list[Memory]) -> dict:
    """Summary of a topic — what `summary()` reads without touching the blocks."""
    ordered = sorted(mems, key=lambda m: m.ts)
    kinds: dict[str, int] = {}
    for m in mems:
        kinds[m.kind] = kinds.get(m.kind, 0) + 1
    latest = ordered[-1]
    return {
        "topic": topic,
        "n": len(mems),
        "kinds": kinds,
        "tmin": ordered[0].ts,
        "tmax": latest.ts,
        "latest": latest.text[:80],
    }


class MemoryStore:
    """Accumulates memories and serializes them as a .bh envelope.

    File layout (position encodes the hierarchy — there is no HIERARCHY field):

        MAGIC(4)
        header_len(4)  + header_json    {n_topics, n_mem}
        table_len(4)   + table_json     [{topic, n, kinds, tmin, tmax,
                                          latest, offset, size}, ...]
        idindex_len(4) + idindex_json   {id -> topic}   (only `provenance` reads it)
        topic_block_0                   json([memory, ...])
        topic_block_1
        ...

    The header + table are the STRUCTURE INDEX: small, always read by
    summary/recall/since. The id_index is a SEPARATE region — only `provenance`
    loads it, so the summary does not pay for the id map. The blocks live at the
    end and are read by seek, only when a query asks for them.
    """

    def __init__(self) -> None:
        self._mem: list[Memory] = []

    def add(self, m: Memory) -> None:
        self._mem.append(m)

    def __len__(self) -> int:
        return len(self._mem)

    def _grouped(self) -> dict[str, list[Memory]]:
        groups: dict[str, list[Memory]] = {}
        for m in self._mem:
            groups.setdefault(m.topic, []).append(m)
        return groups

    def save(self, path: str | os.PathLike) -> str:
        groups = self._grouped()
        blocks: dict[str, bytes] = {
            topic: json.dumps([asdict(m) for m in mems], ensure_ascii=False).encode("utf-8")
            for topic, mems in groups.items()
        }
        # offsets relative to the start of the blocks region
        table = []
        offset = 0
        for topic, mems in groups.items():
            entry = _topic_summary(topic, mems)
            entry["offset"] = offset
            entry["size"] = len(blocks[topic])
            table.append(entry)
            offset += entry["size"]

        header = json.dumps(
            {"n_topics": len(groups), "n_mem": len(self._mem)},
            ensure_ascii=False,
        ).encode("utf-8")
        table_bytes = json.dumps(table, ensure_ascii=False).encode("utf-8")
        id_index = {m.id: m.topic for m in self._mem}
        idindex_bytes = json.dumps(id_index, ensure_ascii=False).encode("utf-8")

        with open(path, "wb") as f:
            f.write(MAGIC)
            f.write(_U32.pack(len(header)))
            f.write(header)
            f.write(_U32.pack(len(table_bytes)))
            f.write(table_bytes)
            f.write(_U32.pack(len(idindex_bytes)))
            f.write(idindex_bytes)
            for topic in groups:
                f.write(blocks[topic])
        return str(path)


@dataclass
class ReadStats:
    """How much a reading actually cost — measured, not claimed."""

    bytes_read: int
    blocks_read: int
    file_size: int

    @property
    def fraction(self) -> float:
        return self.bytes_read / self.file_size if self.file_size else 0.0


class MemoryReader:
    """Opens a .bh and serves the multiple readings with real seeks.

    On open it reads only the index (MAGIC + header + table). Blocks are read on
    demand — that is what makes `recall`/`since`/`provenance` cheap.
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = str(path)
        self.file_size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            if f.read(4) != MAGIC:
                raise ValueError("not a .bh file (bhmem)")
            (hlen,) = _U32.unpack(f.read(4))
            self.header = json.loads(f.read(hlen))
            (tlen,) = _U32.unpack(f.read(4))
            self.table = json.loads(f.read(tlen))
            # id_index region: located, but NOT read (lazy)
            (self._idindex_len,) = _U32.unpack(f.read(4))
            self._idindex_start = f.tell()
            self._blocks_start = self._idindex_start + self._idindex_len
        # bytes paid by summary/recall/since (structure index only)
        self._index_bytes = 4 + 4 + hlen + 4 + tlen + 4
        self._by_topic = {e["topic"]: e for e in self.table}
        self._id_index: dict[str, str] | None = None  # loaded on demand

    # ---- reading 1: the summary (index only) -----------------------------
    def summary(self) -> tuple[list[dict], ReadStats]:
        view = [
            {k: e[k] for k in ("topic", "n", "kinds", "tmin", "tmax", "latest")}
            for e in self.table
        ]
        return view, ReadStats(self._index_bytes, 0, self.file_size)

    # ---- reading 2: one branch (one topic) -------------------------------
    def recall(self, topic: str) -> tuple[list[dict], ReadStats]:
        entry = self._by_topic.get(topic)
        if entry is None:
            return [], ReadStats(self._index_bytes, 0, self.file_size)
        block = self._read_block(entry)
        return json.loads(block), ReadStats(
            self._index_bytes + entry["size"], 1, self.file_size
        )

    # ---- reading 3: a time window ----------------------------------------
    def since(self, t: float) -> tuple[list[dict], ReadStats]:
        out: list[dict] = []
        read = self._index_bytes
        nblocks = 0
        with open(self.path, "rb") as f:
            for entry in self.table:
                if entry["tmax"] < t:
                    continue  # whole branch outside the window — don't even read it
                f.seek(self._blocks_start + entry["offset"])
                block = f.read(entry["size"])
                read += entry["size"]
                nblocks += 1
                out.extend(m for m in json.loads(block) if m["ts"] >= t)
        out.sort(key=lambda m: m["ts"])
        return out, ReadStats(read, nblocks, self.file_size)

    # ---- reading 4: provenance of one memory -----------------------------
    def provenance(self, mem_id: str) -> tuple[dict | None, ReadStats]:
        # cost: structure index + the id_index (loaded now) + 1 block
        self._load_id_index()
        cost = self._index_bytes + self._idindex_len
        topic = self._id_index.get(mem_id)  # type: ignore[union-attr]
        if topic is None:
            return None, ReadStats(cost, 0, self.file_size)
        entry = self._by_topic[topic]
        block = self._read_block(entry)
        mem = next((m for m in json.loads(block) if m["id"] == mem_id), None)
        result = None
        if mem is not None:
            result = {
                "id": mem["id"],
                "topic": topic,
                "source": mem.get("source", ""),
                "ts": mem["ts"],
                "kind": mem["kind"],
            }
        return result, ReadStats(cost + entry["size"], 1, self.file_size)

    def _load_id_index(self) -> None:
        if self._id_index is not None:
            return
        with open(self.path, "rb") as f:
            f.seek(self._idindex_start)
            self._id_index = json.loads(f.read(self._idindex_len))

    # ---- baseline: read everything ---------------------------------------
    def full(self) -> tuple[list[dict], ReadStats]:
        out: list[dict] = []
        nblocks = 0
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start)
            for entry in self.table:
                block = f.read(entry["size"])
                nblocks += 1
                out.extend(json.loads(block))
        return out, ReadStats(self.file_size, nblocks, self.file_size)

    def _read_block(self, entry: dict) -> bytes:
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start + entry["offset"])
            return f.read(entry["size"])
