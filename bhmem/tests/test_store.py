"""bhmem tests — correctness as a gate before any claim of gain."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bhmem import Memory, MemoryReader, MemoryStore  # noqa: E402

T0 = 1_700_000_000.0


def _store() -> MemoryStore:
    s = MemoryStore()
    n = 0
    for topic, reps in [("a", 5), ("b", 3), ("c", 7)]:
        for k in range(reps):
            s.add(Memory(id=f"m{n:03d}", ts=T0 + n * 100, kind="fact",
                         topic=topic, text=f"text {topic} {k}", source=f"src{n}"))
            n += 1
    return s


@pytest.fixture()
def bh(tmp_path) -> MemoryReader:
    p = tmp_path / "mem.bh"
    _store().save(p)
    return MemoryReader(p)


def test_roundtrip_preserves_all_memories(bh: MemoryReader) -> None:
    mems, stats = bh.full()
    assert len(mems) == 15
    assert {m["id"] for m in mems} == {f"m{n:03d}" for n in range(15)}
    assert stats.bytes_read == bh.file_size  # full reads the whole file


def test_recall_returns_only_the_topic(bh: MemoryReader) -> None:
    mems, stats = bh.recall("b")
    assert len(mems) == 3
    assert all(m["topic"] == "b" for m in mems)
    assert stats.blocks_read == 1  # read ONE block, not all


def test_recall_unknown_topic(bh: MemoryReader) -> None:
    mems, stats = bh.recall("zzz")
    assert mems == []
    assert stats.blocks_read == 0


def test_summary_does_not_read_blocks(bh: MemoryReader) -> None:
    view, stats = bh.summary()
    assert {e["topic"] for e in view} == {"a", "b", "c"}
    assert stats.blocks_read == 0
    # the summary is strictly cheaper than reading everything
    _, full_stats = bh.full()
    assert stats.bytes_read < full_stats.bytes_read


def test_since_filters_by_time(bh: MemoryReader) -> None:
    cutoff = T0 + 10 * 100  # memories m010..m014
    mems, stats = bh.since(cutoff)
    assert {m["id"] for m in mems} == {f"m{n:03d}" for n in range(10, 15)}
    assert all(m["ts"] >= cutoff for m in mems)
    # should have read only the block(s) touching the window, not all 3
    assert stats.blocks_read <= 2


def test_provenance_reads_only_one_block(bh: MemoryReader) -> None:
    prov, stats = bh.provenance("m007")
    assert prov is not None
    assert prov["id"] == "m007"
    assert prov["source"] == "src7"
    assert prov["topic"] == "b"  # a=m000..m004, b=m005..m007, c=m008..m014
    assert stats.blocks_read == 1


def test_provenance_unknown_id(bh: MemoryReader) -> None:
    prov, stats = bh.provenance("does_not_exist")
    assert prov is None
    assert stats.blocks_read == 0


def test_selective_reading_is_cheaper_than_full(bh: MemoryReader) -> None:
    _, recall_stats = bh.recall("b")
    _, full_stats = bh.full()
    assert recall_stats.bytes_read < full_stats.bytes_read
    assert recall_stats.fraction < 1.0


def test_invalid_file_rejected(tmp_path) -> None:
    bad = tmp_path / "bad.bh"
    bad.write_bytes(b"NOPE" + b"\x00" * 20)
    with pytest.raises(ValueError):
        MemoryReader(bad)
