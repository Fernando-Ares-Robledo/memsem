# memsem - MT25Q NOR Flash Visualizer

Desktop app (Windows-first, cross-platform) built with Python + PySide6 to simulate and visualize a single MT25Q-like 256Mbit NOR flash memory model with hierarchical zoom to bit level.

## Features
- **One unified MT25Q model**: 32MiB (`0x000000..0x01FFFFFF`) storage buffer with erase/program operations.
- **NOR rule programming**: optional `old & new` semantics (1->0 only) or overwrite mode.
- **Die canvas**: folded 64-sector block mapping, two banks separated by central strip region, pan/zoom/rotation and picking.
- **Hierarchical drill-down**:
  - overview sector tiles
  - sector detail with 32KB halves and 4KB blocks
  - 4KB detail with pages
  - page bit cells
- **Inspector dock**:
  - selected range metadata
  - bit-plane/band view (word bits, plane index, bit order)
  - clickable bit info and hex/ascii context
- **Programming UI**:
  - program/erase by 64KB sector, 32KB sub-sector, 4KB sub-sector, or arbitrary range
  - pattern segments (`text`, `hex`, `fill`) with repeat/clip behavior
- **Save/Load project**: JSON metadata + binary dump.
- **Export**: PNG export for die and inspector views.
- **Layout config in model**: block count/shape/gaps + hidden blocks support.

## Repository layout
- `core/`
  - `constants.py`: MT25Q constants and layout config dataclass
  - `addressing.py`: address formulas (sector/sub32/sub4/page)
  - `layout.py`: strict folded-64 mapping and global bank/block placement
  - `patterns.py`: pattern segment parsing and payload generation
  - `model.py`: 32MiB flash buffer, erase/program/summary/bit-plane, save/load
- `ui/`
  - `die_view.py`: QGraphicsView scene for overview + drill-down + worker summary rendering
  - `inspector.py`: bit-plane inspector and bit clicking details
  - `main_window.py`: full QMainWindow with docks, actions, controls
- `tests/`
  - required tests for mapping, formulas, NOR rule, 4KB region update isolation
- `main.py`: app entry point

## Run
```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Test
```bash
pytest -q
```
