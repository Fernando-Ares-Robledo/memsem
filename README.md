# MemSem Die Visualizer

Desktop app (PySide6) for unified flash-memory die visualization, pattern simulation, drill-down navigation, and paper-style band inspection.

## Features
- One `QGraphicsView` die canvas with selectable granularity:
  - Paper sectors (16 × 128KB)
  - MT25Q sectors 64KB (512)
  - MT25Q subsectors 32KB (1024)
  - MT25Q subsectors 4KB (8192)
  - MT25Q pages 256B (deep zoom subset)
- Layout engine:
  - `Stack16VerticalThenHorizontal`
  - `Folded64Layout` with exact 0..63 folded mapping
  - CSV/JSON import/export helpers for layout editor workflows
- Pattern generation with 1–2 segments (`text`, `hex`, `fill`) and clip/pad behavior.
- NOR flash model with erase/program (`old & data` rule) and fast summaries.
- Integrated band inspector (paper sectors), band index selection, and bit-color preview.
- Rotation controls (0/90/180/270 + free angle).
- Export PNG, Save/Load JSON project metadata.
- Built-in MT25Q reference panel with address examples + A24 segmentation.

## Structure
- `memsem/models/` core logic (patterns, flash, paper preset, MT25Q formulas, layouts, project I/O)
- `memsem/ui/` die canvas + main window
- `tests/` required tests for layout/address/paper determinism/NOR rule

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install pyside6 numpy pytest
python -m memsem.app
```

## Test
```bash
pytest -q
```
