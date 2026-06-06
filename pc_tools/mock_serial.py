"""
mock_serial.py — Fake UART telemetry stream for VTFD project
Generates output in the same format Node 2 sends over UART:
    T,<timestamp_ms>,<can_id_hex>,<val1_raw>,<val2_raw>,<fault_hex>

Usage:
    python mock_serial.py              # print to stdout
    python mock_serial.py | python telemetry_monitor.py --mock

Pipe directly into telemetry_monitor.py for offline visualization.
"""

import time
import math
import random
import sys

# ── Conversion constants (must match thresholds.h) ───────────────────────────
ADC_FULLSCALE   = 4095.0
ADC_VREF        = 3.3

THRESH_TEMP_RAW = 744    # 60°C → raw ADC count
THRESH_VOLT_MIN = 1860   # 3.0V
THRESH_VOLT_MAX = 2604   # 4.2V
THRESH_CURR_MAX = 3779   # 5.0A

FAULT_TEMP_HIGH = 0x01
FAULT_VOLT_LOW  = 0x02
FAULT_VOLT_HIGH = 0x04
FAULT_CURR_HIGH = 0x08

# ── Simulation parameters ─────────────────────────────────────────────────────
TICK_MS      = 100     # one frame pair every 100 ms → 10 Hz
TEMP_BASE    = 500     # ~40°C baseline raw
TEMP_AMP     = 320     # swings ±320 raw — crosses 744 (60°C) at peak
VOLT_BASE    = 2300    # ~3.7V nominal raw
VOLT_DRIFT   = 200     # slow drift amplitude
CURR_BASE    = 1800    # ~2A baseline raw
CURR_NOISE   = 150     # random noise amplitude

def fault_flags(temp, volt, curr):
    flags = 0
    if temp > THRESH_TEMP_RAW:   flags |= FAULT_TEMP_HIGH
    if volt < THRESH_VOLT_MIN:   flags |= FAULT_VOLT_LOW
    if volt > THRESH_VOLT_MAX:   flags |= FAULT_VOLT_HIGH
    if curr > THRESH_CURR_MAX:   flags |= FAULT_CURR_HIGH
    return flags

def run():
    t_ms   = 0
    phase  = 0.0   # radians, advances each tick

    try:
        while True:
            # ── Simulate raw ADC values ───────────────────────────────────
            temp_raw = int(TEMP_BASE + TEMP_AMP * math.sin(phase))
            volt_raw = int(VOLT_BASE + VOLT_DRIFT * math.sin(phase * 0.3))
            curr_raw = int(CURR_BASE + CURR_NOISE * (random.random() - 0.5) * 2)

            # clamp to ADC range
            temp_raw = max(0, min(4095, temp_raw))
            volt_raw = max(0, min(4095, volt_raw))
            curr_raw = max(0, min(4095, curr_raw))

            flags = fault_flags(temp_raw, volt_raw, curr_raw)

            # ── Emit 0x100 frame (temp + volt) ───────────────────────────
            print(f"T,{t_ms:06d},0x100,{temp_raw},{volt_raw},0x{flags:02X}",
                  flush=True)
            t_ms += TICK_MS // 2

            # ── Emit 0x101 frame (current) ────────────────────────────────
            print(f"T,{t_ms:06d},0x101,{curr_raw},0,0x{flags:02X}",
                  flush=True)
            t_ms += TICK_MS // 2

            phase += 0.05   # full sine cycle every ~125 frames (~12.5 s)

            time.sleep(TICK_MS / 1000.0)

    except KeyboardInterrupt:
        sys.exit(0)

if __name__ == "__main__":
    run()
