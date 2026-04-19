from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple


def _column_letter(index: int) -> str:
    idx = max(1, int(index))
    letters = ""
    while idx > 0:
        idx, rem = divmod(idx - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


@dataclass
class ExcelChunkerConfig:
    max_rows_per_chunk: int = 20
    header_search_rows: int = 6
    max_text_chars_per_row: int = 220


class ExcelChunker:
    """Build QA-friendly structured chunks from adapter-level sheet payloads."""

    def __init__(self, config: Optional[ExcelChunkerConfig] = None) -> None:
        self.config = config or ExcelChunkerConfig()

    def chunk_workbook(
        self,
        sheet_payloads: Sequence[Dict[str, Any]],
        *,
        doc_id: str = "excel_doc",
    ) -> List[Dict[str, Any]]:
        all_chunks: List[Dict[str, Any]] = []
        for sheet in sheet_payloads:
            if not isinstance(sheet, dict):
                continue
            all_chunks.extend(self.chunk_sheet(sheet, doc_id=doc_id))
        return all_chunks

    def chunk_sheet(self, sheet: Dict[str, Any], *, doc_id: str = "excel_doc") -> List[Dict[str, Any]]:
        rows = sheet.get("rows") if isinstance(sheet.get("rows"), list) else []
        if not rows:
            return []

        headers, header_row_idx, min_col = self._infer_headers(sheet, rows)
        data_rows = [r for r in rows if int(r.get("row_index") or 0) > header_row_idx]
        if not data_rows:
            data_rows = rows

        chunks: List[Dict[str, Any]] = []
        chunk_size = max(1, int(self.config.max_rows_per_chunk))
        sheet_name = str(sheet.get("sheet_name") or "Sheet")
        sheet_index = int(sheet.get("sheet_index") or 0)
        max_col = int(sheet.get("max_col") or (min_col + len(headers) - 1))

        for chunk_index, start in enumerate(range(0, len(data_rows), chunk_size)):
            part = data_rows[start : start + chunk_size]
            if not part:
                continue

            row_start = int(part[0].get("row_index") or 0)
            row_end = int(part[-1].get("row_index") or row_start)
            row_records = self._build_row_records(part, headers)
            chunk_range = self._to_excel_range(min_col, row_start, max_col, row_end)
            text = self._serialize_chunk_text(sheet_name, chunk_range, headers, row_records)

            chunk_id = f"{doc_id}_{sheet_name}_c{chunk_index:03d}"
            chunk = {
                "type": "excel_chunk",
                "chunk_id": chunk_id,
                "index": chunk_index,
                "sheet": sheet_name,
                "sheet_index": sheet_index,
                "range": chunk_range,
                "headers": headers,
                "header_row": header_row_idx,
                "rows": row_records,
                "text": text,
                "structure": {
                    "row_count": len(row_records),
                    "col_count": len(headers),
                    "has_header": bool(headers),
                },
                "position": {
                    "sheet": sheet_name,
                    "row_start": row_start,
                    "row_end": row_end,
                    "col_start": min_col,
                    "col_end": max_col,
                },
                # OCR-like compatibility fields
                "label": "excel_table",
                "content": text,
                "bbox_2d": [min_col, row_start, max_col, row_end],
                "meta": {
                    "source": "excel",
                    "sheet": sheet_name,
                    "range": chunk_range,
                    "headers": headers,
                },
            }
            chunks.append(chunk)

        return chunks

    def _infer_headers(
        self,
        sheet: Dict[str, Any],
        rows: Sequence[Dict[str, Any]],
    ) -> Tuple[List[str], int, int]:
        min_col = int(sheet.get("min_col") or 1)
        max_scan = min(len(rows), max(1, int(self.config.header_search_rows)))
        best_idx = 0
        best_score = -1.0

        for idx in range(max_scan):
            row = rows[idx]
            values_raw = row.get("values")
            values: List[Any] = values_raw if isinstance(values_raw, list) else []
            non_empty = [v for v in values if v is not None and str(v).strip()]
            if not values:
                continue
            uniqueness = len({str(v).strip().lower() for v in non_empty}) / max(1, len(non_empty))
            density = len(non_empty) / max(1, len(values))
            score = density * 0.7 + uniqueness * 0.3
            if score > best_score:
                best_score = score
                best_idx = idx

        header_row = rows[best_idx]
        header_row_idx = int(header_row.get("row_index") or 1)
        raw_headers_raw = header_row.get("values")
        raw_headers: List[Any] = raw_headers_raw if isinstance(raw_headers_raw, list) else []
        headers = self._normalize_headers(raw_headers)
        return headers, header_row_idx, min_col

    def _normalize_headers(self, raw_headers: Sequence[Any]) -> List[str]:
        used: Dict[str, int] = {}
        headers: List[str] = []
        for idx, value in enumerate(raw_headers):
            base = str(value).strip() if value is not None and str(value).strip() else f"Column_{idx + 1}"
            key = base.lower()
            if key not in used:
                used[key] = 1
                headers.append(base)
                continue
            used[key] += 1
            headers.append(f"{base}_{used[key]}")
        return headers

    def _build_row_records(self, rows: Sequence[Dict[str, Any]], headers: Sequence[str]) -> List[Dict[str, Any]]:
        records: List[Dict[str, Any]] = []
        for row in rows:
            row_idx = int(row.get("row_index") or 0)
            values_raw = row.get("values")
            values: List[Any] = values_raw if isinstance(values_raw, list) else []
            mapped: Dict[str, Any] = {}
            for idx, header in enumerate(headers):
                value = values[idx] if idx < len(values) else None
                mapped[header] = value
            records.append(
                {
                    "row_index": row_idx,
                    "values": mapped,
                }
            )
        return records

    def _serialize_chunk_text(
        self,
        sheet_name: str,
        chunk_range: str,
        headers: Sequence[str],
        row_records: Sequence[Dict[str, Any]],
    ) -> str:
        header_line = " | ".join(headers) if headers else "(no header)"
        lines: List[str] = [
            f"工作表: {sheet_name}",
            f"范围: {chunk_range}",
            f"表头: {header_line}",
        ]

        for row in row_records:
            row_idx = int(row.get("row_index") or 0)
            values_obj = row.get("values")
            values: Dict[str, Any] = values_obj if isinstance(values_obj, dict) else {}
            cells: List[str] = []
            for header in headers:
                value = values.get(header)
                if value is None or not str(value).strip():
                    continue
                short = self._truncate(str(value).strip(), self.config.max_text_chars_per_row)
                cells.append(f"{header}: {short}")
            if not cells:
                lines.append(f"行 {row_idx}: (空行)")
            else:
                lines.append(f"行 {row_idx}: " + "; ".join(cells))

        lines.append(f"块摘要: 该块包含 {len(row_records)} 行，{len(headers)} 列。")
        return "\n".join(lines).strip()

    def _to_excel_range(self, col_start: int, row_start: int, col_end: int, row_end: int) -> str:
        left = f"{_column_letter(max(1, col_start))}{max(1, row_start)}"
        right = f"{_column_letter(max(col_start, col_end))}{max(row_start, row_end)}"
        return f"{left}:{right}"

    def _truncate(self, text: str, limit: int) -> str:
        if len(text) <= limit:
            return text
        return text[: limit - 3] + "..."


def evaluate_excel_chunk_quality(chunks: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    total_chunks = len(chunks)
    if total_chunks == 0:
        return {
            "score": 0.0,
            "issues": ["no_excel_chunks"],
            "metrics": {
                "chunk_count": 0.0,
                "avg_rows_per_chunk": 0.0,
                "empty_value_ratio": 1.0,
                "header_completeness": 0.0,
                "data_consistency": 0.0,
            },
        }

    total_rows = 0
    total_cells = 0
    empty_cells = 0
    header_cells = 0
    valid_header_cells = 0
    consistency_hits = 0

    for chunk in chunks:
        headers_raw = chunk.get("headers") if isinstance(chunk, dict) else None
        rows_raw = chunk.get("rows") if isinstance(chunk, dict) else None
        headers: List[Any] = headers_raw if isinstance(headers_raw, list) else []
        rows: List[Dict[str, Any]] = rows_raw if isinstance(rows_raw, list) else []
        header_cells += len(headers)
        valid_header_cells += sum(1 for h in headers if str(h).strip() and not str(h).startswith("Column_"))

        total_rows += len(rows)
        for row in rows:
            values_obj = row.get("values")
            values: Dict[str, Any] = values_obj if isinstance(values_obj, dict) else {}
            total_cells += len(headers)
            row_non_empty = 0
            for header in headers:
                value = values.get(header)
                if value is None or not str(value).strip():
                    empty_cells += 1
                else:
                    row_non_empty += 1
            if headers and row_non_empty >= max(1, int(len(headers) * 0.4)):
                consistency_hits += 1

    empty_ratio = empty_cells / max(1, total_cells)
    header_completeness = valid_header_cells / max(1, header_cells)
    data_consistency = consistency_hits / max(1, total_rows)

    penalty = min(0.5, empty_ratio * 0.7) + min(0.3, (1.0 - header_completeness) * 0.4) + min(0.2, (1.0 - data_consistency) * 0.2)
    score = max(0.0, min(1.0, 1.0 - penalty))

    issues: List[str] = []
    if empty_ratio > 0.45:
        issues.append("high_empty_value_ratio")
    if header_completeness < 0.5:
        issues.append("weak_header_quality")
    if data_consistency < 0.6:
        issues.append("row_data_inconsistency")

    return {
        "score": round(score, 4),
        "issues": sorted(set(issues)),
        "metrics": {
            "chunk_count": float(total_chunks),
            "avg_rows_per_chunk": round(total_rows / max(1, total_chunks), 4),
            "empty_value_ratio": round(empty_ratio, 4),
            "header_completeness": round(header_completeness, 4),
            "data_consistency": round(data_consistency, 4),
        },
    }
