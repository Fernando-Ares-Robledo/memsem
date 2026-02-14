# NOR Flash Visualizer (MT25Q-like single model)

Desktop app (Python + PySide6) to simulate a single 32MiB NOR flash memory model and visualize it as two physical-looking arrays with folded 64-sector grouping.

## Features
- Single model only: 32MiB, sectors/blocks/pages as requested.
- One unified die canvas: Array0 (top), decorative center strip, Array1 (bottom).
- Folded 64-sector block layout with gap row.
- Program/erase by 64KB sector, 32KB block, 4KB block, 256B page, and arbitrary range.
- LOD sector rendering with deterministic green/yellow band-like visuals.
- Sector dataset view (256 datasets/pages) and simulated ECC overlay logic (10 bits/page).
- Jump-to address, click selection, double-click drill-down to sector.
- Rotation controls (0/90/180/270).
- Save/load project (.json + .bin), export PNG from current view.

## Run
```bash
cd app
python -m pip install -r requirements.txt
python main.py
```

## Tests
```bash
cd app
PYTHONPATH=. pytest -q
```

## Notes
- ECC shown here is a deterministic parity-based *visualization overlay* (not a claim of physical storage).
- NOR programming rule is modeled with bitwise AND when enabled.
