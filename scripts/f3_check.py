#!/usr/bin/env python3
"""F3 — đọc hai dòng CRC32 từ kit và so với giá trị Python tính lại.

Kit in mỗi giây hai dòng:
    F3,ROM,xxxxxxxx     CRC32 của 64 KB nội dung BSRAM đã khởi tạo bằng $readmemh
    F3,RW,xxxxxxxx      CRC32 sau khi ghi mẫu thứ hai vào toàn bộ rồi đọc lại

CRC kỳ vọng KHÔNG hard-code: script gọi lại chính `scripts/gen_pattern.py` (cùng LFSR,
cùng hạt giống, cùng thứ tự byte little-endian) để tính tại chỗ.

Tự tìm cổng trong /dev/cu.usbserial* (quy tắc 9). Mọi lần mở cổng đều có timeout.
Mã thoát 0 = ĐẠT.
"""
from __future__ import annotations

import argparse
import glob
import importlib.util
import re
import sys
import time
import zlib
from pathlib import Path

import serial

HERE = Path(__file__).resolve().parent


def load_gen_pattern():
    spec = importlib.util.spec_from_file_location("gen_pattern", HERE / "gen_pattern.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def expected_crcs(words: int, seed=None):
    gp = load_gen_pattern()
    rom = list(gp.lfsr_words(words, seed if seed is not None else gp.SEED))
    rw = [(a ^ gp.MASK2) & 0xFFFFFFFF for a in range(words)]
    return (zlib.crc32(gp.to_bytes_le(rom)) & 0xFFFFFFFF,
            zlib.crc32(gp.to_bytes_le(rw)) & 0xFFFFFFFF,
            rom)


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def collect(ser, say, timeout, need=("ROM", "RW")):
    """Thu các dòng F3,<nhãn>,<crc hex> tới khi đủ các nhãn cần."""
    found = {}
    buf = b""
    raw = []
    t0 = time.time()
    while time.time() - t0 < timeout and not all(k in found for k in need):
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
            m = re.fullmatch(r"F3,(ROM|RW),([0-9A-Fa-f]{8})", text)
            if m:
                found[m.group(1)] = int(m.group(2), 16)
            else:
                say(f"    (dòng không khớp khuôn: {text!r})")
    return found, raw


def try_port(port, args, say, exp_rom, exp_rw):
    say(f"--- Thử cổng {port} @ {args.baud} 8N1 ---")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.2)
    except Exception as exc:  # noqa: BLE001
        say(f"    không mở được: {type(exc).__name__}: {exc}")
        return False, None
    try:
        time.sleep(0.1)
        ser.reset_input_buffer()
        # Xả bộ đệm cũ: driver macOS/FT2232 còn giữ dữ liệu của bitstream TRƯỚC đó
        # (đã quan sát thực tế khi thay bitstream), reset_input_buffer() không đủ.
        # Đọc bỏ trong `drain` giây rồi mới bắt đầu thu.
        t_drain = time.time()
        dropped = 0
        while time.time() - t_drain < args.drain:
            dropped += len(ser.read(512))
        if dropped:
            say(f"    (xả {dropped} byte tồn trong bộ đệm trước khi đọc)")
        t0 = time.time()
        found, raw = collect(ser, say, args.timeout)
        dt = time.time() - t0
        if not found:
            say(f"    KHÔNG ĐẠT: sau {dt:.2f}s không thấy dòng F3,...")
            return False, None
        say(f"    Các dòng thô nhận được ({len(raw)}): {raw[:6]}")
        ok = True
        for label, exp in (("ROM", exp_rom), ("RW", exp_rw)):
            got = found.get(label)
            if got is None:
                say(f"    KHÔNG ĐẠT: thiếu dòng F3,{label}")
                ok = False
            elif got != exp:
                say(f"    KHÔNG ĐẠT: CRC {label} từ kit = {got:08X}, Python = {exp:08X}")
                ok = False
            else:
                say(f"    ĐẠT: CRC {label} = {got:08X} khớp Python")
        if not ok:
            return False, None
        return True, {"port": port, "rom": found["ROM"], "rw": found["RW"],
                      "seconds": dt, "lines": len(raw)}
    finally:
        ser.close()
        say(f"    (đã đóng {port})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", action="append", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--words", type=int, default=16384)
    ap.add_argument("--timeout", type=float, default=6.0)
    ap.add_argument("--drain", type=float, default=1.5,
                    help="số giây đọc bỏ để xả dữ liệu tồn của bitstream cũ")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=None,
                    help="hạt giống LFSR nếu khác mặc định (phép phản chứng)")
    ap.add_argument("--repeat", type=int, default=1,
                    help="số lần đọc lại độc lập (mở/đóng cổng mỗi lần)")
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        exp_rom, exp_rw, rom = expected_crcs(args.words, args.seed)
        say("# F3 check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
        say(f"Số từ: {args.words} ({args.words*4} byte = {args.words*4//1024} KB)")
        say(f"Từ đầu/cuối của mẫu: {rom[0]:08x} ... {rom[-1]:08x}")
        say(f"CRC32 kỳ vọng (Python, zlib): ROM={exp_rom:08X}  RW={exp_rw:08X}")

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
            got_one = False
            for p in ports:
                ok, inf = try_port(p, args, say, exp_rom, exp_rw)
                if ok:
                    got_one = True
                    info = inf
                    ports = [p]      # các lần sau chỉ thử cổng đã đúng
                    break
            if got_one:
                passes += 1
            if attempt < args.repeat:
                time.sleep(0.5)

        say("")
        if passes == args.repeat and info:
            say(f"F3_PASS cổng={info['port']} CRC_ROM={info['rom']:08X} "
                f"CRC_RW={info['rw']:08X} lần_đọc_đạt={passes}/{args.repeat}")
            return 0
        say(f"F3_FAIL: {passes}/{args.repeat} lần đọc đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
