#!/usr/bin/env python3

import argparse
import json
import re
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path


LOG_RE = re.compile(
    r"^(?P<ts>\S+ \S+) \[(?P<kind>[^\]]+)\] (?P<msg>.*)$"
)
UPDATE_READ_RE = re.compile(r"received update-read aris (?P<name>[a-zA-Z0-9_]+): (?P<value>.+)$")
POLL_READ_RE = re.compile(r"sent poll-read aris (?P<name>[a-zA-Z0-9_]+): (?P<value>.+)$")
PARSE_ERR_RE = re.compile(
    r"(?:unable to parse (?:poll-read|update-read) aris|decode aris) (?P<name>[a-zA-Z0-9_]+).*(?:ERR: )(?P<error>.+)$"
)
UNKNOWN_CMD_RE = re.compile(r"received unknown BC cmd: (?P<frame>[0-9a-f]+)$")


@dataclass
class Evidence:
    name: str
    log_values: list[str] = field(default_factory=list)
    mqtt_values: list[str] = field(default_factory=list)
    log_timestamps: list[str] = field(default_factory=list)
    mqtt_timestamps: list[str] = field(default_factory=list)
    parse_failures: list[str] = field(default_factory=list)
    related_frames: list[str] = field(default_factory=list)
    sources: set[str] = field(default_factory=set)
    notes: list[str] = field(default_factory=list)
    mqtt_children: set[str] = field(default_factory=set)
    log_events: list[tuple[str, str]] = field(default_factory=list)
    mqtt_events: list[tuple[str, str]] = field(default_factory=list)

    def add_log_value(self, timestamp: str, value: str) -> None:
        self.sources.add("ebusd_log")
        self.log_timestamps.append(timestamp)
        self.log_events.append((timestamp, value))
        if value not in self.log_values:
            self.log_values.append(value)

    def add_mqtt_value(self, timestamp: str, value: str) -> None:
        self.sources.add("mqtt")
        self.mqtt_timestamps.append(timestamp)
        self.mqtt_events.append((timestamp, value))
        if value not in self.mqtt_values:
            self.mqtt_values.append(value)

    def add_failure(self, error: str) -> None:
        self.sources.add("ebusd_log")
        if error not in self.parse_failures:
            self.parse_failures.append(error)

    def add_frame(self, frame: str) -> None:
        self.sources.add("ebusd_log")
        if frame not in self.related_frames:
            self.related_frames.append(frame)


def normalize_payload(payload: str) -> str:
    payload = payload.strip()
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return payload
    if isinstance(data, dict):
        parts = []
        for key, value in data.items():
            if isinstance(value, dict) and "value" in value:
                parts.append(f"{key}={value['value']}")
            else:
                parts.append(f"{key}={value}")
        return "; ".join(parts)
    return str(data)


def derive_parent_name(name: str) -> str | None:
    bundle_suffixes = (
        "_base_setpoint",
        "_day_temp",
        "_night_temp",
        "_max_water_temp",
        "_min_water_temp",
        "_offset",
        "_param1_temp",
        "_param2_temp",
        "_slope",
        "_heating_request",
        "_zone_call_state",
        "_zone_status_code",
        "_primary_setpoint",
        "_circuit_setpoint",
        "_dhw_reference",
    )
    for suffix in bundle_suffixes:
        if name.endswith(suffix):
            return name[: -len(suffix)]
    if name.endswith("_val"):
        return name[: -4]
    return None


def temporal_consistency(entry: Evidence) -> str:
    values = entry.log_values + entry.mqtt_values
    if not values:
        return "unknown"
    unique = list(dict.fromkeys(values))
    if len(unique) == 1:
        return "stable"
    if len(unique) == 2:
        return "limited_variation"
    return "variable"


def recent_values(entry: Evidence, count: int = 3) -> list[str]:
    events = [(ts, value, "log") for ts, value in entry.log_events] + [
        (ts, value, "mqtt") for ts, value in entry.mqtt_events
    ]
    events = [item for item in events if item[0]]
    events.sort(key=lambda item: item[0])
    values = [value for _, value, _ in events[-count:]]
    return list(dict.fromkeys(values))


def recency_bias(entry: Evidence) -> str:
    values = recent_values(entry)
    if not values:
        return "unknown"
    if len(values) == 1:
        return "stable_recent"
    return "recently_variable"


def has_corrected_history(entry: Evidence) -> bool:
    if len(entry.log_values) < 2:
        return False
    return entry.log_values[-1] != entry.log_values[0]


def parse_logs(log_paths: list[Path], evidence: dict[str, Evidence]) -> None:
    last_unknown_frame = None
    for path in sorted(log_paths):
        for line in path.read_text().splitlines():
            match = LOG_RE.match(line)
            if not match:
                continue
            ts = match.group("ts")
            msg = match.group("msg")

            m = UNKNOWN_CMD_RE.search(msg)
            if m:
                last_unknown_frame = m.group("frame")
                continue

            m = UPDATE_READ_RE.search(msg)
            if m:
                name = m.group("name")
                entry = evidence.setdefault(name, Evidence(name=name))
                entry.add_log_value(ts, m.group("value"))
                if last_unknown_frame:
                    entry.add_frame(last_unknown_frame)
                continue

            m = POLL_READ_RE.search(msg)
            if m:
                name = m.group("name")
                entry = evidence.setdefault(name, Evidence(name=name))
                entry.sources.add("ebusd_log")
                if m.group("value") not in entry.log_values:
                    entry.log_values.append(m.group("value"))
                continue

            m = PARSE_ERR_RE.search(msg)
            if m:
                name = m.group("name")
                entry = evidence.setdefault(name, Evidence(name=name))
                entry.add_failure(m.group("error"))


def parse_mqtt_exports(json_paths: list[Path], evidence: dict[str, Evidence]) -> None:
    for path in sorted(json_paths):
        if path.name == "reverse_engineering_report.json":
            continue
        try:
            data = json.loads(path.read_text())
        except Exception:
            continue
        entities = data.get("data", {}).get("mqtt_debug_info", {}).get("entities", [])
        for entity in entities:
            entity_id = entity.get("entity_id", "")
            base = entity_id.split(".", 1)[-1]
            if base.startswith("ariston_cares_s_"):
                base = base[len("ariston_cares_s_") :]
            if base.startswith("ebusd_aris_"):
                base = base[len("ebusd_aris_") :]
            if not base:
                continue
            entry = evidence.setdefault(base, Evidence(name=base))
            for sub in entity.get("subscriptions", []):
                for message in sub.get("messages", []):
                    entry.add_mqtt_value(message.get("time", ""), normalize_payload(message.get("payload", "")))
            parent = derive_parent_name(base)
            if parent:
                parent_entry = evidence.setdefault(parent, Evidence(name=parent))
                parent_entry.sources.add("mqtt")
                parent_entry.mqtt_children.add(base)
                for sub in entity.get("subscriptions", []):
                    for message in sub.get("messages", []):
                        parent_entry.add_mqtt_value(message.get("time", ""), normalize_payload(message.get("payload", "")))


def add_dump_hints(report_path: Path, evidence: dict[str, Evidence]) -> None:
    if not report_path.exists():
        return
    report = json.loads(report_path.read_text())
    validated = report.get("validated_rows", {})
    for status_name in ("confirmed", "usable"):
        for name in validated.get(status_name, []):
            entry = evidence.setdefault(name, Evidence(name=name))
            entry.sources.add("dump_report")
            entry.notes.append(f"listed as {status_name} in reverse_engineering_report.json")


def classify(entry: Evidence) -> str:
    has_log_values = bool(entry.log_values)
    has_mqtt_values = bool(entry.mqtt_values)
    has_dump = "dump_report" in entry.sources
    has_failures = bool(entry.parse_failures)
    recent_stable = recency_bias(entry) == "stable_recent"

    if (has_log_values and has_mqtt_values) or (has_log_values and has_dump) or (has_mqtt_values and has_dump):
        if not has_failures:
            return "confirmed"
        if recent_stable:
            return "mixed"
    if has_log_values or has_mqtt_values:
        if has_failures:
            return "mixed"
        if has_corrected_history(entry) and recent_stable:
            return "confirmed"
        return "usable"
    if has_failures:
        return "broken"
    if has_dump:
        return "candidate"
    return "unknown"


def confidence(entry: Evidence) -> str:
    count = len(entry.log_values) + len(entry.mqtt_values)
    source_count = len(entry.sources)
    if classify(entry) == "broken":
        return "low"
    if source_count >= 3 or count >= 4:
        return "high"
    if source_count >= 2 or count >= 2:
        return "medium"
    return "low"


def build_matrix(root: Path) -> dict:
    evidence: dict[str, Evidence] = {}
    log_paths = list((root / "logs").glob("*.log")) + list(root.glob("*.log"))
    json_paths = list((root / "json").glob("*.json")) + list(root.glob("*.json"))
    parse_logs(log_paths, evidence)
    parse_mqtt_exports(json_paths, evidence)
    add_dump_hints(root / "json" / "reverse_engineering_report.json", evidence)

    rows = []
    for name in sorted(evidence):
        entry = evidence[name]
        rows.append(
            {
                "name": name,
                "status": classify(entry),
                "confidence": confidence(entry),
                "sources": sorted(entry.sources),
                "log_values": entry.log_values[:10],
                "mqtt_values": entry.mqtt_values[:10],
                "log_samples": len(entry.log_timestamps),
                "mqtt_samples": len(entry.mqtt_timestamps),
                "parse_failures": entry.parse_failures,
                "related_frames": entry.related_frames[:10],
                "mqtt_children": sorted(entry.mqtt_children),
                "temporal_consistency": temporal_consistency(entry),
                "recent_values": recent_values(entry),
                "recency_bias": recency_bias(entry),
                "has_corrected_history": has_corrected_history(entry),
                "notes": entry.notes,
            }
        )

    summary = defaultdict(int)
    for row in rows:
        summary[row["status"]] += 1

    return {
        "version": 1,
        "generated_from": {
            "logs": sorted(str(p.relative_to(root)) for p in log_paths if p.exists()),
            "json_exports": sorted(str(p.relative_to(root)) for p in json_paths if p.exists()),
        },
        "summary": dict(sorted(summary.items())),
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a cross-source evidence matrix from ebusd logs and MQTT exports")
    parser.add_argument("--root", default=Path(__file__).resolve().parents[1], type=Path)
    parser.add_argument("--output", default=None, type=Path)
    args = parser.parse_args()

    root = args.root.resolve()
    output = args.output or (root / "json" / "evidence_matrix.json")
    matrix = build_matrix(root)
    output.write_text(json.dumps(matrix, indent=2, sort_keys=False) + "\n")
    print(f"wrote {output}")
    print(json.dumps(matrix["summary"], indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
