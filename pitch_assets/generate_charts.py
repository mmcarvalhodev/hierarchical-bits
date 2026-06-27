"""Gera os gráficos comparativos do pitch BH (matplotlib), bilíngue.

PT  -> pitch_assets/*.png
EN  -> pitch_assets/en/*.png
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent
plt.rcParams.update({"font.size": 11, "figure.dpi": 130, "savefig.bbox": "tight"})

GREEN, RED, GRAY, BLUE = "#2e7d32", "#c62828", "#90a4ae", "#1565c0"

STR = {
    "pt": {
        "formats": [".bh (BH-União)", "WebP / AVIF", "PDF", "OLAP / Vector-DB", "AST / JSON"],
        "caps": ["Compacto", "Leitura\nseletiva", "Orquestra\nespecialistas",
                 "Hierarquia +\npertencimento", "Verificável", "Auto-\ndescritivo"],
        "title_a": "Matriz de capacidades — substrato-partilhado já é SOTA (DICOM/COG/lakeFS)",
        "doc_size": "Tamanho do documento", "kb": "KB", "smaller": "2,1× menor",
        "regs": ["plano", "gradiente", "texto", "diagrama"],
        "reads_all": "WebP (lê tudo)", "reads_region": ".bh (lê a região)",
        "bytes_region": "Bytes para ler UMA região", "less": "3–55× menos",
        "sup_b": "Economia de substrato-partilhado — real, e já SOTA",
        "items": ["Procedural (ondas)", "Procedural (anéis)", "Simbólico / composto",
                  "Leitura seletiva*", "Documento estruturado",
                  "Foto + estrutura (mista)", "Foto natural pura"],
        "tie": "empate",
        "xlabel_c": "ganho do BH (× menor / menos dados)  —  escala log",
        "title_c": "Onde o BH rende e onde DELEGA — a fronteira honesta",
        "foot_c": "* leitura seletiva: mecanismo já existente em OLAP/Merkle "
                  "(âncora de credibilidade, não novidade) · vermelho = o BH DELEGA ao WebP/AVIF",
    },
    "en": {
        "formats": [".bh (BH-Union)", "WebP / AVIF", "PDF", "OLAP / Vector-DB", "AST / JSON"],
        "caps": ["Compact", "Selective\nread", "Orchestrates\nspecialists",
                 "Hierarchy +\nbelonging", "Verifiable", "Self-\ndescribing"],
        "title_a": "Capability matrix — substrate-sharing is already SOTA (DICOM/COG/lakeFS)",
        "doc_size": "Document size", "kb": "KB", "smaller": "2.1× smaller",
        "regs": ["flat", "gradient", "text", "diagram"],
        "reads_all": "WebP (reads all)", "reads_region": ".bh (reads the region)",
        "bytes_region": "Bytes to read ONE region", "less": "3–55× less",
        "sup_b": "Substrate-sharing economics — real, and already SOTA",
        "items": ["Procedural (waves)", "Procedural (rings)", "Symbolic / composite",
                  "Selective read*", "Structured document",
                  "Photo + structure (mixed)", "Pure natural photo"],
        "tie": "tie",
        "xlabel_c": "BH gain (× smaller / less data)  —  log scale",
        "title_c": "Where BH pays off and where it DELEGATES — the honest boundary",
        "foot_c": "* selective read: mechanism already in OLAP/Merkle "
                  "(credibility anchor, not novelty) · red = BH DELEGATES to WebP/AVIF",
    },
}


def build(lang: str) -> None:
    S = STR[lang]
    out = ROOT if lang == "pt" else ROOT / lang
    out.mkdir(parents=True, exist_ok=True)

    # ---------- A) CAPABILITY MATRIX ----------
    formats, caps = S["formats"], S["caps"]
    M = np.array([
        [1, 1, 1, 1, 1, 1],   # .bh
        [1, 0, 0, 0, 0, 0],   # WebP/AVIF
        [1, 0, 1, 0, 0, 1],   # PDF
        [0, 1, 0, 1, 1, 0],   # OLAP/Vector-DB
        [0, 0, 0, 1, 0, 1],   # AST/JSON
    ])
    fig, ax = plt.subplots(figsize=(9, 4.2))
    for i in range(len(formats)):
        for j in range(len(caps)):
            ok = M[i, j] == 1
            ax.add_patch(plt.Rectangle((j, i), 1, 1, facecolor=(GREEN if ok else "#f5f5f5"),
                                       edgecolor="white", lw=2))
            ax.text(j + .5, i + .5, "✓" if ok else "—", ha="center", va="center",
                    color="white" if ok else GRAY, fontsize=15, fontweight="bold")
    ax.set_xlim(0, len(caps)); ax.set_ylim(0, len(formats))
    ax.set_xticks(np.arange(len(caps)) + .5); ax.set_xticklabels(caps, fontsize=9)
    ax.set_yticks(np.arange(len(formats)) + .5); ax.set_yticklabels(formats, fontsize=10)
    ax.invert_yaxis(); ax.tick_params(length=0)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(S["title_a"], fontweight="bold", pad=14)
    fig.savefig(out / "01_matriz_capacidades.png"); plt.close(fig)

    # ---------- B) THE UNION (document) ----------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.2))
    ax1.bar(["WebP", ".bh"], [4.8, 2.3], color=[GRAY, BLUE], width=.6)
    for x, v in zip([0, 1], [4.8, 2.3]):
        ax1.text(x, v + .08, f"{v} KB", ha="center", fontweight="bold")
    ax1.set_title(S["doc_size"], fontweight="bold")
    ax1.set_ylabel(S["kb"]); ax1.set_ylim(0, 5.6)
    ax1.text(.5, 5.2, S["smaller"], ha="center", color=GREEN, fontweight="bold")
    regs = S["regs"]; bh_read = [0.087, 0.096, 0.59, 1.8]
    x = np.arange(len(regs))
    ax2.bar(x - .2, [4.8] * 4, .4, color=GRAY, label=S["reads_all"])
    ax2.bar(x + .2, bh_read, .4, color=BLUE, label=S["reads_region"])
    ax2.set_xticks(x); ax2.set_xticklabels(regs)
    ax2.set_title(S["bytes_region"], fontweight="bold")
    ax2.set_ylabel(S["kb"]); ax2.legend(fontsize=9)
    ax2.text(1.5, 4.95, S["less"], ha="center", color=GREEN, fontweight="bold")
    fig.suptitle(S["sup_b"], fontweight="bold", y=1.02)
    fig.savefig(out / "02_uniao.png"); plt.close(fig)

    # ---------- C) WHERE IT PAYS OFF / DELEGATES (honest, log) ----------
    vals = [3572, 2904, 384, 100, 2.1, 1.0, 0.1]
    cols = [GREEN, GREEN, GREEN, GRAY, GREEN, GRAY, RED]
    names = S["items"]
    fig, ax = plt.subplots(figsize=(9.5, 4.6))
    y = np.arange(len(names))
    ax.barh(y, vals, color=cols, height=.62)
    ax.set_yticks(y); ax.set_yticklabels(names)
    ax.set_xscale("log")
    ax.axvline(1, color="#37474f", lw=1.2, ls="--")
    ax.text(1.15, len(names) - .3, S["tie"], color="#37474f", fontsize=9)
    for yi, v in zip(y, vals):
        ax.text(v * (1.25 if v >= 1 else 0.78), yi, f"{v:g}×", va="center",
                ha="left" if v >= 1 else "right", fontweight="bold", fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel(S["xlabel_c"])
    ax.set_title(S["title_c"], fontweight="bold", pad=12)
    for s in ["top", "right"]:
        ax.spines[s].set_visible(False)
    fig.text(0.5, -0.02, S["foot_c"], ha="center", fontsize=8, color=GRAY)
    fig.savefig(out / "03_onde_rende.png"); plt.close(fig)


if __name__ == "__main__":
    for lang in ("pt", "en"):
        build(lang)
        print(f"gerados ({lang}):", *(p.name for p in sorted(
            (ROOT if lang == 'pt' else ROOT / lang).glob('0*.png'))))
