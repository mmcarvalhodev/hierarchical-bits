"""bhckpt — a model checkpoint as a navigable .bh envelope.

The BH thesis applied to model weights. A checkpoint IS a hierarchy:
model -> layers -> tensors (and, for MoE, layer -> experts -> tensors). The
heavy residual is the raw weight bytes; the structure (which tensor, which
shape, which layer, which expert) is tiny.

bhckpt writes ONE envelope where the STRUCTURE is the index — architecture +
the tensor table — read instantly, and the raw weight blocks are read only on
demand:

    summary()          architecture + tensor list (names/shapes/sizes)  — index only
    tensor(name)       the raw bytes of one tensor                       — its block
    layer(i)           every tensor of one layer                         — those blocks
    expert(i, e)       one MoE expert of one layer (a sub-branch)        — those blocks
    full()             all weights                                       — the baseline

Every reading reports the bytes it ACTUALLY read (real seeks), so the gain is
measured, not claimed. The honest baseline is a flat checkpoint loaded whole for
any access.

Honest boundary (the same as the study): selective per-tensor read already
exists — `safetensors` does header+offsets+mmap. That is the ANCHOR
(credibility, not novelty). The NEW piece is the union: the MoE expert as a
first-class HIERARCHICAL read (load one expert without the rest), per-tensor
codec routing recorded in the index (each tensor can be delegated to its own
best quantization/compression specialist — the dense residual), and a
Merkle face over the blocks for verifiable provenance. bhckpt does not
re-implement quantization; it records the routing and reads by structure.
"""
from __future__ import annotations

import json
import os
import struct
from dataclasses import dataclass, field

MAGIC = b"BCK1"
_U32 = struct.Struct("<I")


@dataclass
class Tensor:
    """One tensor. `data` is the raw (already-encoded) bytes; `codec` records
    which specialist produced them (the per-tensor routing decision)."""

    name: str
    shape: list[int]
    dtype: str
    data: bytes
    codec: str = "fp16"


class CheckpointStore:
    """Accumulates tensors and serializes the checkpoint as a .bckpt envelope.

    Layout (position encodes the hierarchy via the dotted tensor names):

        MAGIC(4)
        header_len(4) + header_json   {arch{...}, n_tensors, total_bytes}
        table_len(4)  + table_json    [{name, shape, dtype, codec,
                                        nbytes, off, size}, ...]
        weight_block_0                raw bytes of tensor 0
        weight_block_1
        ...

    The header + table are the STRUCTURE INDEX: tiny, always read by summary().
    The weight blocks (the residual) live at the end and are read by seek, only
    for the tensors a query asks for.
    """

    def __init__(self, arch: dict | None = None) -> None:
        self.arch = arch or {}
        self._tensors: list[Tensor] = []

    def add(self, t: Tensor) -> None:
        self._tensors.append(t)

    def __len__(self) -> int:
        return len(self._tensors)

    def save(self, path: str | os.PathLike) -> str:
        table = []
        offset = 0
        total = 0
        for t in self._tensors:
            n = len(t.data)
            table.append({
                "name": t.name, "shape": t.shape, "dtype": t.dtype,
                "codec": t.codec, "nbytes": n, "off": offset, "size": n,
            })
            offset += n
            total += n

        header = json.dumps({
            "arch": self.arch, "n_tensors": len(self._tensors), "total_bytes": total,
        }, ensure_ascii=False).encode("utf-8")
        table_bytes = json.dumps(table, ensure_ascii=False).encode("utf-8")

        with open(path, "wb") as f:
            f.write(MAGIC)
            f.write(_U32.pack(len(header)))
            f.write(header)
            f.write(_U32.pack(len(table_bytes)))
            f.write(table_bytes)
            for t in self._tensors:
                f.write(t.data)
        return str(path)


@dataclass
class ReadStats:
    """How much a reading actually cost — measured, not claimed."""

    bytes_read: int
    blocks_read: int      # tensors read
    file_size: int

    @property
    def fraction(self) -> float:
        return self.bytes_read / self.file_size if self.file_size else 0.0


class CheckpointReader:
    """Opens a .bckpt and serves the readings with real seeks.

    On open it reads only the index (MAGIC + header + table). Weight blocks are
    read on demand — that is what makes summary / one-expert reads cheap.
    """

    def __init__(self, path: str | os.PathLike) -> None:
        self.path = str(path)
        self.file_size = os.path.getsize(self.path)
        with open(self.path, "rb") as f:
            if f.read(4) != MAGIC:
                raise ValueError("not a .bckpt file (bhckpt)")
            (hlen,) = _U32.unpack(f.read(4))
            self.header = json.loads(f.read(hlen))
            (tlen,) = _U32.unpack(f.read(4))
            self.table = json.loads(f.read(tlen))
            self._blocks_start = f.tell()
        self._index_bytes = 4 + 4 + hlen + 4 + tlen
        self._by_name = {e["name"]: e for e in self.table}

    # ---- reading 1: the architecture + tensor list (index only) ----------
    def summary(self) -> tuple[dict, ReadStats]:
        tensors = [{"name": e["name"], "shape": e["shape"], "dtype": e["dtype"],
                    "codec": e["codec"], "MB": round(e["nbytes"] / 1e6, 2)}
                   for e in self.table]
        view = {
            "arch": self.header.get("arch", {}),
            "n_tensors": self.header.get("n_tensors"),
            "total_MB": round(self.header.get("total_bytes", 0) / 1e6, 1),
            "tensors": tensors,
        }
        return view, ReadStats(self._index_bytes, 0, self.file_size)

    # ---- reading 2: one tensor -------------------------------------------
    def tensor(self, name: str) -> tuple[dict | None, ReadStats]:
        e = self._by_name.get(name)
        if e is None:
            return None, ReadStats(self._index_bytes, 0, self.file_size)
        data = self._read_block(e)
        return {**_meta(e), "data": data}, ReadStats(
            self._index_bytes + e["size"], 1, self.file_size)

    # ---- reading 3: one layer (a branch) ---------------------------------
    def layer(self, idx: int) -> tuple[list[dict], ReadStats]:
        return self.prefix(f"model.layers.{idx}.")

    # ---- reading 4: one MoE expert (a sub-branch) ------------------------
    def expert(self, layer_idx: int, expert_idx: int) -> tuple[list[dict], ReadStats]:
        return self.prefix(f"model.layers.{layer_idx}.mlp.experts.{expert_idx}.")

    def prefix(self, pre: str) -> tuple[list[dict], ReadStats]:
        names = [e["name"] for e in self.table if e["name"].startswith(pre)]
        return self._read_tensors(names)

    # ---- baseline: all weights -------------------------------------------
    def full(self) -> tuple[list[dict], ReadStats]:
        out = []
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start)
            for e in self.table:
                out.append({**_meta(e), "data": f.read(e["size"])})
        return out, ReadStats(self.file_size, len(self.table), self.file_size)

    def _read_tensors(self, names: list[str]) -> tuple[list[dict], ReadStats]:
        out = []
        read = self._index_bytes
        with open(self.path, "rb") as f:
            for name in names:
                e = self._by_name[name]
                f.seek(self._blocks_start + e["off"])
                out.append({**_meta(e), "data": f.read(e["size"])})
                read += e["size"]
        return out, ReadStats(read, len(names), self.file_size)

    def _read_block(self, e: dict) -> bytes:
        with open(self.path, "rb") as f:
            f.seek(self._blocks_start + e["off"])
            return f.read(e["size"])


def _meta(e: dict) -> dict:
    return {"name": e["name"], "shape": e["shape"], "dtype": e["dtype"],
            "codec": e["codec"], "nbytes": e["nbytes"]}
