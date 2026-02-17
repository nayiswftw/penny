"""CSV export utilities."""

from __future__ import annotations

import csv
import io
import os

from penny.exceptions import ExportError


def export_to_csv(data_dict: dict | list, filename: str | None = None) -> str:
    """Serialize a flat dict (or list-of-dicts) to CSV text.

    Returns the CSV content as a string. If *filename* is provided the
    content is also written to disk.

    Raises
    ------
    ExportError
        If writing to disk fails.
    """
    buf = io.StringIO()

    if isinstance(data_dict, list):
        if not data_dict:
            return ""
        writer = csv.DictWriter(buf, fieldnames=data_dict[0].keys())
        writer.writeheader()
        writer.writerows(data_dict)
    else:
        writer = csv.writer(buf)  # type: ignore[assignment]
        writer.writerow(["Metric", "Value"])
        for k, v in data_dict.items():
            writer.writerow([k, v])

    content = buf.getvalue()

    if filename:
        try:
            os.makedirs(os.path.dirname(filename) or ".", exist_ok=True)
            with open(filename, "w", newline="", encoding="utf-8") as f:
                f.write(content)
        except OSError as exc:
            raise ExportError(f"Failed to write CSV to {filename}: {exc}") from exc

    return content
