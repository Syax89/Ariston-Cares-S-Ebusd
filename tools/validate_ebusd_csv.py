#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
LOWER_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def looks_hex(value: str, allowed_lengths: set[int] | None = None) -> bool:
    if not value:
        return True
    if not HEX_RE.fullmatch(value):
        return False
    if allowed_lengths is None:
        return True
    return len(value) in allowed_lengths


def load_csv_rows(path: Path) -> list[list[str]]:
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.reader(handle))


def validate_template_row(line_no: int, row: list[str]) -> list[str]:
    errors: list[str] = []

    if not row or row[0].strip().startswith("#"):
        return errors

    if not any(item.strip() for item in row):
        return errors

    if len(row) != 5:
        errors.append(f"_templates.csv:{line_no}: expected 5 columns, found {len(row)}")
        return errors

    name, field_type, values, _unit, _comment = [item.strip() for item in row]
    if not LOWER_NAME_RE.fullmatch(name):
        errors.append(f"_templates.csv:{line_no}: suspicious template name '{name}'")
    if not field_type:
        errors.append(f"_templates.csv:{line_no}: missing field type")
    if not values:
        errors.append(f"_templates.csv:{line_no}: missing values map")

    return errors


def collect_template_names(rows: list[list[str]]) -> set[str]:
    names: set[str] = set()
    for row in rows:
        if not row or row[0].strip().startswith("#"):
            continue
        if not any(item.strip() for item in row):
            continue
        if row:
            name = row[0].strip()
            if name:
                names.add(name)
    return names


def validate_row(line_no: int, row: list[str], template_names: set[str]) -> list[str]:
    errors: list[str] = []

    if not row or row[0].strip().startswith("#"):
        return errors

    if not any(item.strip() for item in row):
        return errors

    if len(row) < 8:
        errors.append(f"line {line_no}: too few columns ({len(row)})")
        return errors

    row_type, circuit, name, comment, qq, zz, pbsb, ident = [item.strip() for item in row[:8]]

    if not row_type:
        errors.append(f"line {line_no}: missing type")
    if not circuit:
        errors.append(f"line {line_no}: missing circuit")
    if not name:
        errors.append(f"line {line_no}: missing name")
    if not looks_hex(qq, {2}):
        errors.append(f"line {line_no}: suspicious QQ '{qq}'")
    if not looks_hex(zz, {2}):
        errors.append(f"line {line_no}: suspicious ZZ '{zz}'")
    if not looks_hex(pbsb, {4, 6}):
        errors.append(f"line {line_no}: suspicious PBSB '{pbsb}'")
    if ident and not looks_hex(ident):
        errors.append(f"line {line_no}: suspicious ID '{ident}' (possible shifted columns)")

    for field_index in range(10, len(row), 6):
        field_type = row[field_index].strip()
        if not field_type:
            continue
        if LOWER_NAME_RE.fullmatch(field_type) and field_type not in template_names:
            errors.append(f"line {line_no}: unknown template '{field_type}' in field type column")

    return errors


def dump_row(line_no: int, row: list[str]) -> None:
    print(f"line {line_no}: {len(row)} columns")
    for index, value in enumerate(row, start=1):
        print(f"  {index:02d}: {value!r}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Lightweight sanity checker for ebusd CSV rows")
    parser.add_argument("csv_path", nargs="?", default="aris-development.csv")
    parser.add_argument("--show-line", type=int, action="append", default=[], help="print indexed columns for a line")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    csv_path = Path(args.csv_path)
    if not csv_path.is_absolute():
        csv_path = root / csv_path

    rows = load_csv_rows(csv_path)
    templates_path = csv_path.parent / "_templates.csv"
    template_rows = load_csv_rows(templates_path) if templates_path.exists() else []
    template_names = collect_template_names(template_rows)

    for line_no in args.show_line:
        if 1 <= line_no <= len(rows):
            dump_row(line_no, rows[line_no - 1])
        else:
            print(f"line {line_no}: out of range")

    all_errors: list[str] = []
    for line_no, row in enumerate(template_rows, start=1):
        all_errors.extend(validate_template_row(line_no, row))

    ids: dict[tuple[str, str, str, str], list[tuple[int, str, str]]] = {}
    for line_no, row in enumerate(rows, start=1):
        all_errors.extend(validate_row(line_no, row, template_names))
        if not row or row[0].strip().startswith("#") or len(row) < 8:
            continue
        if not any(item.strip() for item in row):
            continue
        key = tuple(item.strip() for item in row[4:8])
        ids.setdefault(key, []).append((line_no, row[1].strip(), row[2].strip()))

    for key, occurrences in sorted(ids.items()):
        if len(occurrences) < 2:
            continue
        qq, zz, pbsb, ident = key
        labels = ", ".join(f"line {line_no} {circuit}.{name}" for line_no, circuit, name in occurrences)
        all_errors.append(
            f"duplicate id {qq},{zz},{pbsb},{ident}: {labels}"
        )

    if all_errors:
        for error in all_errors:
            print(error)
        print(f"\nfound {len(all_errors)} likely issue(s) in {csv_path}")
        return 1

    if templates_path.exists():
        print(f"ok: {csv_path} (+ {templates_path.name})")
    else:
        print(f"ok: {csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
