#!/usr/bin/env python3
"""F8 — đọc số đo DOT4 từ kit, kiểm đúng đắn và tính tăng tốc thật.

Tiêu chí ĐẠT (docs/FEASIBILITY_PLAN.md):
  - CRC khớp (bản DOT4 = bản vô hướng = Python)
  - kit = mô phỏng (chu kỳ bằng tuyệt đối)
  - có số tăng tốc thật

CRC kỳ vọng KHÔNG hard-code: gọi lại scripts/gen_f8_data.py để tự tính.
So thêm với F7 (results/feasibility/F7/kernel.csv) để kiểm bản vô hướng không đổi
khi bật PCPI.
Mã thoát 0 = ĐẠT.
"""
from __future__ import annotations

import argparse
import csv
import glob
import importlib.util
import re
import sys
import time
import zlib
from pathlib import Path

import serial

HERE = Path(__file__).resolve().parent
LINE_RE = re.compile(r"^F8,([A-Za-z0-9]+),?(.*)$")


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def golden_crc(say):
    """Tính lại CRC32 kỳ vọng của bài A (offset thẳng hàng 4 byte) bằng Python."""
    import numpy as np
    spec = importlib.util.spec_from_file_location("gen_f7_data", HERE / "gen_f7_data.py")
    f7 = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(f7)
    rng = np.random.default_rng(f7.SEED)
    pool = rng.integers(-128, 128, size=f7.POOL, dtype=np.int16).astype(np.int8)
    span = f7.POOL - f7.VLEN
    res = []
    for i in range(f7.NPAIR):
        oa = ((i * 71) % span) & ~3
        ob = (((i * 131) + 3000) % span) & ~3
        a = pool[oa:oa + f7.VLEN].astype(np.int32)
        b = pool[ob:ob + f7.VLEN].astype(np.int32)
        v = int(np.dot(a, b)) & 0xFFFFFFFF
        res.append(v)
    raw = b"".join(v.to_bytes(4, "little") for v in res)
    crc = zlib.crc32(raw) & 0xFFFFFFFF
    say(f"Python tính lại CRC32 bài A (offset thẳng hàng 4 byte): {crc:08X}")
    return crc


def parse_block(lines):
    out = {"hello": None, "mac": None, "scalar": None, "dot4": None, "lat": None}
    started = False
    for ln in lines:
        m = LINE_RE.match(ln.strip())
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        if key == "hello":
            started = True
            out = {"hello": rest, "mac": None, "scalar": None, "dot4": None, "lat": None}
            continue
        if not started:
            continue
        if key == "mac":
            a = [int(x) for x in rest.split(",")]
            out["mac"] = {"mac_a": a[0], "ndot4": a[1]}
        elif key in ("scalar", "dot4"):
            a = rest.split(",")
            out[key] = {"cycles": int(a[0]), "hw": int(a[1]),
                        "instret": int(a[2]), "crc": int(a[3], 16)}
        elif key == "lat":
            a = [int(x) for x in rest.split(",")]
            out["lat"] = {"n": a[0], "dot4": a[1], "add": a[2]}
        elif key == "done":
            if out["scalar"] and out["dot4"]:
                return out
    return None


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
            say(f"    (xả {dropped} byte tồn)")
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
        return None, lines
    finally:
        ser.close()


def f7_scalar_cycles(path, say):
    if not path or not Path(path).exists():
        return None
    with open(path) as f:
        for row in csv.DictReader(f):
            if row["bai"] == "A":
                v = int(row["cycles_kit"])
                say(f"F7 bài A (không có PCPI), chu kỳ trên kit: {v:,}")
                return v
    return None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim-log", required=True)
    ap.add_argument("--variant", required=True, choices=("dsp", "lut"))
    ap.add_argument("--csv", default=None)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--size", default=None)
    ap.add_argument("--f7-csv", default=None)
    ap.add_argument("--port", action="append", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--drain", type=float, default=0.0)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        say("# F8 check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}  ·  biến thể: {args.variant}")
        crc_exp = golden_crc(say)

        sim = parse_block(Path(args.sim_log).read_text().splitlines())
        if not sim:
            say(f"LỖI: không đọc được khối F8 trong {args.sim_log}")
            return 1
        say("Verilator (nhân hành vi):")
        for k in ("scalar", "dot4"):
            t = sim[k]
            say(f"    {k:7s}: cycles={t['cycles']:,} instret={t['instret']:,} crc={t['crc']:08X}")

        f7c = f7_scalar_cycles(args.f7_csv, say)

        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        passes = 0
        kit = None
        used_port = None
        for attempt in range(1, args.repeat + 1):
            if args.repeat > 1:
                say(f"== Lần đọc {attempt}/{args.repeat} ==")
            k = None
            for p in ports:
                k, raw = read_kit(p, args, say)
                if k:
                    used_port = p
                    ports = [p]
                    break
                say(f"    {p}: chưa đủ dự liệu ({len(raw)} dòng thô)")
            if not k:
                continue
            kit = k
            probs = []
            for key in ("scalar", "dot4"):
                if kit[key]["crc"] != crc_exp:
                    probs.append(f"{key}: CRC kit {kit[key]['crc']:08X} != Python {crc_exp:08X}")
                for col in ("cycles", "instret", "hw"):
                    if kit[key][col] != sim[key][col]:
                        probs.append(f"{key}.{col}: kit {kit[key][col]:,} != sim {sim[key][col]:,}")
            if kit["scalar"]["crc"] != kit["dot4"]["crc"]:
                probs.append("CRC bản DOT4 khác bản vô hướng")
            if probs:
                for pb in probs:
                    say("    VẤN ĐỀ: " + pb)
            else:
                say("    ĐẠT: CRC DOT4 = vô hướng = Python; chu kỳ kit = Verilator")
                passes += 1
            if attempt < args.repeat:
                time.sleep(0.3)

        if not kit:
            say("F8_FAIL: không đọc được số đo từ kit")
            return 1

        mac = kit["mac"]["mac_a"]
        nd = kit["mac"]["ndot4"]
        cs = kit["scalar"]["cycles"]
        cd = kit["dot4"]["cycles"]
        say("")
        say("## Số đo trên kit")
        say(f"    bài A, {mac:,} MAC, {nd:,} lệnh DOT4")
        say(f"    vô hướng: {cs:,} chu kỳ · {kit['scalar']['instret']:,} lệnh · "
            f"{cs/mac:.2f} chu kỳ/MAC · CPI {cs/kit['scalar']['instret']:.2f}")
        say(f"    DOT4    : {cd:,} chu kỳ · {kit['dot4']['instret']:,} lệnh · "
            f"{cd/mac:.2f} chu kỳ/MAC · CPI {cd/kit['dot4']['instret']:.2f}")
        say(f"    **TĂNG TỐC = {cs/cd:.3f}x** (số lệnh giảm "
            f"{kit['scalar']['instret']/kit['dot4']['instret']:.3f}x)")
        if kit["lat"]:
            la = kit["lat"]
            say(f"    độ trễ DOT4: vòng DOT4 {la['dot4']:,} vs vòng ADD {la['add']:,} "
                f"trên {la['n']:,} vòng → DOT4 đắt hơn ADD "
                f"{(la['dot4']-la['add'])/la['n']:+.3f} chu kỳ/lệnh")
        if f7c:
            say(f"    bản vô hướng khi BẬT PCPI: {cs:,} chu kỳ; "
                f"ở F7 khi KHÔNG có PCPI: {f7c:,} → "
                f"chênh {cs-f7c:+,} chu kỳ")

        if args.csv:
            path = Path(args.csv)
            path.parent.mkdir(parents=True, exist_ok=True)
            new = args.append and path.exists()
            with open(path, "a" if new else "w", newline="") as f:
                wr = csv.writer(f)
                if not new:
                    wr.writerow(["bien_the", "ban", "mac", "ndot4", "cycles_kit", "cycles_sim",
                                 "hw_count", "instret", "cpi", "cycles_per_mac", "speedup",
                                 "crc_kit", "crc_python", "lat_dot4_minus_add"])
                lat = ((kit["lat"]["dot4"] - kit["lat"]["add"]) / kit["lat"]["n"]
                       if kit["lat"] else "")
                for ban in ("scalar", "dot4"):
                    t = kit[ban]
                    wr.writerow([args.variant, ban, mac, nd if ban == "dot4" else 0,
                                 t["cycles"], sim[ban]["cycles"], t["hw"], t["instret"],
                                 f"{t['cycles']/t['instret']:.4f}",
                                 f"{t['cycles']/mac:.4f}",
                                 f"{cs/cd:.4f}" if ban == "dot4" else "",
                                 f"{t['crc']:08X}", f"{crc_exp:08X}",
                                 f"{lat:.4f}" if ban == "dot4" and lat != "" else ""])
            say(f"Đã ghi {path}")

        say("")
        if passes == args.repeat:
            say(f"F8_PASS biến_thể={args.variant} cổng={used_port} "
                f"lần_đọc_đạt={passes}/{args.repeat} tăng_tốc={cs/cd:.3f}x "
                f"chu_kỳ/MAC {cs/mac:.2f}→{cd/mac:.2f}")
            return 0
        say(f"F8_FAIL biến_thể={args.variant}: {passes}/{args.repeat} lần đọc đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
