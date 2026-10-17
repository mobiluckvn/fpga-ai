#!/usr/bin/env python3
"""F4 — đọc dòng F4,<nhãn>,<acc hex> từ kit và so với giá trị Python tính lại.

Giá trị kỳ vọng KHÔNG hard-code: script gọi lại `scripts/gen_f4_expect.py` (cùng LFSR,
cùng hạt giống, cùng số chu kỳ) để tính tại chỗ.

Có xả bộ đệm trước khi đọc (driver macOS/FT2232 còn giữ dữ liệu của bitstream trước —
đã gặp ở F3). Tự tìm cổng trong /dev/cu.usbserial* (quy tắc 9).

Mã thoát 0 = ĐẠT.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import re
import sys
import time
from pathlib import Path

import serial

HERE = Path(__file__).resolve().parent


def load_expect_mod():
    spec = importlib.util.spec_from_file_location("gen_f4_expect", HERE / "gen_f4_expect.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def try_port(port, args, say, exp_acc):
    say(f"--- Thử cổng {port} @ {args.baud} 8N1 ---")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.2)
    except Exception as exc:  # noqa: BLE001
        say(f"    không mở được: {type(exc).__name__}: {exc}")
        return False, None
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
        raw = []
        found = {}
        t0 = time.time()
        while time.time() - t0 < args.timeout and args.label not in found:
            chunk = ser.read(256)
            if not chunk:
                continue
            buf += chunk
            while b"\r\n" in buf:
                line, _, buf = buf.partition(b"\r\n")
                text = line.decode("ascii", "replace").strip()
                if not text:
                    continue
                raw.append(text)
                m = re.fullmatch(r"F4,([A-Z0-9]{3}),([0-9A-Fa-f]{8})", text)
                if m:
                    found[m.group(1)] = int(m.group(2), 16)
                else:
                    say(f"    (dòng không khớp khuôn: {text!r})")
        if not found:
            say(f"    KHÔNG ĐẠT: sau {time.time()-t0:.2f}s không thấy dòng F4,...")
            return False, None
        say(f"    Dòng thô nhận được: {raw[:4]}")
        if args.label not in found:
            say(f"    KHÔNG ĐẠT: không thấy nhãn {args.label} (chỉ có {sorted(found)}). "
                f"Có phải bitstream đang chạy là biến thể khác?")
            return False, None
        got = found[args.label]
        if got != exp_acc:
            say(f"    KHÔNG ĐẠT: acc từ kit = {got:08X}, Python = {exp_acc:08X}")
            return False, None
        say(f"    ĐẠT: acc = {got:08X} khớp Python")
        return True, {"port": port, "label": args.label, "acc": got}
    finally:
        ser.close()
        say(f"    (đã đóng {port})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="DSP", choices=("DSP", "D18", "PRM", "LUT"))
    ap.add_argument("--port", action="append", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--cycles", type=int, default=None)
    ap.add_argument("--timeout", type=float, default=6.0)
    ap.add_argument("--drain", type=float, default=1.5)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        mod = load_expect_mod()
        n = args.cycles if args.cycles else mod.N
        t0 = time.time()
        exp_acc, a_end, b_end, dmin, dmax = mod.accumulate(n)
        say("# F4 check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
        say(f"Biến thể cần kiểm: {args.label}")
        say(f"Python tính lại {n} chu kỳ trong {time.time()-t0:.2f}s: "
            f"ACC={exp_acc:08X} (LFSR cuối a={a_end:08X} b={b_end:08X}, "
            f"dot trong khoảng {dmin}..{dmax})")

        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        say(f"Cổng sẽ thử: {ports}")
        if not ports:
            say("LỖI: không tìm thấy cổng /dev/cu.usbserial*")
            return 1

        passes = 0
        info = None
        for attempt in range(1, args.repeat + 1):
            if args.repeat > 1:
                say(f"== Lần đọc {attempt}/{args.repeat} ==")
            for p in ports:
                ok, inf = try_port(p, args, say, exp_acc)
                if ok:
                    passes += 1
                    info = inf
                    ports = [p]
                    break
            if attempt < args.repeat:
                time.sleep(0.3)

        say("")
        if passes == args.repeat and info:
            say(f"F4_PASS nhãn={info['label']} cổng={info['port']} "
                f"ACC={info['acc']:08X} lần_đọc_đạt={passes}/{args.repeat}")
            return 0
        say(f"F4_FAIL nhãn={args.label}: {passes}/{args.repeat} lần đọc đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
