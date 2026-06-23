# Zenodo submission — ready-to-use kit

This file has everything you need to publish the study on Zenodo and get a
permanent DOI. The PDF is already generated; the metadata below is paste-ready.

---

## The file to upload

**`BH_MASTER.pdf`** — the preprint (cover page + the full English study,
~11 pages, generated from `BH_MASTER.en.md`).
Regenerate any time with:

```
X:/miniconda3/python.exe print_pdf.py
"C:/Program Files/Google/Chrome/Application/chrome.exe" --headless=new --disable-gpu --no-pdf-header-footer --print-to-pdf="X:/bitH/BH_MASTER.pdf" "file:///X:/bitH/_print_master.html"
```

---

## Metadata (paste-ready)

**Title**
```
Hierarchical Bits: A Structural Envelope for Orchestrating Representations — Method, Measurements and Boundaries
```

**Authors** — `Carvalho, Márcio M.` · Affiliation: `Independent researcher`

**Resource type** — `Publication` → `Technical note`
(not "Journal article" — this is a technical report, not peer-reviewed.)

**License** — `Creative Commons Attribution 4.0 International (CC BY 4.0)`

**Keywords**
```
hierarchical data, structural envelope, codec orchestration, selective reading, agent memory, data formats
```

**Description**
```
Hierarchical Bits (BH) is a data-format paradigm investigated as a structural
envelope rather than a codec. This technical note tests the hypothesis ("the
byte is an implicit tree; hierarchy is interpretation") across nine independent
angles — image codec, database aggregation, Merkle verification, co-registered
layers (wafer/video), GPU data movement, multimodal AI storage,
symbolic/compositional density, decode-as-program, and orchestration — each
with declared falsifiable claims, exact correctness as a gate, and honest
baselines distinguishing gains vs naive from gains vs state of the art.

Central finding: BH does not compress dense signal better than JPEG/WebP/AVIF
(it loses — measured), but as a structural envelope it (a) makes structure
explicit at 0–6% cost, (b) routes each region's residual to the right
specialist, and (c) offers multiple reads over one structure. Anchor result: a
structured document is 2.1× smaller than WebP and readable per-region in 3–55×
fewer bytes, within one file. A usable prototype (bhmem, agent memory)
accompanies the study. The transversal law: BH pays off to the extent the data
is structure, not signal; the boundary is structure recognition, not entropy.
```

---

## Option A — Quick manual upload (2 minutes, gives a DOI now)

1. Go to **https://zenodo.org** → **Log in with GitHub** (most convenient).
2. **New upload** → drag in **`BH_MASTER.pdf`**.
3. Fill the fields with the metadata above.
4. **Publish.** You get a permanent DOI in seconds (e.g. `10.5281/zenodo.XXXXXXX`).

This DOI is for the PDF only. Use Option B as well if you want the *code* archived
and auto-versioned.

## Option B — GitHub integration (auto-DOI on every release)

This archives the whole repository and mints a DOI automatically each release.
The repo already contains [`.zenodo.json`](.zenodo.json) so Zenodo reads the
metadata above without you retyping it.

1. **https://zenodo.org** → log in with GitHub.
2. Top-right menu → **GitHub** → find **`mmcarvalhodev/hierarchical-bits`** →
   flip the toggle **ON**. (This installs the release webhook.)
3. Back on GitHub: **Releases** → **Draft a new release** → tag `v1.0.0`,
   title `Hierarchical Bits v1.0.0` → **Publish release**.
4. Zenodo catches the release, reads `.zenodo.json`, and mints the DOI
   (visible back on the Zenodo "GitHub" page within a minute).

You get **two DOIs**: a *concept DOI* (always points to the latest version) and
a *version DOI* (this specific release). Cite the concept DOI in the README.

---

## After you have the DOI — close the loop

1. **README badge** — add at the very top of `README.md` (replace the number):
   ```markdown
   [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.XXXXXXX.svg)](https://doi.org/10.5281/zenodo.XXXXXXX)
   ```
2. **CITATION.cff** — uncomment the `doi:` line in [`CITATION.cff`](CITATION.cff)
   and fill it in (GitHub then shows a "Cite this repository" button).
3. **Homepage / LinkedIn** — link the DOI as the formal preprint reference.

That closes the cycle: arrivals from the site find the formal preprint;
arrivals from Zenodo find the code.

---

## Notes

- **Affiliation** is optional on Zenodo; "Independent researcher" is fine, no
  institution required.
- The repository keeps the **dual license**: code under Apache-2.0
  ([`LICENSE`](LICENSE)), documents under CC BY 4.0
  ([`LICENSE-docs.md`](LICENSE-docs.md)). The Zenodo record (the PDF/document)
  is the CC BY 4.0 side.
- A Portuguese PDF can be produced too (point `print_pdf.py` at `BH_MASTER.md`)
  if you want a bilingual Zenodo record — just ask.
