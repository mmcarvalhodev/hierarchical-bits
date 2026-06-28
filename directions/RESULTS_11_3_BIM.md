# 11.3 BIM / Digital Twins — targeted property read (measured)

- 4000 elements · layers {'geometry': 2048, 'thermal': 120, 'cost': 80, 'structural': 150} · full model 10,146,226 B

| query | bytes read | % of full | vs full-load |
|---|---|---|---|
| thermal analysis (thermal+geometry) | 9,226,226 | 90.9% | **1.1× less** |
| cost report (cost only) | 874,226 | 8.6% | **11.6× less** |
| structural check (structural+geometry) | 9,346,226 | 92.1% | **1.1× less** |
| metadata only (no geometry: thermal+cost+structural) | 1,954,226 | 19.3% | **5.2× less** |
| full load (baseline) | 10,146,226 | 100.0% | 1× |

## Verdict (honest)

- **Claim holds, mechanically:** a targeted query reads far less than the full model — geometry dominates, so any query that skips it (cost report) is tiny, and even thermal/structural skip the other layers.
- **But this is partial loading — already SOTA.** IFC sub-model extraction, glTF `EXT_*` + 3D Tiles streaming, and BIM viewers already load only the needed elements/properties. The number is *vs naive full-load*, not vs those tools.
- **And it tests the wrong angle.** The applicability sweep flagged CAD/BIM as the one BUILD — but for the **rival discipline overlays** (arch/structural/MEP disagreeing on one element), i.e. the FCIR property. This test measures selective read (ANCHOR), not that. z.ai's framing measures the part that already exists.
