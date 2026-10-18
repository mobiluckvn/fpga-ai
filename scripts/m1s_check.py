#!/usr/bin/env python3
"""M1-S — đọc số đo suy luận từ kit, so với golden Python và với Verilator.

Tiêu chí ghi nhận một số đo (theo README/quy ước dự án):
  - CRC32 từng lớp trên kit = CRC32 golden Python  (a1, p1, a2, p2, logit)
  - dự đoán trên kit = dự đoán golden
  - số chu kỳ trên kit = số chu kỳ trong Verilator (bằng tuyệt đối)

CRC/dự đoán golden KHÔNG hard-code: đọc lại từ fw/weights.h (file do
model/quantize_m1s.py sinh ra từ chính mô hình đã huấn luyện).

Ghi CSV: bien_the,img,label,pred,pred_golden,conv1,pool1,conv2,pool2,dense,total,
         instret,cycles_sim,crc_ok,ms_27mhz,cycles_per_mac
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

HERE = Path(__file__).resolve().parent
WEIGHTS_H = HERE.parent / "fw" / "weights.h"
# Số MAC mặc định là của M1-S; `macs_from_weights()` ghi đè theo đúng header đang dùng,
# nên cột "chu kỳ/MAC" đúng cho cả mô hình giữ lại M1-L (662.912 MAC). Trước khi có hàm
# này, phép đo M1-L in ra 5,81 chu kỳ/MAC vì chia cho 192.064 của M1-S.
MAC_TOTAL = 192064
MAC_LAYER = {"conv1": 48672, "conv2": 139392, "dense": 4000, "pool1": 0, "pool2": 0}


def macs_from_weights(path):
    """Suy số MAC từng lớp từ các #define trong weights.h (do quantize sinh ra)."""
    txt = pathlib.Path(path).read_text() if not isinstance(path, Path) else path.read_text()
    d = {k: int(v) for k, v in
         re.findall(r"^#define\s+M1S_(\w+)\s+(\d+)\s*$", txt, re.M)}
    try:
        c1, c2 = d["C1"], d["C2"]
        o1, o2 = d["OUT1"], d["OUT2"]
        p2, ncls = d["POOL2"], d["NCLS"]
    except KeyError:
        return None, None
    lay = {"conv1": o1 * o1 * c1 * 9,
           "conv2": o2 * o2 * c2 * c1 * 9,
           "dense": p2 * p2 * c2 * ncls,
           "pool1": 0, "pool2": 0}
    tot = d.get("MAC", sum(lay.values()))
    return tot, lay
LINE_RE = re.compile(r"^M1S,([a-z]+),?(.*)$")   # dấu phẩy thứ hai là tùy chọn: dòng "M1S,done" không có


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def read_golden(path: Path):
    """Lấy m1s_labels, m1s_pred_golden và 5 mảng CRC từ weights.h."""
    txt = path.read_text()
    out = {}
    for name in ("m1s_labels", "m1s_pred_golden", "m1s_crc_a1", "m1s_crc_p1",
                 "m1s_crc_a2", "m1s_crc_p2", "m1s_crc_logit"):
        m = re.search(rf"{name}\[\d+\][^=]*=\s*\{{(.*?)\}};", txt, re.S)
        if not m:
            raise SystemExit(f"Không thấy {name} trong {path}")
        vals = [int(v) for v in re.findall(r"-?\d+", m.group(1))]
        out[name] = vals
    m = re.search(r"float ([\d.]+)% · int8 ([\d.]+)%", txt)
    out["acc"] = (float(m.group(1)), float(m.group(2))) if m else None
    return out


def parse_block(lines):
    out = {"hello": None, "variant": None, "src": None,
           "img": {}, "cyc": {}, "crc": {}, "sum": None}
    started = False
    for ln in lines:
        m = LINE_RE.match(ln.strip())
        if not m:
            continue
        key, rest = m.group(1), m.group(2)
        a = rest.split(",")
        if key == "hello":
            started = True
            out = {"hello": a[0], "variant": a[1] if len(a) > 1 else None, "src": None,
                   "img": {}, "cyc": {}, "crc": {}, "sum": None}
            continue
        if not started:
            continue
        if key == "src":
            out["src"] = a[0]
        elif key == "img":
            out["img"][int(a[0])] = dict(label=int(a[1]), pred=int(a[2]),
                                         pred_golden=int(a[3]), okmask=int(a[4]))
        elif key == "cyc":
            out["cyc"][int(a[0])] = dict(conv1=int(a[1]), pool1=int(a[2]), conv2=int(a[3]),
                                         pool2=int(a[4]), dense=int(a[5]), total=int(a[6]),
                                         instret=int(a[7]))
        elif key == "crc":
            out["crc"][int(a[0])] = [int(x, 16) for x in a[1:6]]
        elif key == "sum":
            out["sum"] = dict(n=int(a[0]), label_ok=int(a[1]),
                              pred_ok=int(a[2]), crc_ok=int(a[3]))
        elif key == "done":
            if out["sum"] is not None:
                return out
    return None


def open_port(port, args, say):
    """Mở cổng và xả dữ liệu tồn. Trả về cổng đang mở, hoặc None nếu không mở được."""
    try:
        ser = serial.Serial(port, args.baud, timeout=0.2)
    except Exception as exc:  # noqa: BLE001
        say(f"    không mở được: {type(exc).__name__}: {exc}")
        return None
    time.sleep(0.1)
    ser.reset_input_buffer()
    t_drain = time.time()
    dropped = 0
    while time.time() - t_drain < args.drain:
        dropped += len(ser.read(512))
    if dropped:
        say(f"    (xả {dropped} byte tồn)")
    return ser


class BlockReader:
    """Đọc lần lượt các khối báo cáo từ MỘT cổng đang mở.

    Phải GIỮ LẠI phần byte dư sau mỗi khối: khối kế tiếp thường đã nằm sẵn trong
    chunk vừa đọc, nên nếu vứt đi thì lần đọc sau mất dữ liệu. (Bản đầu của hàm này
    vứt đi thật, và phép chạy khô hai khối liên tiếp đã bắt được: lần đọc 2 trả None.)

    `parse_block()` tự đồng bộ — chỉ bắt đầu ở dòng `hello`, chỉ trả về ở `done` —
    nên khối dở dang ở đầu luồng bị bỏ qua an toàn.
    """

    def __init__(self, ser, args):
        self.ser = ser
        self.args = args
        self.buf = b""

    def read(self):
        lines = []
        t0 = time.time()
        while True:
            while b"\r\n" in self.buf:
                ln, _, self.buf = self.buf.partition(b"\r\n")
                txt = ln.decode("ascii", "replace").strip()
                if not txt:
                    continue
                lines.append(txt)
                blk = parse_block(lines)
                if blk:
                    return blk, lines
            if time.time() - t0 >= self.args.timeout:
                return None, lines
            chunk = self.ser.read(512)
            if chunk:
                self.buf += chunk


def read_block(ser, args):
    """Đọc một khối từ cổng đang mở, không giữ trạng thái. Dùng cho đường mặc định."""
    return BlockReader(ser, args).read()


def read_kit(port, args, say):
    """Mở cổng, đọc một khối, đóng cổng. Hành vi mặc định, không đổi."""
    ser = open_port(port, args, say)
    if ser is None:
        return None, []
    try:
        return read_block(ser, args)
    finally:
        ser.close()


def ram_usage(size_path, say):
    if not size_path or not Path(size_path).exists():
        return None
    secs = {}
    for ln in Path(size_path).read_text().splitlines():
        p = ln.split()
        if len(p) >= 2 and p[0].startswith("."):
            try:
                secs[p[0]] = int(p[1])
            except ValueError:
                pass
    used = sum(v for k, v in secs.items() if k in (".text", ".data", ".bss"))
    say("RAM: " + " + ".join(f"{k} {v}" for k, v in secs.items()
                             if k in (".text", ".data", ".bss"))
        + f" = {used:,} / 65.536 byte ({100*used/65536:.1f} %)")
    return used


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--variant", required=True)
    ap.add_argument("--csv-label", default=None,
                    help="nhãn ghi vào CSV (mặc định = --variant); dùng khi cùng firmware "
                         "chạy trên lõi khác, ví dụ nhãn bv0 cho firmware A-V0 trên lõi nhánh B")
    ap.add_argument("--src-hash", default=None,
                    help="dấu vân tay nội dung main.c+weights.h mà firmware PHẢI báo về")
    ap.add_argument("--sim-log", required=True)
    ap.add_argument("--size", default=None)
    ap.add_argument("--csv", default=None)
    ap.add_argument("--append", action="store_true")
    ap.add_argument("--weights", default=str(WEIGHTS_H))
    ap.add_argument("--port", action="append", default=None)
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--timeout", type=float, default=40.0)
    ap.add_argument("--drain", type=float, default=0.0)
    ap.add_argument("--repeat", type=int, default=1)
    ap.add_argument("--keep-open", action="store_true",
                    help="giữ cổng serial MỞ xuyên suốt các lần đọc, thay vì đóng rồi "
                         "mở lại giữa chừng. Mặc định TẮT để không đổi cách đo của mọi "
                         "số đã ghi nhận. Dùng khi lần đọc sau mất sạch dữ liệu vì kênh "
                         "FT2232 kẹt ở nhịp mở lại (xem results/pipeline/S6/kit/README.md).")
    ap.add_argument("--log", default=None)
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        say("# M1-S check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}  ·  biến thể: {args.variant}")
        g = read_golden(Path(args.weights))
        _tot, _lay = macs_from_weights(Path(args.weights))
        if _tot:
            global MAC_TOTAL, MAC_LAYER
            MAC_TOTAL, MAC_LAYER = _tot, _lay
        nimg = len(g["m1s_labels"])
        if g["acc"]:
            say(f"Độ chính xác mô hình (10.000 ảnh test): float {g['acc'][0]:.2f}% · "
                f"int8 {g['acc'][1]:.2f}%  (chênh {g['acc'][0]-g['acc'][1]:+.2f} điểm %)")
        say(f"Golden từ {args.weights}: {nimg} ảnh thử, nhãn {g['m1s_labels']}, "
            f"dự đoán golden {g['m1s_pred_golden']}")

        sim = parse_block(Path(args.sim_log).read_text().splitlines())
        if not sim:
            say(f"LỖI: không đọc được khối M1S trong {args.sim_log}")
            return 1
        say(f"Verilator: biến thể {sim['variant']}, tổng/ảnh "
            f"{[sim['cyc'][k]['total'] for k in sorted(sim['cyc'])]}")

        used = ram_usage(args.size, say)

        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        passes = 0
        kit = None
        used_port = None
        held = None          # cổng đang giữ mở, chỉ khi --keep-open
        if args.keep_open:
            say("    (giữ cổng mở xuyên suốt các lần đọc)")
        for attempt in range(1, args.repeat + 1):
            if args.repeat > 1:
                say(f"== Lần đọc {attempt}/{args.repeat} ==")
            k = None
            if held is not None:
                k, raw = held.read()
                if not k:
                    say(f"    {used_port}: chưa đủ dữ liệu ({len(raw)} dòng thô)")
            else:
                for p in ports:
                    if args.keep_open:
                        ser = open_port(p, args, say)
                        if ser is None:
                            continue
                        rd = BlockReader(ser, args)
                        k, raw = rd.read()
                        if k:
                            held = rd
                        else:
                            ser.close()
                    else:
                        k, raw = read_kit(p, args, say)
                    if k:
                        used_port = p
                        ports = [p]
                        break
                    say(f"    {p}: chưa đủ dữ liệu ({len(raw)} dòng thô)")
            if not k:
                continue
            kit = k
            probs = []
            if k["variant"] != args.variant:
                probs.append(f"kit báo biến thể {k['variant']}, mong đợi {args.variant}")
            if args.src_hash and k.get("src") != args.src_hash:
                probs.append(f"kit báo SRC_HASH={k.get('src')}, mong đợi {args.src_hash}"
                             " — firmware trên kit KHÔNG dựng từ mã nguồn hiện tại")
            for i in range(nimg):
                if i not in k["crc"]:
                    probs.append(f"ảnh {i}: kit thiếu dòng crc")
                    continue
                exp = [g["m1s_crc_a1"][i], g["m1s_crc_p1"][i], g["m1s_crc_a2"][i],
                       g["m1s_crc_p2"][i], g["m1s_crc_logit"][i]]
                for nm, got, e in zip(("a1", "p1", "a2", "p2", "logit"), k["crc"][i], exp):
                    if got != e:
                        probs.append(f"ảnh {i}: CRC {nm} kit {got:08X} != golden {e:08X}")
                if k["img"][i]["pred"] != g["m1s_pred_golden"][i]:
                    probs.append(f"ảnh {i}: dự đoán kit {k['img'][i]['pred']} "
                                 f"!= golden {g['m1s_pred_golden'][i]}")
                for col in ("conv1", "pool1", "conv2", "pool2", "dense", "total", "instret"):
                    if k["cyc"][i][col] != sim["cyc"][i][col]:
                        probs.append(f"ảnh {i}: {col} kit {k['cyc'][i][col]:,} "
                                     f"!= sim {sim['cyc'][i][col]:,}")
            if probs:
                for pb in probs[:12]:
                    say("    VẤN ĐỀ: " + pb)
                if len(probs) > 12:
                    say(f"    ... và {len(probs)-12} vấn đề nữa")
            else:
                say(f"    ĐẠT: CRC 5 lớp × {nimg} ảnh khớp golden; dự đoán khớp golden; "
                    f"chu kỳ kit = Verilator")
                passes += 1
            if attempt < args.repeat:
                time.sleep(0.3)

        if held is not None:
            held.ser.close()

        if not kit:
            say("M1S_FAIL: không đọc được số đo từ kit")
            return 1

        # ---------- bảng số đo ----------
        say("")
        say("## Số đo trên kit (27 MHz)")
        tot = [kit["cyc"][i]["total"] for i in sorted(kit["cyc"])]
        med = sorted(tot)[len(tot) // 2]
        say(f"    {len(tot)} ảnh · tổng chu kỳ/ảnh: min {min(tot):,} · trung vị {med:,} "
            f"· max {max(tot):,}")
        say(f"    trung vị = {med/27e6*1000:.1f} ms @27 MHz · "
            f"{med/MAC_TOTAL:.2f} chu kỳ/MAC trên {MAC_TOTAL:,} MAC")
        say(f"    dự đoán đúng nhãn: {kit['sum']['label_ok']}/{kit['sum']['n']} · "
            f"khớp golden: {kit['sum']['pred_ok']}/{kit['sum']['n']} · "
            f"CRC khớp hết 5 lớp: {kit['sum']['crc_ok']}/{kit['sum']['n']}")
        say("")
        say("    | lớp | chu kỳ (trung vị) | % tổng | MAC | chu kỳ/MAC |")
        say("    |---|---:|---:|---:|---:|")
        for lay in ("conv1", "pool1", "conv2", "pool2", "dense"):
            vals = sorted(kit["cyc"][i][lay] for i in sorted(kit["cyc"]))
            v = vals[len(vals) // 2]
            mac = MAC_LAYER[lay]
            cpm = f"{v/mac:.2f}" if mac else "—"
            say(f"    | {lay} | {v:,} | {100*v/med:.1f} % | {mac if mac else '—'} | {cpm} |")

        if args.csv:
            path = Path(args.csv)
            path.parent.mkdir(parents=True, exist_ok=True)
            new = args.append and path.exists()
            with open(path, "a" if new else "w", newline="") as f:
                wr = csv.writer(f)
                if not new:
                    wr.writerow(["bien_the", "img", "label", "pred", "pred_golden",
                                 "conv1", "pool1", "conv2", "pool2", "dense", "total",
                                 "instret", "total_sim", "crc_ok_5lop", "ms_27mhz",
                                 "cycles_per_mac"])
                for i in sorted(kit["cyc"]):
                    c = kit["cyc"][i]
                    wr.writerow([args.csv_label or args.variant, i, kit["img"][i]["label"],
                                 kit["img"][i]["pred"], g["m1s_pred_golden"][i],
                                 c["conv1"], c["pool1"], c["conv2"], c["pool2"],
                                 c["dense"], c["total"], c["instret"],
                                 sim["cyc"][i]["total"],
                                 1 if kit["img"][i]["okmask"] == 31 else 0,
                                 f"{c['total']/27e6*1000:.3f}",
                                 f"{c['total']/MAC_TOTAL:.4f}"])
            say(f"Đã ghi {path}")

        say("")
        if passes == args.repeat:
            say(f"M1S_PASS bien_the={args.variant} cổng={used_port} "
                f"lần_đọc_đạt={passes}/{args.repeat} trung_vị={med:,} chu kỳ "
                f"({med/27e6*1000:.1f} ms) chu_kỳ/MAC={med/MAC_TOTAL:.2f}"
                + (f" RAM={used:,}/65536" if used else ""))
            return 0
        say(f"M1S_FAIL bien_the={args.variant}: {passes}/{args.repeat} lần đọc đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
