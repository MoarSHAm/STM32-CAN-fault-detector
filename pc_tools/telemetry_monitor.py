"""
telemetry_monitor.py — VTFD Real-Time Telemetry Visualization
Reads UART stream from Node 2 (or mock_serial.py) and plots live.

Wire format:
    T,<timestamp_ms>,<can_id_hex>,<val1_raw>,<val2_raw>,<fault_hex>

Usage:
    # Real hardware (Node 2 over USB-UART):
    python telemetry_monitor.py --port /dev/ttyACM0

    # Offline with mock data (pipe mode):
    python mock_serial.py | python telemetry_monitor.py --mock

    # Offline with mock data (auto-launch mock internally):
    python telemetry_monitor.py --mock --launch-mock
"""

import argparse
import sys
import time
import csv
import threading
import subprocess
import math
from collections import deque
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# ── Conversion to engineering units ──────────────────────────────────────────
def raw_to_temp_c(raw):
    return (raw / 4095.0) * 3.3 * 100.0          # LM35: 10 mV/°C

def raw_to_volt_v(raw):
    return (raw / 4095.0) * 3.3 * 2.0            # voltage divider ratio 2.0

def raw_to_curr_a(raw):
    v = (raw / 4095.0) * 3.3
    return (v - 2.5) / 0.185                      # ACS712-5A: 2.5V zero, 185mV/A

# ── Fault bitmasks ────────────────────────────────────────────────────────────
FAULT_TEMP_HIGH = 0x01
FAULT_VOLT_LOW  = 0x02
FAULT_VOLT_HIGH = 0x04
FAULT_CURR_HIGH = 0x08

FAULT_LABELS = {
    FAULT_TEMP_HIGH: "TEMP HIGH",
    FAULT_VOLT_LOW:  "VOLT LOW",
    FAULT_VOLT_HIGH: "VOLT HIGH",
    FAULT_CURR_HIGH: "CURR HIGH",
}

# ── Plot config ───────────────────────────────────────────────────────────────
WINDOW      = 200      # number of samples shown in rolling window
UPDATE_MS   = 100      # plot refresh interval

# ── Shared state (written by reader thread, read by plot thread) ──────────────
lock        = threading.Lock()
ts_buf      = deque(maxlen=WINDOW)
temp_buf    = deque(maxlen=WINDOW)
volt_buf    = deque(maxlen=WINDOW)
curr_buf    = deque(maxlen=WINDOW)
fault_buf   = deque(maxlen=WINDOW)
latest_fault = 0
line_count   = 0

# ── CSV logger ────────────────────────────────────────────────────────────────
csv_filename = f"vtfd_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
csv_file     = open(csv_filename, "w", newline="")
csv_writer   = csv.writer(csv_file)
csv_writer.writerow(["timestamp_ms", "can_id", "temp_c", "volt_v", "curr_a", "fault_flags"])

# ── Persistent state across frames ───────────────────────────────────────────
last_temp_c = 0.0
last_volt_v = 0.0
last_curr_a = 0.0

def parse_line(line):
    """Parse one UART line. Returns (timestamp_ms, can_id, v1, v2, flags) or None."""
    line = line.strip()
    if not line.startswith("T,"):
        return None
    parts = line.split(",")
    if len(parts) != 6:
        return None
    try:
        ts    = int(parts[1])
        cid   = int(parts[2], 16)
        v1    = int(parts[3])
        v2    = int(parts[4])
        flags = int(parts[5], 16)
        return ts, cid, v1, v2, flags
    except ValueError:
        return None

def reader_thread(source):
    """Reads lines from source (file-like), parses, updates shared buffers."""
    global last_temp_c, last_volt_v, last_curr_a, latest_fault, line_count

    for raw_line in source:
        if isinstance(raw_line, bytes):
            raw_line = raw_line.decode("utf-8", errors="ignore")

        result = parse_line(raw_line)
        if result is None:
            continue

        ts, cid, v1, v2, flags = result

        with lock:
            latest_fault = flags

            if cid == 0x100:
                last_temp_c = raw_to_temp_c(v1)
                last_volt_v = raw_to_volt_v(v2)
            elif cid == 0x101:
                last_curr_a = raw_to_curr_a(v1)

            ts_buf.append(ts / 1000.0)      # convert ms → seconds
            temp_buf.append(last_temp_c)
            volt_buf.append(last_volt_v)
            curr_buf.append(last_curr_a)
            fault_buf.append(flags)
            line_count += 1

            # CSV: write one row per 0x100 frame (has temp + volt)
            if cid == 0x100:
                csv_writer.writerow([ts, hex(cid),
                                     f"{last_temp_c:.2f}",
                                     f"{last_volt_v:.3f}",
                                     f"{last_curr_a:.3f}",
                                     hex(flags)])
                csv_file.flush()

def active_fault_labels(flags):
    return [label for bit, label in FAULT_LABELS.items() if flags & bit]

def setup_plot():
    fig, (ax_temp, ax_volt, ax_curr) = plt.subplots(3, 1, figsize=(12, 8),
                                                      sharex=True)
    fig.suptitle("VTFD — CAN Bus Telemetry Monitor", fontsize=14,
                 fontweight="bold", color="#1A3A5C")
    fig.patch.set_facecolor("#F8F9FA")

    for ax in (ax_temp, ax_volt, ax_curr):
        ax.set_facecolor("#FFFFFF")
        ax.grid(True, alpha=0.3, linestyle="--")
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    ax_temp.set_ylabel("Temperature (°C)", fontsize=10)
    ax_temp.axhline(60.0, color="#C0392B", linewidth=1, linestyle="--",
                    alpha=0.6, label="Max 60°C")
    ax_temp.legend(fontsize=8, loc="upper right")

    ax_volt.set_ylabel("Voltage (V)", fontsize=10)
    ax_volt.axhline(4.2, color="#C0392B", linewidth=1, linestyle="--",
                    alpha=0.6, label="Max 4.2V")
    ax_volt.axhline(3.0, color="#E67E22", linewidth=1, linestyle="--",
                    alpha=0.6, label="Min 3.0V")
    ax_volt.legend(fontsize=8, loc="upper right")

    ax_curr.set_ylabel("Current (A)", fontsize=10)
    ax_curr.set_xlabel("Time (s)", fontsize=10)
    ax_curr.axhline(5.0, color="#C0392B", linewidth=1, linestyle="--",
                    alpha=0.6, label="Max 5.0A")
    ax_curr.legend(fontsize=8, loc="upper right")

    line_temp, = ax_temp.plot([], [], color="#2E6DA4", linewidth=1.5)
    line_volt, = ax_volt.plot([], [], color="#1E8449", linewidth=1.5)
    line_curr, = ax_curr.plot([], [], color="#8E44AD", linewidth=1.5)

    # Status bar at bottom
    status_ax = fig.add_axes([0.1, 0.01, 0.8, 0.03])
    status_ax.axis("off")
    status_text = status_ax.text(0.5, 0.5, "Waiting for data...",
                                  ha="center", va="center",
                                  fontsize=9, transform=status_ax.transAxes)

    plt.tight_layout(rect=[0, 0.04, 1, 1])

    return fig, (ax_temp, ax_volt, ax_curr), \
           (line_temp, line_volt, line_curr), status_text

def update_plot(fig, axes, lines, status_text):
    ax_temp, ax_volt, ax_curr = axes
    line_temp, line_volt, line_curr = lines

    with lock:
        if len(ts_buf) < 2:
            return
        xs    = list(ts_buf)
        temps = list(temp_buf)
        volts = list(volt_buf)
        currs = list(curr_buf)
        faults = list(fault_buf)
        flags  = latest_fault
        count  = line_count

    line_temp.set_data(xs, temps)
    line_volt.set_data(xs, volts)
    line_curr.set_data(xs, currs)

    for ax, data in zip(axes, [temps, volts, currs]):
        ax.set_xlim(xs[0], max(xs[-1], xs[0] + 5))
        margin = (max(data) - min(data)) * 0.15 + 0.5
        ax.set_ylim(min(data) - margin, max(data) + margin)

        # red background spans where fault is active
        ax.collections.clear()
        for i in range(1, len(xs)):
            if faults[i]:
                ax.axvspan(xs[i-1], xs[i], alpha=0.15, color="#C0392B",
                           linewidth=0)

    # Status bar
    if flags:
        labels = ", ".join(active_fault_labels(flags))
        status_text.set_text(f"⚠ FAULT ACTIVE: {labels}  |  frames: {count}  |  log: {csv_filename}")
        status_text.set_color("#C0392B")
    else:
        status_text.set_text(f"✓ System nominal  |  frames: {count}  |  log: {csv_filename}")
        status_text.set_color("#1E8449")

    fig.canvas.draw_idle()

def main():
    parser = argparse.ArgumentParser(description="VTFD Telemetry Monitor")
    parser.add_argument("--port",        default=None,
                        help="Serial port e.g. /dev/ttyACM0 or COM3")
    parser.add_argument("--baud",        type=int, default=115200)
    parser.add_argument("--mock",        action="store_true",
                        help="Read from stdin (pipe from mock_serial.py)")
    parser.add_argument("--launch-mock", action="store_true",
                        help="Auto-launch mock_serial.py internally")
    args = parser.parse_args()

    # ── Open data source ──────────────────────────────────────────────────
    if args.launch_mock:
        proc = subprocess.Popen(
            [sys.executable, "mock_serial.py"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        source = proc.stdout
        print("Launched mock_serial.py internally.")
    elif args.mock:
        source = sys.stdin
        print("Reading from stdin (pipe mode).")
    elif args.port:
        import serial
        ser = serial.Serial(args.port, args.baud, timeout=1)
        source = ser
        print(f"Opened {args.port} at {args.baud} baud.")
    else:
        # Auto-launch mock if no port given
        proc = subprocess.Popen(
            [sys.executable, "mock_serial.py"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL
        )
        source = proc.stdout
        print("No port specified — launching mock_serial.py.")

    # ── Start reader thread ───────────────────────────────────────────────
    t = threading.Thread(target=reader_thread, args=(source,), daemon=True)
    t.start()

    # ── Build plot ────────────────────────────────────────────────────────
    fig, axes, lines, status_text = setup_plot()

    def on_timer():
        update_plot(fig, axes, lines, status_text)

    timer = fig.canvas.new_timer(interval=UPDATE_MS)
    timer.add_callback(on_timer)
    timer.start()

    print(f"Logging to {csv_filename}")
    print("Close the plot window to stop.")
    plt.show()

    csv_file.close()

if __name__ == "__main__":
    main()
