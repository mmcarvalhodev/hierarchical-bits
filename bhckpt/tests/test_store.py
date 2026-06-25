"""bhckpt tests — correctness as a gate before any claim of gain."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from bhckpt import CheckpointReader, CheckpointStore, Tensor  # noqa: E402


def _store() -> CheckpointStore:
    s = CheckpointStore({"dim": 4, "n_layers": 1, "moe_layers": [0], "n_experts": 2})
    s.add(Tensor("model.embed_tokens.weight", [4, 4], "fp16", b"E" * 32))
    s.add(Tensor("model.layers.0.self_attn.q_proj.weight", [4, 4], "fp16", b"Q" * 32))
    s.add(Tensor("model.layers.0.mlp.gate.weight", [2, 4], "fp16", b"G" * 16))
    s.add(Tensor("model.layers.0.mlp.experts.0.up_proj.weight", [4, 4], "fp16", b"0" * 32))
    s.add(Tensor("model.layers.0.mlp.experts.1.up_proj.weight", [4, 4], "fp16", b"1" * 32))
    return s


@pytest.fixture()
def ck(tmp_path) -> CheckpointReader:
    p = tmp_path / "m.bckpt"
    _store().save(p)
    return CheckpointReader(p)


def test_roundtrip_preserves_all_tensors(ck: CheckpointReader) -> None:
    tensors, stats = ck.full()
    assert len(tensors) == 5
    assert stats.bytes_read == ck.file_size


def test_summary_is_index_only(ck: CheckpointReader) -> None:
    view, stats = ck.summary()
    assert stats.blocks_read == 0
    assert view["n_tensors"] == 5
    assert view["arch"]["n_experts"] == 2
    assert {t["name"] for t in view["tensors"]} >= {"model.embed_tokens.weight"}
    _, full_stats = ck.full()
    assert stats.bytes_read < full_stats.bytes_read


def test_tensor_returns_exact_bytes(ck: CheckpointReader) -> None:
    t, stats = ck.tensor("model.embed_tokens.weight")
    assert t is not None
    assert t["data"] == b"E" * 32
    assert stats.blocks_read == 1


def test_tensor_unknown(ck: CheckpointReader) -> None:
    t, stats = ck.tensor("nope")
    assert t is None
    assert stats.blocks_read == 0


def test_layer_returns_branch(ck: CheckpointReader) -> None:
    tensors, stats = ck.layer(0)
    names = {t["name"] for t in tensors}
    assert "model.layers.0.self_attn.q_proj.weight" in names
    assert "model.embed_tokens.weight" not in names  # embed is not in a layer
    assert stats.blocks_read == len(tensors)


def test_expert_loads_only_one_expert(ck: CheckpointReader) -> None:
    e0, stats = ck.expert(0, 0)
    assert {t["name"] for t in e0} == {"model.layers.0.mlp.experts.0.up_proj.weight"}
    assert e0[0]["data"] == b"0" * 32
    assert stats.blocks_read == 1
    # the other expert is NOT read
    e1, _ = ck.expert(0, 1)
    assert e1[0]["data"] == b"1" * 32


def test_expert_cheaper_than_layer(ck: CheckpointReader) -> None:
    _, e = ck.expert(0, 0)
    _, ly = ck.layer(0)
    assert e.bytes_read < ly.bytes_read


def test_invalid_file_rejected(tmp_path) -> None:
    bad = tmp_path / "bad.bckpt"
    bad.write_bytes(b"NOPE" + b"\x00" * 20)
    with pytest.raises(ValueError):
        CheckpointReader(bad)
