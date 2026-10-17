#!/usr/bin/env python3
"""F7 — đọc số đo kernel int8 từ kit, so CRC với Python và so chu kỳ với Verilator.

Tiêu chí ĐẠT (docs/FEASIBILITY_PLAN.md):
  - CRC trên kit = Python cho cả hai bài
  - chu kỳ kit = mô phỏng (bằng tuyệt đối)
  - có số chu kỳ/MAC

CRC kỳ vọng KHÔNG hard-code: script gọi lại scripts/gen_f7_data.py để tự tính.
Ghi CSV: bai,mac,cycles_kit,cycles_sim,hw_count,instret,cpi,cycles_per_mac,crc_kit,crc_python.
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
from pathlib import Path

import serial

HERE = Path(__file__).resolve().parent
LINE_RE = re.compile(r"^F7,([A-Za-z]+),?(.*)$")


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def golden_crcs(say):
    """Tính lại CRC kỳ vọng bằng chính module đã sinh dữ liệu."""
    spec = importlib.util.spec_from_file_location("gen_f7_data", HERE / "gen_f7_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    import numpy as np
    rng = np.random.default_rng(mod.SEED)
    pool = rng.integers(-128, 128, size=mod.POOL, dtype=np.int16).astype(np.int8)
    img = rng.integers(-128, 128, size=(mod.IMG, mod.IMG), dtype=np.int16).astype(np.int8)
    w = rng.integers(-64, 65, size=(mod.OCH, mod.K, mod.K), dtype=np.int16).astype(np.int8)
    bias = rng.integers(-4096, 4097, size=mod.OCH, dtype=np.int32)
    _, _, crc_a = mod.task_a(pool)
    _, m0, shift, max_acc, crc_b = mod.task_b(img, w, bias)
    say(f"Python tính lại: CRC_A={crc_a:08X}  CRC_B={crc_b:08X}  "
        f"(M0={m0}, shift={shift}, acc max={max_acc})")
    return crc_a, crc_b, mod


def parse_block(lines):
    out = {"hello": None, "mac": None, "tasks": {}}
    started = False
    for ln in lines:
        m = LINE_RE.match(ln.strip())
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        if key == "hello":
            started = True
            out = {"hello": rest, "mac": None, "tasks": {}}
            continue
        if not started:
            continue
        if key == "mac":
            a = [int(x) for x in rest.split(",")]
            out["mac"] = {"A": a[0], "B": a[1]}
        elif key in ("A", "B"):
            a = rest.split(",")
            out["tasks"][key] = {"cycles": int(a[0]), "hw": int(a[1]),
                                 "instret": int(a[2]), "crc": int(a[3], 16)}
        elif key == "done":
            if out["tasks"]:
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
        return None, lines
    finally:
        ser.close()


def ram_usage(size_path, say):
    """Đọc output của `size -A` để kiểm firmware + dữ liệu vừa RAM 64 KB."""
    if not size_path or not Path(size_path).exists():
        return None
    txt = Path(size_path).read_text()
    secs = {}
    for ln in txt.splitlines():
        p = ln.split()
        if len(p) >= 2 and p[0].startswith("."):
            try:
                secs[p[0]] = int(p[1])
            except ValueError:
                pass
    used = sum(v for k, v in secs.items() if k in (".text", ".data", ".bss", ".sdata", ".sbss"))
    say(f"RAM: " + " + ".join(f"{k} {v}" for k, v in secs.items()
                              if k in (".text", ".data", ".bss")) +
        f" = {used:,} / 65.536 byte ({100*used/65536:.1f} %)")
    return used


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sim-log", required=True)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--size", default=None)
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
        say("# F7 check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
        crc_a, crc_b, mod = golden_crcs(say)
        exp = {"A": crc_a, "B": crc_b}

        sim = parse_block(Path(args.sim_log).read_text().splitlines())
        if not sim:
            say(f"LỖI: không đọc được khối F7 trong {args.sim_log}")
            return 1
        say("Verilator:")
        for k in ("A", "B"):
            t = sim["tasks"][k]
            say(f"    bài {k}: cycles={t['cycles']:,} hw={t['hw']:,} "
                f"instret={t['instret']:,} crc={t['crc']:08X}")

        used = ram_usage(args.size, say)

        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        say(f"Cổng sẽ thử: {ports}")
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
            for key in ("A", "B"):
                if key not in kit["tasks"]:
                    probs.append(f"kit thiếu bài {key}")
                    continue
                t, s = kit["tasks"][key], sim["tasks"][key]
                if t["crc"] != exp[key]:
                    probs.append(f"bài {key}: CRC kit {t['crc']:08X} != Python {exp[key]:08X}")
                if t["cycles"] != s["cycles"]:
                    probs.append(f"bài {key}: cycles kit {t['cycles']:,} != sim {s['cycles']:,}")
                if t["instret"] != s["instret"]:
                    probs.append(f"bài {key}: instret kit {t['instret']:,} != sim {s['instret']:,}")
                if t["hw"] != s["hw"]:
                    probs.append(f"bài {key}: hw kit {t['hw']:,} != sim {s['hw']:,}")
            if probs:
                for pb in probs:
                    say("    VẤN ĐỀ: " + pb)
            else:
                say(f"    ĐẠT: CRC khớp Python và chu kỳ khớp Verilator cho cả hai bài")
                passes += 1
            if attempt < args.repeat:
                time.sleep(0.3)

        if not kit:
            say("F7_FAIL: không đọc được số đo từ kit")
            return 1

        # ---- số chu kỳ/MAC ----
        say("")
        say("## Số đo trên kit")
        rows = []
        for key, name in (("A", "dot int8 1024 x100"), ("B", "conv1 3x3 1->8 kenh 28x28")):
            t = kit["tasks"][key]
            mac = kit["mac"][key]
            cpm = t["cycles"] / mac
            cpi = t["cycles"] / t["instret"]
            say(f"    bài {key} ({name}): {mac:,} MAC · {t['cycles']:,} chu kỳ "
                f"· **{cpm:.2f} chu kỳ/MAC** · CPI {cpi:.2f} "
                f"· hw−cycles={t['hw']-t['cycles']} · {t['cycles']/27e6*1000:.1f} ms @27 MHz")
            rows.append([key, name, mac, t["cycles"], sim["tasks"][key]["cycles"],
                         t["hw"], t["instret"], f"{cpi:.4f}", f"{cpm:.4f}",
                         f"{t['crc']:08X}", f"{exp[key]:08X}"])

        # ngoại suy THÔ cho M1-S
        cpm_b = kit["tasks"]["B"]["cycles"] / kit["mac"]["B"]
        m1s_mac = 192064
        est = cpm_b * m1s_mac
        say("")
        say(f"Ước tính THÔ cho M1-S ({m1s_mac:,} MAC), ngoại suy từ chu kỳ/MAC của bài B "
            f"({cpm_b:.2f}): {est:,.0f} chu kỳ ≈ {est/27e6*1000:.0f} ms @27 MHz.")
        say("   Đây là ƯỚC TÍNH, không phải số đo: M1-S còn có MaxPool và Dense "
            "với chi phí/MAC khác, và conv2 có 16 kênh vào nên tỉ lệ nạp lại trọng số khác.")

        if args.csv:
            Path(args.csv).parent.mkdir(parents=True, exist_ok=True)
            with open(args.csv, "w", newline="") as f:
                wr = csv.writer(f)
                wr.writerow(["bai", "ten", "mac", "cycles_kit", "cycles_sim", "hw_count",
                             "instret", "cpi", "cycles_per_mac", "crc_kit", "crc_python"])
                wr.writerows(rows)
            say(f"Đã ghi {args.csv}")

        say("")
        if passes == args.repeat:
            say(f"F7_PASS cổng={used_port} lần_đọc_đạt={passes}/{args.repeat} "
                f"chu_kỳ/MAC: A={kit['tasks']['A']['cycles']/kit['mac']['A']:.2f} "
                f"B={cpm_b:.2f}" + (f" RAM={used:,}/65536" if used else ""))
            return 0
        say(f"F7_FAIL: {passes}/{args.repeat} lần đọc đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
