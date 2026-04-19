from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import date, datetime, time
from decimal import Decimal
import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple


class ExcelAdapter(ABC):
    @abstractmethod
    def parse_workbook(self, excel_path: Path | str) -> List[Dict[str, Any]]:
        raise NotImplementedError

    def close(self) -> None:
        return None


class OpenpyxlExcelAdapter(ExcelAdapter):
    """Read workbook/sheet/cell data and normalize into adapter-level sheet payloads."""

    def __init__(self, data_only: bool = True) -> None:
        self.data_only = data_only

    def parse_workbook(self, excel_path: Path | str) -> List[Dict[str, Any]]:
        try:
            openpyxl_module = importlib.import_module("openpyxl")
            load_workbook = getattr(openpyxl_module, "load_workbook")
        except Exception as exc:
            raise RuntimeError("openpyxl is required. Install with: pip install openpyxl") from exc

        path = Path(excel_path).resolve()
        if not path.exists():
            raise FileNotFoundError(f"Excel file not found: {path}")
        if path.suffix.lower() != ".xlsx":
            raise ValueError("Only .xlsx files are supported")

        wb = load_workbook(filename=str(path), data_only=self.data_only, read_only=False)
        try:
            sheets: List[Dict[str, Any]] = []
            for idx, ws in enumerate(wb.worksheets):
                sheets.append(self._parse_sheet(ws, sheet_index=idx))
            return sheets
        finally:
            wb.close()

    def _parse_sheet(self, ws: Any, sheet_index: int) -> Dict[str, Any]:
        min_row, max_row, min_col, max_col = self._effective_bounds(ws)
        merged_value_map = self._merged_value_map(ws)

        rows: List[Dict[str, Any]] = []
        if min_row > 0 and max_row >= min_row and min_col > 0 and max_col >= min_col:
            for row_idx in range(min_row, max_row + 1):
                values: List[Any] = []
                for col_idx in range(min_col, max_col + 1):
                    cell_value = ws.cell(row=row_idx, column=col_idx).value
                    if cell_value is None:
                        cell_value = merged_value_map.get((row_idx, col_idx))
                    values.append(self._normalize_value(cell_value))
                rows.append({"row_index": row_idx, "values": values})

        return {
            "type": "excel_sheet",
            "sheet_name": ws.title,
            "sheet_index": sheet_index,
            "min_row": min_row,
            "max_row": max_row,
            "min_col": min_col,
            "max_col": max_col,
            "n_rows": max(0, max_row - min_row + 1) if min_row and max_row else 0,
            "n_cols": max(0, max_col - min_col + 1) if min_col and max_col else 0,
            "rows": rows,
            "merged_ranges": [str(rng) for rng in ws.merged_cells.ranges],
        }

    def _effective_bounds(self, ws: Any) -> Tuple[int, int, int, int]:
        min_row: Optional[int] = None
        max_row: Optional[int] = None
        min_col: Optional[int] = None
        max_col: Optional[int] = None

        for row in ws.iter_rows(values_only=False):
            for cell in row:
                value = cell.value
                if value is None:
                    continue
                row_idx = int(cell.row)
                col_idx = int(cell.column)
                min_row = row_idx if min_row is None else min(min_row, row_idx)
                max_row = row_idx if max_row is None else max(max_row, row_idx)
                min_col = col_idx if min_col is None else min(min_col, col_idx)
                max_col = col_idx if max_col is None else max(max_col, col_idx)

        if min_row is None or max_row is None or min_col is None or max_col is None:
            return 0, 0, 0, 0
        return min_row, max_row, min_col, max_col

    def _merged_value_map(self, ws: Any) -> Dict[Tuple[int, int], Any]:
        value_map: Dict[Tuple[int, int], Any] = {}
        for merged in ws.merged_cells.ranges:
            min_col, min_row, max_col, max_row = merged.bounds
            anchor_value = ws.cell(row=min_row, column=min_col).value
            for row_idx in range(min_row, max_row + 1):
                for col_idx in range(min_col, max_col + 1):
                    if row_idx == min_row and col_idx == min_col:
                        continue
                    value_map[(row_idx, col_idx)] = anchor_value
        return value_map

    def _normalize_value(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, (int, float, bool, str)):
            return value
        if isinstance(value, Decimal):
            return float(value)
        if isinstance(value, datetime):
            return value.isoformat(sep=" ", timespec="seconds")
        if isinstance(value, date):
            return value.isoformat()
        if isinstance(value, time):
            return value.isoformat(timespec="seconds")
        return str(value)


def workbook_to_ocr_like_pages(sheet_payloads: Sequence[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
    """Convert sheet payloads to page-like blocks for OCR-style downstream compatibility."""
    pages: List[List[Dict[str, Any]]] = []
    for sheet in sheet_payloads:
        if not isinstance(sheet, dict):
            continue
        min_col = int(sheet.get("min_col") or 1)
        rows_raw = sheet.get("rows")
        rows: List[Dict[str, Any]] = rows_raw if isinstance(rows_raw, list) else []
        blocks: List[Dict[str, Any]] = []
        for idx, row in enumerate(rows):
            if not isinstance(row, dict):
                continue
            row_idx = int(row.get("row_index") or idx + 1)
            values_raw = row.get("values")
            values: List[Any] = values_raw if isinstance(values_raw, list) else []
            text = " | ".join(str(v).strip() for v in values if v is not None and str(v).strip())
            blocks.append(
                {
                    "index": idx,
                    "label": "excel_row",
                    "content": text,
                    "bbox_2d": [
                        min_col,
                        row_idx,
                        min_col + max(0, len(values) - 1),
                        row_idx,
                    ],
                }
            )
        pages.append(blocks)
    return pages
