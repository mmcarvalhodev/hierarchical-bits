"""Painel de evidências — os testes onde o BH foi superior, com o baseline
rotulado. Bilíngue: PT -> pitch_assets/*.png · EN -> pitch_assets/en/*.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
plt.rcParams.update({"font.size": 9, "figure.dpi": 130, "savefig.bbox": "tight"})
GREEN, BLUE, GRAY = "#2e7d32", "#1565c0", "#90a4ae"

STR = {
    "pt": {
        "sup": "Medições do estudo (codec / substrato) — contra o baseline rotulado",
        "p1_title": "Dado gerado por regra → programa", "p1_fam": ["anéis", "ondas", "xadrez", "grad."],
        "p1_y": "× menor que WebP", "p1_note": "vs WebP (SOTA) · reconstrói exato",
        "p2_title": "Conteúdo casado (gradiente)", "p2_q": ["50,2 dB", "57,9 dB"],
        "p2_call": "48× menor\nE qualidade\nmaior", "kb": "KB",
        "p3_title": "Ler UMA região (capacidade)", "p3_regs": ["plano", "grad.", "texto", "diagr."],
        "p3_all": "WebP (lê tudo)", "p3_reg": ".bh (só a região)", "p3_y": "KB lidos",
        "p3_call": "3–55×\nmenos\nbytes",
        "p4_title": "Dado simbólico / composto", "p4_x": ["vetor\ndenso", "envelope\nBH"],
        "p4_y": "MB (1M conceitos)", "p4_call": "384× menor\n+ consultas que o\ndenso nem formula",
        "p5_title": "Camadas co-registradas (vídeo)", "p5_x": ["indep.", "temporal", "wafer +\ntemporal"],
        "p5_y": "× vs independente", "p5_note": "estrutura+redundância compõem",
        "p6_title": "Face de leitura (âncora)", "p6_x": ["banco", "GPU", "Merkle"],
        "p6_y": "× vs varredura ingênua",
        "p6_note": "mecanismo já-SOTA (OLAP/Merkle):\ncredibilidade, NÃO novidade",
    },
    "en": {
        "sup": "Study measurements (codec / substrate) — against the labeled baseline",
        "p1_title": "Rule-generated data → program", "p1_fam": ["rings", "waves", "checker", "grad."],
        "p1_y": "× smaller than WebP", "p1_note": "vs WebP (SOTA) · reconstructs exact",
        "p2_title": "Matched content (gradient)", "p2_q": ["50.2 dB", "57.9 dB"],
        "p2_call": "48× smaller\nAND higher\nquality", "kb": "KB",
        "p3_title": "Read ONE region (capability)", "p3_regs": ["flat", "grad.", "text", "diagr."],
        "p3_all": "WebP (reads all)", "p3_reg": ".bh (region only)", "p3_y": "KB read",
        "p3_call": "3–55×\nfewer\nbytes",
        "p4_title": "Symbolic / composite data", "p4_x": ["dense\nvector", "BH\nenvelope"],
        "p4_y": "MB (1M concepts)", "p4_call": "384× smaller\n+ queries dense\ncan't formulate",
        "p5_title": "Co-registered layers (video)", "p5_x": ["indep.", "temporal", "wafer +\ntemporal"],
        "p5_y": "× vs independent", "p5_note": "structure+redundancy compose",
        "p6_title": "Reading face (anchor)", "p6_x": ["DB", "GPU", "Merkle"],
        "p6_y": "× vs naive scan",
        "p6_note": "already-SOTA mechanism (OLAP/Merkle):\ncredibility, NOT novelty",
    },
}


def build(lang: str) -> None:
    S = STR[lang]
    out = ROOT if lang == "pt" else ROOT / lang
    out.mkdir(parents=True, exist_ok=True)
    fig, axs = plt.subplots(2, 3, figsize=(12.5, 7))

    # 1) decode-programa
    ax = axs[0, 0]
    rat = [2904, 3572, 809, 2096]
    ax.bar(S["p1_fam"], rat, color=GREEN)
    ax.set_yscale("log"); ax.set_ylabel(S["p1_y"])
    for i, v in enumerate(rat):
        ax.text(i, v * 1.15, f"{v:,}×", ha="center", fontsize=8, fontweight="bold")
    ax.set_title(S["p1_title"], fontweight="bold", fontsize=10)
    ax.text(0, 0.92, S["p1_note"], transform=ax.transAxes, fontsize=7.5, color=GRAY)
    ax.set_ylim(100, 9000)

    # 2) matched content
    ax = axs[0, 1]
    ax.bar(["WebP", "BH"], [116.7, 2.4], color=[GRAY, BLUE])
    for i, (v, q) in enumerate([(116.7, S["p2_q"][0]), (2.4, S["p2_q"][1])]):
        ax.text(i, v + 3, f"{v} KB\n{q}", ha="center", fontsize=8, fontweight="bold")
    ax.set_ylabel(S["kb"]); ax.set_ylim(0, 145)
    ax.set_title(S["p2_title"], fontweight="bold", fontsize=10)
    ax.text(0.5, 0.55, S["p2_call"], transform=ax.transAxes, fontsize=8.5,
            color=GREEN, fontweight="bold", ha="center")

    # 3) union — read one region
    ax = axs[0, 2]
    ax.bar(np.arange(4) - .2, [4.8] * 4, .4, color=GRAY, label=S["p3_all"])
    ax.bar(np.arange(4) + .2, [0.087, 0.096, 0.59, 1.8], .4, color=BLUE, label=S["p3_reg"])
    ax.set_xticks(range(4)); ax.set_xticklabels(S["p3_regs"])
    ax.set_ylabel(S["p3_y"]); ax.legend(fontsize=7, loc="upper left")
    ax.set_title(S["p3_title"], fontweight="bold", fontsize=10)
    ax.text(0.97, 0.5, S["p3_call"], transform=ax.transAxes, fontsize=8.5,
            color=GREEN, fontweight="bold", ha="right")

    # 4) symbolic / composite
    ax = axs[1, 0]
    ax.bar(S["p4_x"], [3070, 8], color=[GRAY, GREEN])
    ax.set_yscale("log"); ax.set_ylabel(S["p4_y"])
    for i, v in enumerate([3070, 8]):
        ax.text(i, v * 1.3, f"{v} MB", ha="center", fontsize=8, fontweight="bold")
    ax.set_title(S["p4_title"], fontweight="bold", fontsize=10)
    ax.text(0.97, 0.55, S["p4_call"], transform=ax.transAxes, fontsize=8,
            color=GREEN, fontweight="bold", ha="right")
    ax.set_ylim(3, 9000)

    # 5) co-registered layers (video)
    ax = axs[1, 1]
    vals = [1.0, 1.65, 2.13]
    ax.bar(S["p5_x"], vals, color=[GRAY, BLUE, GREEN])
    for i, v in enumerate(vals):
        ax.text(i, v + .04, f"{v}×", ha="center", fontsize=8, fontweight="bold")
    ax.set_ylabel(S["p5_y"]); ax.set_ylim(0, 2.5)
    ax.set_title(S["p5_title"], fontweight="bold", fontsize=10)
    ax.text(0, 0.92, S["p5_note"], transform=ax.transAxes, fontsize=7.5, color=GRAY)

    # 6) reading face (anchor)
    ax = axs[1, 2]
    ax.bar(S["p6_x"], [488, 1750, 52103], color=GRAY)
    ax.set_yscale("log"); ax.set_ylabel(S["p6_y"])
    for i, v in enumerate([488, 1750, 52103]):
        ax.text(i, v * 1.3, f"{v:,}×", ha="center", fontsize=8, fontweight="bold")
    ax.set_title(S["p6_title"], fontweight="bold", fontsize=10)
    ax.text(0, 0.92, S["p6_note"], transform=ax.transAxes, fontsize=7.5, color=GRAY)
    ax.set_ylim(100, 200000)

    fig.suptitle(S["sup"], fontweight="bold", fontsize=13, y=1.0)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fig.savefig(out / "04_evidencias.png"); plt.close(fig)


if __name__ == "__main__":
    for lang in ("pt", "en"):
        build(lang)
        print(f"gerado ({lang}): 04_evidencias.png")
