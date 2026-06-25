"""bhtrace tests — correctness as a gate before any claim of gain."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bhtrace import Span, TraceReader, TraceStore  # noqa: E402


def _store() -> TraceStore:
    # root -> (a:db, b:cache); a -> (a1:db, a2:db)
    s = TraceStore("t1")
    s.add(Span("root", None, "gateway", "GET /x", 0, 1000, "ok", {"k": "root"}))
    s.add(Span("a", "root", "db", "query", 10, 600, "ok", {"k": "a"}))
    s.add(Span("b", "root", "cache", "get", 20, 200, "ok", {"k": "b"}))
    s.add(Span("a1", "a", "db", "query", 15, 300, "error", {"k": "a1"}))
    s.add(Span("a2", "a", "db", "query", 20, 100, "ok", {"k": "a2"}))
    return s


@pytest.fixture()
def tr(tmp_path) -> TraceReader:
    p = tmp_path / "t.bht"
    _store().save(p)
    return TraceReader(p)


def test_roundtrip_preserves_all_spans(tr: TraceReader) -> None:
    spans, stats = tr.full()
    assert len(spans) == 5
    assert {s["id"] for s in spans} == {"root", "a", "b", "a1", "a2"}
    assert stats.bytes_read == tr.file_size


def test_summary_is_index_only(tr: TraceReader) -> None:
    view, stats = tr.summary()
    assert stats.blocks_read == 0
    assert view["n_spans"] == 5
    assert set(view["services"]) == {"gateway", "db", "cache"}
    assert view["services"]["db"]["spans"] == 3
    assert view["services"]["db"]["errors"] == 1
    _, full_stats = tr.full()
    assert stats.bytes_read < full_stats.bytes_read


def test_critical_path_follows_longest_child(tr: TraceReader) -> None:
    path, stats = tr.critical_path()
    # root -> a (600 > b 200) -> a1 (300 > a2 100)
    assert [p["id"] for p in path] == ["root", "a", "a1"]
    assert stats.blocks_read == 0


def test_subtree_returns_span_and_descendants(tr: TraceReader) -> None:
    spans, stats = tr.subtree("a")
    assert {s["id"] for s in spans} == {"a", "a1", "a2"}
    assert stats.blocks_read == 3
    assert stats.bytes_read < tr.file_size


def test_subtree_leaf(tr: TraceReader) -> None:
    spans, stats = tr.subtree("b")
    assert {s["id"] for s in spans} == {"b"}
    assert stats.blocks_read == 1


def test_service_filter(tr: TraceReader) -> None:
    spans, stats = tr.service("db")
    assert {s["id"] for s in spans} == {"a", "a1", "a2"}
    assert all(s["service"] == "db" for s in spans)


def test_subtree_unknown(tr: TraceReader) -> None:
    spans, stats = tr.subtree("zzz")
    assert spans == []
    assert stats.blocks_read == 0


def test_selective_cheaper_than_full(tr: TraceReader) -> None:
    _, sub = tr.subtree("b")
    _, full = tr.full()
    assert sub.bytes_read < full.bytes_read
    assert sub.fraction < 1.0


def test_invalid_file_rejected(tmp_path) -> None:
    bad = tmp_path / "bad.bht"
    bad.write_bytes(b"NOPE" + b"\x00" * 20)
    with pytest.raises(ValueError):
        TraceReader(bad)
