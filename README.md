# Ariston Cares S — eBUS BridgeNet Configuration

Decode the eBUS BridgeNet protocol of Ariston Cares S (and compatible) boilers.

This repository provides a complete [ebusd](https://github.com/john30/ebusd) configuration for reading live boiler data via MQTT into Home Assistant — temperatures, setpoints, operating modes, diagnostics, and maintenance counters. Zone 2–6 registers are documented but commented (single-zone thermostat only).

## ⚠️ Important: My Setup (Parallel to Thermostat)

This configuration was developed and tested on a system where eBUSd is connected **in parallel** to the original **Ariston thermostat (address 0x70)**.

### How it works

The thermostat is the primary bus master and continuously polls registers like:
- `flame_active` (0e11)
- `boiler_status` (c04b)  
- zone temperatures and setpoints
- heating/DHW requests

eBUSd **intercepts these responses passively** — it doesn't need to request them. This is why seeing `poll: 0` in eBUSd status is normal for `b,` (broadcast) messages — they're already on the bus!

However, `r,` (direct read) registers like `hours_burner_on_CH`, `boiler_pressure`, etc. are **NOT** requested by the thermostat. To read these, eBUSd needs to actively poll them.

### Configuration

**With v2.7.1+**, the `mqtt-hassio.cfg` has `filter-seen = 5` which **automatically enables polling** for all `r,` registers with priority ≤ 5. No extra steps needed — just use the provided files.

### If you DON'T have the thermostat

Without the thermostat (0x70), **nobody triggers the broadcast messages** that eBUSd intercepts. You still need:

1. **`filter-seen = 5`** in `mqtt-hassio.cfg` (default in v2.7.1+) — enables auto-polling
2. **`--pollinterval=10`** — poll every 10 seconds  
3. **`ens:` device prefix** — `ens:192.168.4.74:9999` (mandatory for ESP32 rev2)

### ⚠️ Known issue: boiler reset during heavy polling

If you force-read many registers (`-f` flag) while the boiler is actively burning (DHW/heating), the bus traffic may cause the boiler to interpret a communication error as a fault and **restart** itself. This is rare but observed during development. Normal operation with `filter-seen = 5` and `pollinterval=10` should NOT trigger this.

## Quick Start

```bash
# Place aris.csv in your ebusd config path (only one .csv per circuit!)
# Device: use ens: prefix for ESP32 rev2 with eBUS Adapter Shield
ebusd --device=ens:192.168.4.74:9999 --configpath=/config/Ariston/ --pollinterval=10
```

- `--device=ens:...` → **mandatory** for ESP32 rev2 (plain TCP fails with arbitration errors)
- Only **one** .csv file per circuit — keep just `aris.csv`, delete any duplicates
- `--pollinterval=10` → poll direct read registers every 10 seconds

## What You Get

### 📊 Active sensors (Zone 1, published)
- **Boiler status**: operating mode, flame state, heating/DHW active
- **Temperatures**: flow, return, DHW, external, flame target, outdoor, room
- **Setpoints**: heating (primary/circuit/DHW), DHW, max heating, eco, comfort
- **Thermoregulation**: max/min water temp, slope, offset, room influence, antifreeze
- **Diagnostics**: pump modulation, gas modulation (0 in standby), pressure sensor, fan speed, settings counter
- **Maintenance counters**: burner hours CH + DHW, pump hours, ignition/fan/diverter cycles, boiler lifetime
- **Power**: nominal power (24kW), flame power kW (0 in standby — Cares S doesn't report live kW)

### 🗂️ Documented but commented (Zones 2–6)
Complete register maps for zones 2–6 (`#` commented — not published). Covers day/night temp, thermoregulation curves, cooling params, summer/winter changeover, zone state.

## Known Limitations (Cares S)

| Register | Behavior |
|---|---|
| `flame_power_kw` (6847) | Always 0 — Cares S **does not report** instantaneous kW via eBUS |
| `boiler_gas_modulation` (c404) | 0 in standby, but may show values when burning (not verified) |
| `boiler_pressure` (7547) | 0 in standby, shows real pressure when circulating |
| `fan_speed` (4013) | 0 in standby, shows RPM when burning |
| `pump_current_modulation` (c300) | ERR: invalid position — CSV format needs fixing |

Use `hours_burner_on_CH` + `nominal_power` (24 kW) to estimate average consumption over time.

## Repository Structure

| File | Purpose |
|---|---|
| `aris.csv` | **Single active ebusd config** (rename from aris-development.csv) |
| `_templates.csv` | Shared field type templates (onoff, boiler_status, error_code, etc.) |
| `mqtt-hassio.cfg` | Home Assistant MQTT auto-discovery config (v2.7.1+: filter-seen=5) |
| `tools/` | Analysis, validation, and reverse-engineering scripts |
| `json/` | Generated reports and analysis outputs |
| `logs/` | Runtime ebusd log archives |

## Files You Need

Only `aris.csv` and `_templates.csv` are required for ebusd.
Add `mqtt-hassio.cfg` for automatic Home Assistant entity discovery via MQTT.

**Important**: eBUSd loads ALL `.csv` files in the config directory. Having both `aris.csv` AND `aris-development.csv` causes "duplicate ID" errors. Keep only `aris.csv`.

## Validation

```bash
python3 tools/validate_ebusd_csv.py aris.csv
```

## Protocol Notes

Ariston BridgeNet is a proprietary eBUS variant. The boiler broadcasts register values on PBSB 0x2010 while ebusd polls individual registers on PBSB 0x2000. The CSV uses shared templates from `_templates.csv` for boiler status enums, error codes, and thermoreg types.

The ESP32 with eBUS Adapter Shield rev2 firmware requires the **`ens:`** (enhanced) device prefix:
- ✅ `ens:192.168.4.74:9999` — works perfectly (88 messages, 43 updates)
- ❌ `192.168.4.74:9999` — fails with CRC/arbitration errors

## License

MIT
