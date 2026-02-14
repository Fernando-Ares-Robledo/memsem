# NOR Flash Visualizer (MT25Q-like single model)

Desktop app (Python + PySide6) to simulate a single 32MiB NOR flash memory model and visualize it as two physical-looking arrays with folded 64-sector grouping.

## Highlights
- **Single model only**: 32MiB, sectors/blocks/pages exactly as specified.
- **Correct two-array layout**: Array0 (0..255) once, center strip, Array1 (256..511) once.
- **Distribución visual actual**: 8 secciones por fila (arriba y abajo), una fila de secciones por array.
- **One lightweight item per sector** with LOD rendering and background thumbnail jobs.
- **Subsector click selection on canvas**: zoom in and click 32KB half / 4KB block regions.
- **Program/Erase by selected region** from Program Dock (`Unit=selected`) and context menu.
- **Row/Column Strip View** dock: 16-sector strip shown as `0..7 | Sector | 15..8` mirrored presentation.
- **Pick column** tool in `Tools` to click any visual column and open paper-like strip ordering.
- **Single Sector View** dock for paper-like vertical sector inspection (easier comparison with lab imagery).
- **Deterministic green/yellow band thumbnails** and deterministic ECC overlay model.
- **Status metrics**: item count, queued render jobs, cache hit rate.
- **Paper-like preset** action (menu + toolbar) programs sectors 0..15 and validates deterministic hash pairs.
- **Direct sector selection** by Sector ID (0..511) without typing memory addresses (address jump remains available).

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
