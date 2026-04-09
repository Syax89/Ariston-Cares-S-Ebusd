# Ariston Cares S eBUS

This repository is used to reverse-engineer the eBUS protocol of an Ariston Cares S boiler and build a usable `ebusd` configuration.

The goal is simple:

- identify as many registers and bundles as possible
- give them names that match real behavior on the bus
- keep names conservative when the evidence is weak
- document what is confirmed and what is still uncertain

## Main Files

- `aris-development.csv`
  Current working `ebusd` config.

- `_templates.csv`
  Shared templates used by the config.

- `REGISTERS.md`
  Short register map with confidence notes and protocol observations.

- `Dump/`
  Packet captures used as ground truth.

- `json/`
  Generated reports, snapshots, and analysis outputs.

- `tools/`
  Small scripts used to parse dumps, compare captures, extract MQTT snapshots, and audit the CSV.

## What We Are Doing

We take real eBUS traffic and try to answer these questions:

- which register or bundle is this?
- is the current CSV name correct?
- does the value format make sense?
- is the same interpretation stable across multiple captures?

When a name is well supported, it is kept in the CSV.
When a name is only partly supported, it stays conservative.
When the meaning is still unclear, it stays documented as unresolved instead of being guessed.

## Workflow

The usual workflow in this repo is:

1. parse captures from `Dump/`
2. compare repeated frames and state changes
3. check the same register against logs, MQTT snapshots, and reference CSVs
4. update `aris-development.csv` only when the naming is justified
5. record open questions in the documentation or backlog files

## Useful Commands

Parse a dump against the current CSV:

```bash
python3 tools/parse_dump.py "Dump/dump3.pcapng" --csv aris-development.csv --summary-only
```

Compare two dumps:

```bash
python3 tools/compare_dumps.py "Dump/dump2.pcapng" "Dump/dump3.pcapng" --csv aris-development.csv
```

Extract a Home Assistant MQTT snapshot:

```bash
python3 tools/extract_mqtt_snapshot.py "mqtt-....json"
```

Audit the CSV against the captures we already have:

```bash
python3 tools/audit_csv_against_captures.py
```

## Using The CSV With ebusd

The active config in this repo is `aris-development.csv`.

If you want to test it with `ebusd`, place `aris-development.csv` and `_templates.csv` in your config path.

Example:

```bash
ebusd --scanconfig=0 --configpath=/config/Ariston --device=ens:192.168.4.74:9999
```

`--scanconfig=0` is recommended so `ebusd` does not prefer generic Ariston definitions over this repository's file.

## Notes

- The CSV is intentionally conservative.
- Not every row is fully confirmed yet.
- Reference CSVs are useful, but local captures always have priority.
- If a value is still uncertain, it is better to keep a neutral name than a wrong name.

## License

MIT
