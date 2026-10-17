#!/usr/bin/env python3
"""F5 — đọc các dòng F5,... từ kit và so SÁT TỪNG DÒNG với log của Verilator.

Tiêu chí ĐẠT của cổng F5 (docs/FEASIBILITY_PLAN.md):
  - kit in được "F5,hello,<git hash>"
  - "F5,loop" trên kit BẰNG TUYỆT ĐỐI giá trị trong Verilator

Script so mọi khoá mà cả hai bên đều có. Các khoá phụ thuộc thời điểm đo
(F5,cycle) được bỏ qua vì chúng đo từ lúc reset và không nhất thiết trùng nhau.

Có xả bộ đệm trước khi đọc (driver macOS giữ dữ liệu của bitstream cũ — gặp ở F3).
Mã thoát 0 = ĐẠT.
"""
from __future__ import annotations

import argparse
import glob
import re
import sys
import time
from pathlib import Path

import serial

# khoá bỏ qua khi so: giá trị phụ thuộc thời điểm đọc
SKIP = {"cycle"}
LINE_RE = re.compile(r"^F5,([a-z]+),?(.*)$")


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def parse_block(lines):
    """Lấy một khối đầy đủ (từ F5,hello tới F5,done) thành dict."""
    out = {}
    started = False
    for ln in lines:
        m = LINE_RE.match(ln.strip())
        if not m:
            continue
        key, val = m.group(1), m.group(2)
        if key == "hello":
            started = True
            out = {}
        if not started:
            continue
        out[key] = val
        if key == "done":
            return out
    return out if "done" in out else {}


def read_kit(port, args, say):
    try:
        ser = serial.Serial(port, args.baud, timeout=0.2)
    except Exception as exc:  # noqa: BLE001
        say(f"    không mở được: {type(exc).__name__}: {exc}")
        return None, []
    try:
        time.sleep(0.1)
        ser.reset_input_buffer()
        t_drain = time.time()
        dropped = 0
        while time.time() - t_drain < args.drain:
            dropped += len(ser.read(512))
        if dropped:
            say(f"    (xả {dropped} byte tồn trong bộ đệm)")

        buf = b""
        lines = []
        t0 = time.time()
        while time.time() - t0 < args.timeout:
            chunk = ser.read(256)
            if chunk:
                buf += chunk
                while b"\r\n" in buf:
                    ln, _, buf = buf.partition(b"\r\n")
                    txt = ln.decode("ascii", "replace").strip()
                    if txt:
                        lines.append(txt)
            blk = parse_block(lines)
            if blk:
                return blk, lines
        return parse_block(lines) or None, lines
    finally:
        ser.close()
        say(f"    (đã đóng {port})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim-log", required=True, help="log của Verilator (build/sim.log)")
    ap.add_argument("--port", action="append", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=10.0)
    ap.add_argument("--drain", type=float, default=1.5)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        sim_lines = Path(args.sim_log).read_text().splitlines()
        sim = parse_block(sim_lines)
        if not sim:
            say(f"LỖI: không đọc được khối F5 đầy đủ trong {args.sim_log}")
            return 1
        say("# F5 check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
        say(f"Verilator ({args.sim_log}):")
        for k, v in sim.items():
            say(f"    F5,{k},{v}")

        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        say(f"Cổng sẽ thử: {ports}")
        if not ports:
            say("LỖI: không tìm thấy cổng /dev/cu.usbserial*")
            return 1

        passes = 0
        used_port = None
        for attempt in range(1, args.repeat + 1):
            if args.repeat > 1:
                say(f"== Lần đọc {attempt}/{args.repeat} ==")
            kit = None
            for p in ports:
                say(f"--- Thử cổng {p} ---")
                kit, raw = read_kit(p, args, say)
                if kit:
                    used_port = p
                    ports = [p]
                    break
                say(f"    không thấy khối F5 đầy đủ ({len(raw)} dòng thô)")
            if not kit:
                continue

            say("    Kit:")
            for k, v in kit.items():
                say(f"        F5,{k},{v}")

            bad = []
            compared = []
            for k in sim:
                if k in SKIP:
                    continue
                if k not in kit:
                    bad.append(f"kit thiếu khoá '{k}'")
                elif kit[k] != sim[k]:
                    bad.append(f"'{k}': kit={kit[k]!r} != verilator={sim[k]!r}")
                else:
                    compared.append(k)
            if "loop" not in compared:
                bad.append("khoá 'loop' (tiêu chí ĐẠT) không khớp hoặc thiếu")
            if bad:
                say("    KHÔNG ĐẠT: " + "; ".join(bad))
            else:
                say(f"    ĐẠT: khớp tuyệt đối {len(compared)} khoá: {', '.join(compared)}")
                passes += 1
            if attempt < args.repeat:
                time.sleep(0.3)

        say("")
        if passes == args.repeat and used_port:
            say(f"F5_PASS cổng={used_port} loop={sim['loop']} hwc={sim['hwc']} "
                f"instret={sim['instret']} lần_đọc_đạt={passes}/{args.repeat}")
            return 0
        say(f"F5_FAIL: {passes}/{args.repeat} lần đọc đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
