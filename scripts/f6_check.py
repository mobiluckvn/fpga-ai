#!/usr/bin/env python3
"""F6 — đọc số đo từ kit, so với Verilator, kiểm các điều kiện ĐẠT và ghi CSV.

Điều kiện ĐẠT (docs/FEASIBILITY_PLAN.md):
  1. Overhead của phép đo là MỘT HẰNG SỐ  -> chỉ một giá trị F6,cal
  2. hw_count − mcycle là hằng số ở MỌI độ dài
  3. kit = mô phỏng (từng độ dài, bằng tuyệt đối)
  4. 3 lần bật nguồn cho số giống hệt  -> chạy script 3 lần với --run 1/2/3, CSV cộng dồn
  5. rdcycleh tăng khi vượt 2^32 chu kỳ -> dòng F6,hi (đọc riêng bằng --wait-hi)

Ghi CSV: run,length,mcycle,hw_count,sim_cycles  (theo đúng kế hoạch, thêm cột phụ).
Mã thoát 0 = ĐẠT.
"""
from __future__ import annotations

import argparse
import csv
import glob
import re
import sys
import time
from pathlib import Path

import serial

LINE_RE = re.compile(r"^F6,([a-z]+),?(.*)$")


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
    """Lấy một khối đầy đủ (F6,hello ... F6,done). Trả về dict:
       {'hello':..., 'cal':[(delta,count)...], 'len':{N:(mcycle,hwc,instret)}, 'hi':[...]}"""
    out = {"cal": [], "len": {}, "hi": None, "hello": None, "calovf": None}
    started = False
    for ln in lines:
        m = LINE_RE.match(ln.strip())
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        if key == "hello":
            started = True
            out = {"cal": [], "len": {}, "hi": None, "hello": rest, "calovf": None}
            continue
        if not started:
            continue
        if key == "cal":
            a = rest.split(",")
            out["cal"].append((int(a[0]), int(a[1])))
        elif key == "calovf":
            out["calovf"] = int(rest)
        elif key == "len":
            a = [int(x) for x in rest.split(",")]
            out["len"][a[0]] = (a[1], a[2], a[3])
        elif key == "hi":
            out["hi"] = [int(x) for x in rest.split(",")]
        elif key == "done":
            if out["len"]:
                out["complete"] = True
                return out
    # Chỉ trả về khối ĐẦY ĐỦ (đã thấy F6,done). Trả về khối dở dang sẽ làm
    # mất những dòng chưa tới — lỗi đã gặp: thiếu độ dài 100000.
    return None


def read_kit(port, args, say, need_hi=False):
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
        timeout = args.hi_timeout if need_hi else args.timeout
        while time.time() - t0 < timeout:
            chunk = ser.read(256)
            if chunk:
                buf += chunk
                while b"\r\n" in buf:
                    ln, _, buf = buf.partition(b"\r\n")
                    txt = ln.decode("ascii", "replace").strip()
                    if txt:
                        lines.append(txt)
            blk = parse_block(lines)
            if blk and (not need_hi or blk.get("hi")):
                return blk, lines
        return parse_block(lines), lines
    finally:
        ser.close()
        say(f"    (đã đóng {port})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim-log", required=True)
    ap.add_argument("--csv", required=True)
    ap.add_argument("--run", type=int, default=1, help="số thứ tự lần bật nguồn (1..3)")
    ap.add_argument("--port", action="append", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=12.0)
    ap.add_argument("--hi-timeout", type=float, default=260.0)
    ap.add_argument("--drain", type=float, default=1.5)
    ap.add_argument("--wait-hi", action="store_true",
                    help="chờ cả dòng F6,hi (vòng lặp vượt 2^32 chu kỳ, ~166 s)")
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        sim = parse_block(Path(args.sim_log).read_text().splitlines())
        if not sim:
            say(f"LỖI: không đọc được khối F6 trong {args.sim_log}")
            return 1
        say("# F6 check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}  ·  lần bật nguồn: {args.run}")
        say(f"Verilator: cal={sim['cal']}  độ dài={sorted(sim['len'])}")

        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        say(f"Cổng sẽ thử: {ports}")
        kit = None
        used = None
        for p in ports:
            say(f"--- Thử cổng {p} ---")
            kit, raw = read_kit(p, args, say, need_hi=args.wait_hi)
            if kit and (not args.wait_hi or kit.get("hi")):
                used = p
                break
            say(f"    chưa đủ dữ liệu ({len(raw)} dòng thô)")
            kit = None
        if not kit:
            say("F6_FAIL: không đọc được số đo từ kit")
            return 1

        say(f"Kit (cổng {used}): hello={kit['hello']}")
        say(f"    cal = {kit['cal']}" + (f"  (tràn bucket: {kit['calovf']})" if kit['calovf'] else ""))
        for n in sorted(kit["len"]):
            say(f"    len {n:>7}: mcycle={kit['len'][n][0]:>8} hwc={kit['len'][n][1]:>8} "
                f"instret={kit['len'][n][2]:>8}  hwc-mcycle={kit['len'][n][1]-kit['len'][n][0]}")
        if kit.get("hi"):
            h0, h1, c0, c1, n = kit["hi"]
            say(f"    hi: rdcycleh {h0} -> {h1} (tăng {h1-h0}); rdcycle {c0} -> {c1}; {n} vòng")

        # ---- kiểm các điều kiện ----
        problems = []

        # 1. overhead hằng số
        if len(kit["cal"]) != 1:
            problems.append(f"overhead KHÔNG phải hằng số: {len(kit['cal'])} giá trị khác nhau "
                            f"{kit['cal']}")
        if kit["calovf"]:
            problems.append(f"hiệu chuẩn tràn bucket ({kit['calovf']} giá trị lạ)")

        # 2. hwc - mcycle hằng số
        diffs = {n: kit["len"][n][1] - kit["len"][n][0] for n in kit["len"]}
        uniq = set(diffs.values())
        if len(uniq) != 1:
            problems.append(f"hwc−mcycle KHÔNG phải hằng số: {diffs}")

        # 3. kit = verilator
        for n in sim["len"]:
            if n not in kit["len"]:
                problems.append(f"kit thiếu độ dài {n}")
            elif kit["len"][n] != sim["len"][n]:
                problems.append(f"độ dài {n}: kit={kit['len'][n]} != verilator={sim['len'][n]}")
        if kit["cal"] and sim["cal"] and kit["cal"][0][0] != sim["cal"][0][0]:
            problems.append(f"overhead kit={kit['cal'][0][0]} != verilator={sim['cal'][0][0]}")

        # 5. rdcycleh
        if args.wait_hi:
            if not kit.get("hi"):
                problems.append("không nhận được dòng F6,hi")
            else:
                h0, h1, c0, c1, n = kit["hi"]
                if h1 <= h0:
                    problems.append(f"rdcycleh KHÔNG tăng: {h0} -> {h1}")

        # ---- ghi CSV (cộng dồn qua các lần bật nguồn) ----
        csv_path = Path(args.csv)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        new = not csv_path.exists()
        with open(csv_path, "a", newline="") as f:
            w = csv.writer(f)
            if new:
                w.writerow(["run", "length", "mcycle", "hw_count", "sim_cycles",
                            "instret", "hw_minus_mcycle", "cal_overhead"])
            cal = kit["cal"][0][0] if kit["cal"] else ""
            for n in sorted(kit["len"]):
                mc, hw, ir = kit["len"][n]
                w.writerow([args.run, n, mc, hw, sim["len"].get(n, ("", ))[0], ir, hw - mc, cal])
        say(f"Đã ghi {len(kit['len'])} dòng vào {csv_path} (run={args.run})")

        say("")
        if problems:
            for pb in problems:
                say("  VẤN ĐỀ: " + pb)
            say(f"F6_FAIL run={args.run}")
            return 1
        say(f"F6_PASS run={args.run} overhead={kit['cal'][0][0]} "
            f"hwc_offset={next(iter(uniq))} số_độ_dài={len(kit['len'])} kit=verilator")
        return 0
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
