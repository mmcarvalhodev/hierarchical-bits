"""bhckpt demo — a model checkpoint as a .bckpt envelope, measured.

Builds a small synthetic transformer with two MoE layers, writes it as .bckpt,
and shows each reading reads only the fraction it needs — against the honest
baseline (a flat checkpoint loaded whole for any access).

Run:  X:/miniconda3/python.exe X:/bitH/bhckpt/demo.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from bhckpt import CheckpointReader, CheckpointStore, Tensor  # noqa: E402

OUT = Path(__file__).resolve().parent
DIM, VOCAB, FF, N_LAYERS, N_EXPERTS = 256, 3000, 768, 4, 6
MOE_LAYERS = [2, 3]
RNG = np.random.default_rng(0)


def w(*shape: int) -> tuple[bytes, list[int]]:
    a = RNG.standard_normal(shape).astype(np.float16)
    return a.tobytes(), list(shape)


def build() -> CheckpointStore:
    """A small transformer: dense layers 0–1, MoE layers 2–3 (6 experts each).

    The weights dominate; the structure (which tensor, which expert) is tiny.
    That is exactly the shape where reading the architecture, one layer, or one
    expert — without the rest — pays off.
    """
    arch = {"dim": DIM, "vocab": VOCAB, "ff": FF, "n_layers": N_LAYERS,
            "moe_layers": MOE_LAYERS, "n_experts": N_EXPERTS, "dtype": "fp16"}
    s = CheckpointStore(arch)

    def add(name, *shape):
        data, sh = w(*shape)
        s.add(Tensor(name, sh, "fp16", data))

    add("model.embed_tokens.weight", VOCAB, DIM)
    for l in range(N_LAYERS):
        for proj in ("q", "k", "v", "o"):
            add(f"model.layers.{l}.self_attn.{proj}_proj.weight", DIM, DIM)
        add(f"model.layers.{l}.input_layernorm.weight", DIM)
        add(f"model.layers.{l}.post_attention_layernorm.weight", DIM)
        if l in MOE_LAYERS:
            add(f"model.layers.{l}.mlp.gate.weight", N_EXPERTS, DIM)
            for e in range(N_EXPERTS):
                add(f"model.layers.{l}.mlp.experts.{e}.up_proj.weight", FF, DIM)
                add(f"model.layers.{l}.mlp.experts.{e}.down_proj.weight", DIM, FF)
        else:
            add(f"model.layers.{l}.mlp.up_proj.weight", FF, DIM)
            add(f"model.layers.{l}.mlp.down_proj.weight", DIM, FF)
    add("model.norm.weight", DIM)
    add("lm_head.weight", VOCAB, DIM)
    return s


def main() -> None:
    store = build()
    ckpt = OUT / "model.bckpt"
    store.save(ckpt)

    # flat baseline: a checkpoint with no structural index — to get ANY tensor
    # you read the whole file. The honest baseline is the full file size.
    reader = CheckpointReader(ckpt)
    flat_size = reader.file_size  # same bytes, but a flat reader pays it for every access
    total = reader.file_size

    L: list[str] = []
    p = L.append
    p("# bhckpt — model checkpoint as .bckpt (measured demo)\n")
    sm, _ = reader.summary()
    p(f"- tensors: **{sm['n_tensors']}** · total weights: **{sm['total_MB']} MB** · "
      f"arch: {N_LAYERS} layers (MoE: {MOE_LAYERS}, {N_EXPERTS} experts)\n")
    p("A flat checkpoint must read the whole file to reach any tensor. The "
      "`.bckpt` keeps the tensor table as the index and reads weights on demand.\n")
    p("| reading | what it returns | bytes read | % of file | vs flat (reads all) |")
    p("|---|---|---|---|---|")

    def row(label, what, stats, n):
        ratio = flat_size / stats.bytes_read if stats.bytes_read else float("inf")
        p(f"| `{label}` | {what} ({n}) | {stats.bytes_read:,} B | "
          f"{stats.fraction*100:.2f}% | **{ratio:.0f}× less** |")

    sm, st = reader.summary()
    row("summary()", "architecture + tensor list, no weights", st, sm["n_tensors"])
    tn, st = reader.tensor("model.embed_tokens.weight")
    row("tensor('embed_tokens')", "one tensor", st, 1)
    ly, st = reader.layer(0)
    row("layer(0)", "all tensors of a dense layer", st, len(ly))
    ex, st = reader.expert(2, 0)
    row("expert(2, 0)", "ONE MoE expert of layer 2", st, len(ex))
    fl, st = reader.full()
    row("full()", "all weights (baseline)", st, len(fl))

    # the MoE headline: one expert vs the whole MoE layer
    moe_all, st_all = reader.layer(2)
    moe_one, st_one = reader.expert(2, 0)
    saving = st_all.bytes_read / st_one.bytes_read if st_one.bytes_read else 0
    p(f"\n**MoE routing:** loading **one** expert of layer 2 reads "
      f"{st_one.bytes_read/1e6:.2f} MB vs **{st_all.bytes_read/1e6:.2f} MB** for the "
      f"whole layer — **{saving:.1f}× less** to activate a single expert.\n")

    p("## What this demonstrates\n")
    p("- **Architecture without weights.** `summary()` returns the full tensor "
      "map (names, shapes, codecs) reading only the index — inspect a multi-GB "
      "checkpoint instantly, without loading a single weight.")
    p("- **The MoE expert is a first-class hierarchical read.** `expert(i, e)` "
      "loads one expert's tensors and nothing else — the natural unit for MoE "
      "serving and partial loading.")
    p("- **Honest boundary.** Selective per-tensor read already exists "
      "(`safetensors` header+mmap) — that is the anchor, not the novelty. The "
      "new piece is the union: hierarchy (layer/expert) + per-tensor codec "
      "routing recorded in the index + a Merkle face for provenance.")

    out = OUT / "RESULTS_BHCKPT_DEMO.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")

    print(f"tensors={sm['n_tensors']} total={total/1e6:.1f}MB")
    for label, fn in [("summary", reader.summary),
                      ("tensor(embed)", lambda: reader.tensor('model.embed_tokens.weight')),
                      ("layer(0)", lambda: reader.layer(0)),
                      ("expert(2,0)", lambda: reader.expert(2, 0)),
                      ("full", reader.full)]:
        _, s = fn()
        r = flat_size / s.bytes_read if s.bytes_read else 0
        print(f"  {label:16s} {s.bytes_read:9d} B  {s.fraction*100:6.2f}%  {r:6.0f}x less")
    print(f"report: {out}")


if __name__ == "__main__":
    main()
