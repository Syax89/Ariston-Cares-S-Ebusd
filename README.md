# Ariston Cares S — eBUS BridgeNet Configuration

Decode the eBUS BridgeNet protocol of Ariston Cares S (and compatible) boilers.

This repository provides a complete [ebusd](https://github.com/john30/ebusd) configuration for reading live boiler data via MQTT into Home Assistant — temperatures, setpoints, operating modes, diagnostics, and maintenance counters. Zone 2–6 registers are documented but commented (single-zone thermostat only).

## Quick Start

```bash
# Place the CSV files in your ebusd config path
ebusd --scanconfig=0 --configpath=/config/Ariston --device=ens:192.168.4.74:9999
```

`--scanconfig=0` prevents ebusd from preferring generic Ariston definitions over this file.

## What You Get

### 📊 Active sensors (Zone 1, published)
- **Boiler status**: operating mode, flame state, heating/DHW active
- **Temperatures**: flow, return, DHW, external, flame target, outdoor
- **Setpoints**: heating (primary/circuit/DHW), DHW, max heating, eco
- **Thermoregulation**: max/min water temp, slope, offset, room influence, antifreeze
- **Diagnostics**: pump modulation, pressure sensor, fan speed, settings counter
- **Maintenance counters**: burner hours (CH + DHW), pump hours, ignition/fan/diverter cycles, boiler lifetime
- **Cooling config**: setpoint, temp range, max/min water, slope, offset

### 🗂️ Documented but commented (Zones 2–6)
Complete register maps for zones 2–6 (`#` commented — not published). Covers day/night temp, thermoregulation curves, cooling params, summer/winter changeover, zone state.

## Protocol Notes

Ariston BridgeNet is a proprietary eBUS variant. The boiler broadcasts register values on PBSB 0x2010 while ebusd polls individual registers on PBSB 0x2000. The CSV uses shared templates from `_templates.csv` for boiler status enums, error codes, and thermoreg types.

## Repository Structure

| File | Purpose |
|---|---|
| `aris-development.csv` | Active ebusd configuration (dev branch) |
| `aris.csv` | Stable release version |
| `_templates.csv` | Shared field type templates (onoff, boiler_status, error_code, etc.) |
| `mqtt-hassio.cfg` | Home Assistant MQTT auto-discovery config |
| `tools/` | Analysis scripts: | | |
| `validate_ebusd_csv.py` | CSV format validator | |
| `audit_csv_against_captures.py` | Cross-check CSV against pcap dumps | |
| `build_evidence_matrix.py` | Build confidence matrix from logs + MQTT | |
| `parse_dump.py` | Parse raw eBUS packet captures | |
| `compare_dumps.py` | Compare register values across captures | |
| … | Many more reverse-engineering tools | |
| `json/` | Generated reports and analysis outputs |
| `logs/` | Runtime ebusd log archives |

## Files You Need

Only `aris-development.csv` and `_templates.csv` are required for ebusd. Add `mqtt-hassio.cfg` for automatic Home Assistant entity discovery.

## Validation

```bash
python3 tools/validate_ebusd_csv.py aris-development.csv
```

## License

MIT
