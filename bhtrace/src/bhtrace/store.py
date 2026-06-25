"""bhtrace — a distributed trace as a navigable .bh envelope.

The BH thesis applied to observability. A distributed trace IS a tree:
trace -> spans -> events, with belonging (service) and time. Today a trace is
stored in an index (Elastic/Loki/Tempo) bolted on top; to ask "which spans are
slow" you scan, and the heavy part (span attributes, logs, stack traces) is
paid for even when you only want the skeleton.

bhtrace writes ONE envelope where the STRUCTURE (the span tree + timings) is the
index — small, always read — and the heavy per-span payload (attributes,
events) lives in blocks read only on demand:

    summary()         tree rollup: per-service, critical path, slowest  — index only
    critical_path()   the root->leaf chain that dominates the latency    — index only
    subtree(span)     a span and all its descendants (one branch)        — its blocks
    service(name)     every span of one service                          — those blocks
    full()            everything                                          — the baseline

Every reading reports the bytes it ACTUALLY read (real seeks), so the gain is
measured, not claimed. The honest baseline is a flat store (the whole trace
JSON) loaded entirely for any query.

Honest boundary (same as the study): bhtrace wins on STRUCTURAL access over an
attribute-heavy tree. The dense residual (the attribute/log payloads) is
delegated to whatever stores text best; bhtrace makes the structure explicit
and routes to it. Full-text search across attributes still delegates to an
inverted index — bhtrace calls the specialist, it does not replace it.
"""
from __future__ import annotations

import json
import os
import struct
from dataclasses import asdict, dataclass, field

MAGIC = b"BHT1"
_U32 = struct.Struct("<I")


@dataclass
class Span:
    """One span of a trace. The heavy part is attributes/events."""

    span_id: str
    parent_id: str | None
    service: str
    operation: str
    start_us: int          # microseconds, relative to trace start
    dur_us: int            # duration in microseconds
    status: str = "ok"     # ok | error
    attributes: dict = field(default_factory=dict)   # the heavy payload
    events: list = field(default_factory=list)        # logs/events (heavy)


class TraceStore:
    """Accumulates spans and serializes the trace as a .bht envelope.

    Layout (position encodes the tree — there is no separate HIERARCHY field):

        MAGIC(4)
        header_len(4) + header_json   {trace_id, n_spans, root_id, total_us}
        tree_len(4)   + tree_json     [{id, parent, service, op, start_us,
                                        dur_us, status, off, size}, ...]
        payload_block_0               json({attributes, events})   per span
        payload_block_1
        ...

    The header + tree are the STRUCTURE INDEX: small, always read by
    summary/critical_path. The payload blocks (the heavy attributes/events)
    live at the end and are read by seek, only when a query drills in.
    """

    def __init__(self, trace_id: str = "trace") -> None:
        self.trace_id = trace_id
        self._spans: list[Span] = []

    def add(self, s: Span) -> None:
        self._spans.append(s)

    def __len__(self) -> int:
        return len(self._spans)

    def save(self, path: str | os.PathLike) -> str:
        root = next((s for s in self._spans if s.parent_id is None), None)
        blocks: list[bytes] = []
        tree = []
        offset = 0
        for s in self._spans:
            payload = json.dumps(
                {"attributes": s.attributes, "events": s.events}, ensure_ascii=False
            ).encode("utf-8")
            blocks.append(payload)
            tree.append({
                "id": s.span_id, "parent": s.parent_id, "service": s.service,
                "op": s.operation, "start_us": s.start_us, "dur_us": s.dur_us,
                "status": s.status, "off": offset, "size": len(payload),
            })
            offset += len(payload)

        header = json.dumps({
            "trace_id": self.trace_id, "n_spans": len(self._spans),
            "root_id": root.span_id if root else None,
            "total_us": root.dur_us if root else 0,
        }, ensure_ascii=False).encode("utf-8")
        tree_bytes = json.dumps(tree, ensure_ascii=False).encode("utf-8")

        with open(path, "wb") as f:
            f.write(MAGIC)
            f.write(_U32.pack(len(header)))
            f.write(header)
            f.write(_U32.pack(len(tree_bytes)))
            f.write(tree_bytes)
            for b in blocks:
                f.write(b)
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


class TraceReader:
    """Opens a .bht and serves the readings with real seeks.

    On open it reads only the structure index (MAGIC + header + tree). Payload
    blocks are read on demand — that is what makes the skeleton readings cheap.
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = str(path)
        self.file_size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            if f.read(4) != MAGIC:
                raise ValueError("not a .bht file (bhtrace)")
            (hlen,) = _U32.unpack(f.read(4))
            self.header = json.loads(f.read(hlen))
            (tlen,) = _U32.unpack(f.read(4))
            self.tree = json.loads(f.read(tlen))
            self._blocks_start = f.tell()
        self._index_bytes = 4 + 4 + hlen + 4 + tlen
        self._by_id = {e["id"]: e for e in self.tree}
        self._children: dict[str, list[str]] = {}
        for e in self.tree:
            self._children.setdefault(e["parent"], []).append(e["id"])

    # ---- reading 1: the rollup (structure only) --------------------------
    def summary(self) -> tuple[dict, ReadStats]:
        services: dict[str, dict] = {}
        for e in self.tree:
            svc = services.setdefault(e["service"], {"spans": 0, "total_us": 0, "errors": 0})
            svc["spans"] += 1
            svc["total_us"] += e["dur_us"]
            if e["status"] == "error":
                svc["errors"] += 1
        # self-time = own duration minus direct children's duration
        slow = []
        for e in self.tree:
            child_us = sum(self._by_id[c]["dur_us"] for c in self._children.get(e["id"], []))
            slow.append((e["dur_us"] - child_us, e))
        slow.sort(key=lambda x: x[0], reverse=True)
        slowest = [{"op": e["op"], "service": e["service"], "self_us": s}
                   for s, e in slow[:5]]
        view = {
            "trace_id": self.header.get("trace_id"),
            "n_spans": self.header.get("n_spans"),
            "total_us": self.header.get("total_us"),
            "services": services,
            "critical_path": [c["op"] for c in self._critical_path()],
            "slowest_self_time": slowest,
        }
        return view, ReadStats(self._index_bytes, 0, self.file_size)

    # ---- reading 2: the critical path (structure only) -------------------
    def critical_path(self) -> tuple[list[dict], ReadStats]:
        path = [{"id": e["id"], "service": e["service"], "op": e["op"],
                 "dur_us": e["dur_us"]} for e in self._critical_path()]
        return path, ReadStats(self._index_bytes, 0, self.file_size)

    def _critical_path(self) -> list[dict]:
        """Root->leaf chain following the longest-duration child at each step."""
        root_id = self.header.get("root_id")
        if root_id is None:
            return []
        path, cur = [], root_id
        while cur is not None:
            e = self._by_id[cur]
            path.append(e)
            kids = self._children.get(cur, [])
            cur = max(kids, key=lambda c: self._by_id[c]["dur_us"]) if kids else None
        return path

    # ---- reading 3: a subtree (one branch) -------------------------------
    def subtree(self, span_id: str) -> tuple[list[dict], ReadStats]:
        if span_id not in self._by_id:
            return [], ReadStats(self._index_bytes, 0, self.file_size)
        ids: list[str] = []
        stack = [span_id]
        while stack:
            cur = stack.pop()
            ids.append(cur)
            stack.extend(self._children.get(cur, []))
        return self._read_spans(ids)

    # ---- reading 4: one service ------------------------------------------
    def service(self, name: str) -> tuple[list[dict], ReadStats]:
        ids = [e["id"] for e in self.tree if e["service"] == name]
        return self._read_spans(ids)

    # ---- baseline: everything --------------------------------------------
    def full(self) -> tuple[list[dict], ReadStats]:
        out = []
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start)
            for e in self.tree:
                payload = json.loads(f.read(e["size"]))
                out.append({**_meta(e), **payload})
        return out, ReadStats(self.file_size, len(self.tree), self.file_size)

    def _read_spans(self, ids: list[str]) -> tuple[list[dict], ReadStats]:
        out = []
        read = self._index_bytes
        with open(self.path, "rb") as f:
            for sid in ids:
                e = self._by_id[sid]
                f.seek(self._blocks_start + e["off"])
                payload = json.loads(f.read(e["size"]))
                read += e["size"]
                out.append({**_meta(e), **payload})
        return out, ReadStats(read, len(ids), self.file_size)


def _meta(e: dict) -> dict:
    return {"id": e["id"], "parent": e["parent"], "service": e["service"],
            "op": e["op"], "start_us": e["start_us"], "dur_us": e["dur_us"],
            "status": e["status"]}
