# Flash Memory Pattern Simulator (PySide6)

Desktop app for:
- **Mode A**: Paper-style 2-bank/16-sector 256-band visualization with band inspect.
- **Mode B**: MT25Q logical die-like map with sector/subsector/page hierarchy and operations.

## Run

```bash
cd /workspace/memsem
python -m venv .venv
source .venv/bin/activate
pip install -r app/requirements.txt
python app/main.py
```

## Features

- QMainWindow with dockable panels.
- Left dock: pattern editor + required memory map formulas/examples.
- Right dock: inspector + MT25Q detail panel.
- Paper mode:
  - Two bank panes (Bank1 sectors 0..7, Bank2 sectors 15..8 mirrored).
  - Zoom+inspect canvas for sector/band/column crop.
  - Cell click reports bit value, word index, 32-byte hex+ASCII, 16x16 word bit-grid.
- MT25Q mode:
  - 32MiB memory simulation buffer.
  - 2 banks x (16x16 sectors) die-like map with central strip.
  - 4x4 visual super-block overlay boundaries.
  - Program/erase sector and first 4KB block quick actions.
  - NOR optional programming rule (`new = old & data`).
  - Jump-to-address inspector info.
- Save/load JSON configuration with visualization settings and compressed full memory dump.
- PNG export for current central view.

## Tests

```bash
PYTHONPATH=. pytest -q app/tests
```

Includes mapping formulas, deterministic paper-sector equality checks, and NOR rule test.
