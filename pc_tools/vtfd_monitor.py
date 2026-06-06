"""
vtfd_monitor.py — VTFD Live Telemetry Plot
Uses FuncAnimation (correct pattern for live matplotlib plots).

Usage:
    python3 vtfd_monitor.py              # auto-launches mock_serial.py
    python3 vtfd_monitor.py --port /dev/ttyACM0   # real hardware
"""

import argparse, sys, csv, threading, subprocess, queue
from collections import deque
from datetime import datetime

import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# ── Conversions ───────────────────────────────────────────────────────────────
def to_temp(r):  return (r / 4095.0) * 3.3 * 100.0
def to_volt(r):  return (r / 4095.0) * 3.3 * 2.0
def to_curr(r):  return ((r / 4095.0) * 3.3 - 2.5) / 0.185

FAULT_NAMES = {0x01:"TEMP HIGH", 0x02:"VOLT LOW", 0x04:"VOLT HIGH", 0x08:"CURR HIGH"}

# ── Buffers ───────────────────────────────────────────────────────────────────
N = 150
xs    = deque(maxlen=N)
temps = deque(maxlen=N)
volts = deque(maxlen=N)
currs = deque(maxlen=N)
faults= deque(maxlen=N)
lq    = queue.Queue()

last = {"temp":0.0, "volt":0.0, "curr":0.0, "fault":0, "count":0}

# ── CSV ───────────────────────────────────────────────────────────────────────
logname = f"vtfd_{datetime.now().strftime('%H%M%S')}.csv"
logf    = open(logname, "w", newline="")
logw    = csv.writer(logf)
logw.writerow(["ts_ms","id","temp_c","volt_v","curr_a","fault"])

# ── Source reader thread ──────────────────────────────────────────────────────
def read_source(src):
    while True:
        try:
            line = src.readline()
            if not line: break
            if isinstance(line, bytes):
                line = line.decode("utf-8", errors="ignore")
            lq.put(line.strip())
        except Exception:
            break

# ── Parse + buffer update (called from animation) ─────────────────────────────
def drain_queue():
    while not lq.empty():
        line = lq.get_nowait()
        if not line.startswith("T,"): continue
        p = line.split(",")
        if len(p) != 6: continue
        try:
            ts    = int(p[1])
            cid   = int(p[2], 16)
            v1    = int(p[3])
            v2    = int(p[4])
            flags = int(p[5], 16)
        except ValueError:
            continue

        last["fault"] = flags
        last["count"] += 1

        if cid == 0x100:
            last["temp"] = to_temp(v1)
            last["volt"] = to_volt(v2)
            logw.writerow([ts, hex(cid),
                f"{last['temp']:.2f}", f"{last['volt']:.3f}",
                f"{last['curr']:.3f}", hex(flags)])
            logf.flush()
        elif cid == 0x101:
            last["curr"] = to_curr(v1)

        xs.append(ts / 1000.0)
        temps.append(last["temp"])
        volts.append(last["volt"])
        currs.append(last["curr"])
        faults.append(flags)

# ── Build figure ──────────────────────────────────────────────────────────────
fig, (ax_t, ax_v, ax_c) = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
fig.suptitle("VTFD — CAN Bus Telemetry Monitor", fontsize=13,
             fontweight="bold", color="#1A3A5C")
fig.patch.set_facecolor("#F4F6F8")

for ax in (ax_t, ax_v, ax_c):
    ax.set_facecolor("#FFFFFF")
    ax.grid(True, alpha=0.3, linestyle="--")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

ax_t.set_ylabel("Temperature (°C)", fontsize=10)
ax_t.axhline(60.0, color="#C0392B", lw=1, ls="--", alpha=0.7, label="Max 60°C")
ax_t.legend(fontsize=8, loc="upper right")

ax_v.set_ylabel("Voltage (V)", fontsize=10)
ax_v.axhline(4.2, color="#C0392B", lw=1, ls="--", alpha=0.7, label="Max 4.2V")
ax_v.axhline(3.0, color="#E67E22", lw=1, ls="--", alpha=0.7, label="Min 3.0V")
ax_v.legend(fontsize=8, loc="upper right")

ax_c.set_ylabel("Current (A)", fontsize=10)
ax_c.set_xlabel("Time (s)", fontsize=10)
ax_c.axhline(5.0, color="#C0392B", lw=1, ls="--", alpha=0.7, label="Max 5.0A")
ax_c.legend(fontsize=8, loc="upper right")

lt, = ax_t.plot([], [], color="#2E6DA4", lw=1.5)
lv, = ax_v.plot([], [], color="#1E8449", lw=1.5)
lc, = ax_c.plot([], [], color="#8E44AD", lw=1.5)

plt.tight_layout(rect=[0, 0.04, 1, 1])
status_ax = fig.add_axes([0.05, 0.005, 0.9, 0.03])
status_ax.axis("off")
status_txt = status_ax.text(0.5, 0.5, f"Starting... log: {logname}",
    ha="center", va="center", fontsize=9, transform=status_ax.transAxes)

# ── Animation callback ────────────────────────────────────────────────────────
def animate(_):
    drain_queue()
    if len(xs) < 2:
        return lt, lv, lc, status_txt

    xlist = list(xs)
    tlist = list(temps)
    vlist = list(volts)
    clist = list(currs)
    flist = list(faults)
    flags = last["fault"]
    count = last["count"]

    lt.set_data(xlist, tlist)
    lv.set_data(xlist, vlist)
    lc.set_data(xlist, clist)

    for ax, data in zip((ax_t, ax_v, ax_c), (tlist, vlist, clist)):
        ax.set_xlim(xlist[0], max(xlist[-1], xlist[0] + 5))
        span = max(data) - min(data)
        margin = span * 0.2 + 0.5
        ax.set_ylim(min(data) - margin, max(data) + margin)
        for coll in ax.collections[:]:
            coll.remove()
        for i in range(1, len(xlist)):
            if flist[i]:
                ax.axvspan(xlist[i-1], xlist[i],
                           alpha=0.15, color="#C0392B", lw=0)

    if flags:
        names = ", ".join(n for b, n in FAULT_NAMES.items() if flags & b)
        status_txt.set_text(f"⚠  FAULT: {names}  |  frames: {count}  |  {logname}")
        status_txt.set_color("#C0392B")
    else:
        status_txt.set_text(f"✓  Nominal  |  frames: {count}  |  {logname}")
        status_txt.set_color("#1E8449")

    return lt, lv, lc, status_txt

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", default=None, help="Serial port e.g. /dev/ttyACM0")
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    if args.port:
        import serial
        src = serial.Serial(args.port, args.baud, timeout=1)
        print(f"Opened {args.port} at {args.baud} baud.")
    else:
        proc = subprocess.Popen(
            [sys.executable, "mock_serial.py"],
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        src = proc.stdout
        print("Launched mock_serial.py.")

    t = threading.Thread(target=read_source, args=(src,), daemon=True)
    t.start()

    ani = animation.FuncAnimation(
        fig, animate, interval=100, blit=False, cache_frame_data=False)

    print(f"Logging to {logname} — close window to stop.")
    plt.show()
    logf.close()

if __name__ == "__main__":
    main()
