from __future__ import annotations

from dataclasses import dataclass
import csv
import json
from pathlib import Path


@dataclass
class LayoutGrid:
    rows: int
    cols: int
    cells: list[list[int | None]]
    central_label: str = "Logic/Periphery"


class Stack16VerticalThenHorizontal:
    @staticmethod
    def position(local_id: int) -> tuple[int, int]:
        return (local_id % 16, local_id // 16)


class Folded64Layout:
    @staticmethod
    def position(local_id: int) -> tuple[int, int]:
        group = local_id // 16
        pos = local_id % 16
        row = pos if pos < 8 else 23 - pos
        col = 3 - group
        return row, col


def build_folded64_grid() -> LayoutGrid:
    cells = [[None for _ in range(4)] for _ in range(16)]
    for i in range(64):
        r, c = Folded64Layout.position(i)
        cells[r][c] = i
    return LayoutGrid(rows=16, cols=4, cells=cells)


def export_layout_json(layout: LayoutGrid, path: Path) -> None:
    path.write_text(json.dumps(layout.__dict__, indent=2))


def import_layout_json(path: Path) -> LayoutGrid:
    data = json.loads(path.read_text())
    return LayoutGrid(**data)


def export_layout_csv(layout: LayoutGrid, path: Path) -> None:
    with path.open("w", newline="") as f:
        writer = csv.writer(f)
        writer.writerows(layout.cells)


def import_layout_csv(path: Path) -> LayoutGrid:
    cells: list[list[int | None]] = []
    with path.open() as f:
        reader = csv.reader(f)
        for row in reader:
            out_row = []
            for v in row:
                v = v.strip()
                out_row.append(None if v == "" else int(v))
            cells.append(out_row)
    rows = len(cells)
    cols = max((len(r) for r in cells), default=0)
    for r in cells:
        if len(r) < cols:
            r.extend([None] * (cols - len(r)))
    return LayoutGrid(rows=rows, cols=cols, cells=cells)
