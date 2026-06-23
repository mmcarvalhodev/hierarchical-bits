"""Gera um PDF de preprint a partir de BH_MASTER.en.md.

Capa + corpo (a partir do EXECUTIVE SUMMARY), CSS de impressão A4.
Produz _print_master.html; a conversão para PDF é feita pelo Chrome headless
(ver comando no fim / no guia ZENODO_SUBMISSION.md).

Rodar:  X:/miniconda3/python.exe X:/bitH/print_pdf.py
"""
from __future__ import annotations

from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "BH_MASTER.en.md"
OUT_HTML = ROOT / "_print_master.html"

TITLE = "Hierarchical Bits"
SUBTITLE = ("A Structural Envelope for Orchestrating Representations"
            " — Method, Measurements and Boundaries")
AUTHOR = "Márcio M. Carvalho"
PERIOD = "December 2025 – June 2026"
REPO = "github.com/mmcarvalhodev/hierarchical-bits"

CSS = """
@page { size: A4; margin: 22mm 20mm 20mm 20mm; }
* { box-sizing: border-box; }
body { color: #1a1a1a; font: 10.5pt/1.55 Georgia, "Times New Roman", serif;
       margin: 0; }
.cover { height: 247mm; display: flex; flex-direction: column;
         justify-content: center; page-break-after: always; }
.cover .kicker { font: 600 11pt/1 -apple-system, "Segoe UI", sans-serif;
                 letter-spacing: .18em; text-transform: uppercase; color: #2e7d32; }
.cover h1 { font: 700 34pt/1.1 Georgia, serif; margin: 14px 0 6px; }
.cover .sub { font: 400 15pt/1.4 Georgia, serif; color: #333; margin-bottom: 40px; }
.cover .meta { font: 10.5pt/1.7 -apple-system, "Segoe UI", sans-serif; color: #222; }
.cover .meta b { color: #000; }
.cover .rule { height: 3px; width: 70px; background: #2e7d32; margin: 0 0 26px; }
.cover .foot { margin-top: 44px; font: 9.5pt/1.5 -apple-system, sans-serif; color: #666; }
h1, h2, h3, h4 { font-family: -apple-system, "Segoe UI", Helvetica, sans-serif;
                 line-height: 1.25; page-break-after: avoid; }
h2 { font-size: 15pt; border-bottom: 1px solid #ccc; padding-bottom: 3px;
     margin-top: 22px; }
h3 { font-size: 12pt; margin-top: 16px; }
p { text-align: justify; }
a { color: #1b5e20; text-decoration: none; }
blockquote { margin: 10px 0; padding: 4px 14px; border-left: 3px solid #2e7d32;
             background: #f4f8f4; }
code { font: 9pt/1.4 "Consolas", monospace; background: #f4f4f4;
       padding: .1em .35em; border-radius: 3px; }
pre { background: #f6f8fa; border: 1px solid #e1e4e8; border-radius: 6px;
      padding: 11px 13px; overflow: hidden; page-break-inside: avoid;
      white-space: pre-wrap; }
pre code { background: none; padding: 0; font-size: 8.6pt; }
table { border-collapse: collapse; width: 100%; margin: 12px 0; font-size: 9.2pt;
        page-break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 5px 8px; text-align: left;
         vertical-align: top; }
th { background: #f0f2f4; font-weight: 700; }
hr { border: 0; border-top: 1px solid #ddd; margin: 18px 0; }
"""


def main() -> None:
    raw = SRC.read_text(encoding="utf-8")
    idx = raw.find("## EXECUTIVE SUMMARY")
    body_md = raw[idx:] if idx >= 0 else raw
    body = markdown.markdown(
        body_md, extensions=["extra", "tables", "fenced_code", "sane_lists"],
        output_format="html5")

    cover = f"""
<div class="cover">
  <div class="kicker">Technical Note · Open</div>
  <h1>{TITLE}</h1>
  <div class="sub">{SUBTITLE}</div>
  <div class="rule"></div>
  <div class="meta">
    <b>Author:</b> {AUTHOR}<br>
    <b>Study period:</b> {PERIOD}<br>
    <b>License:</b> Creative Commons Attribution 4.0 (CC BY 4.0)<br>
    <b>Repository:</b> {REPO}<br>
    <b>DOI:</b> assigned upon publication on Zenodo
  </div>
  <div class="foot">Technical demonstration report — every claim is accompanied by
  the method and the measured number. 128+ automated tests green; exact
  correctness as a gate before every measurement.</div>
</div>
"""
    html = (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f"<title>{TITLE}</title><style>{CSS}</style></head><body>"
            f"{cover}{body}</body></html>")
    OUT_HTML.write_text(html, encoding="utf-8")
    print(f"wrote {OUT_HTML}")


if __name__ == "__main__":
    main()
