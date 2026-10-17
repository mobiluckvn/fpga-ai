#!/usr/bin/env python3
"""Chạy ĐỦ tập test MNIST (10.000 ảnh) trên kit, không chỉ 10 ảnh nhúng sẵn.

Giao thức (xem experiment/m1s/main.c, chế độ STREAM_10K):
  host -> kit : 1 byte 0xA5 (đồng bộ) + 784 byte ảnh int8, gửi theo khối 64 byte
                (bài học F2: ghi >= 67 byte một lần làm mất byte ở phía host)
  kit  -> host: M1S10K,<idx>,<pred>,<crc ảnh>,<crc logit>,<c1>,<p1>,<c2>,<p2>,<d>,<tổng>,<instret>

Ba phép kiểm độc lập cho từng ảnh:
  1. crc ảnh   : CRC32 của 784 byte kit NHẬN ĐƯỢC = CRC32 của 784 byte host GỬI
                 -> tách lỗi đường truyền khỏi lỗi tính toán
  2. crc logit : CRC32 của 10 số int32 đầu ra = CRC32 của logit golden Python
                 -> đúng TỪNG BIT, mạnh hơn nhiều so với chỉ so dự đoán
  3. dự đoán   : argmax trên kit = argmax golden, và so với nhãn thật

Không có số nào được tính lại bằng tay: logit golden lấy từ model/golden_m1s.py.
"""
import argparse
import csv
import os
import statistics
import sys
import time
import zlib
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))
import golden_m1s as G          # noqa: E402
import mnist                    # noqa: E402

IMG_BYTES = G.IMG * G.IMG
SYNC = b"\xa5"
CHUNK = 64


def load_golden(n, chunk=500):
    """Ảnh int8 (dạng byte để gửi) + dự đoán/logit golden cho n ảnh test đầu tiên."""
    _tx, _ty, ex, ey = mnist.load()
    n = min(n, len(ex))
    q = dict(np.load(ROOT / "model" / "m1s_int8.npz"))
    for k in ("m0_1", "sh_1", "m0_2", "sh_2"):
        q[k] = int(q[k])

    img_bytes, preds, crc_lg = [], [], []
    for i0 in range(0, n, chunk):
        i1 = min(i0 + chunk, n)
        p, lg = G.infer_batch(ex[i0:i1], q)
        x0 = G.quant_images(ex[i0:i1])            # [N,28,28,1] int8
        for j in range(i1 - i0):
            b = np.ascontiguousarray(x0[j, :, :, 0]).tobytes()
            assert len(b) == IMG_BYTES
            assert SYNC[0] not in b, "pixel trùng byte đồng bộ — giao thức sai"
            img_bytes.append(b)
            crc_lg.append(zlib.crc32(np.asarray(lg[j], dtype="<i4").tobytes()) & 0xFFFFFFFF)
        preds.extend(int(v) for v in p)
    return img_bytes, np.asarray(preds), crc_lg, ey[:n], n


def read_line(ser, deadline):
    buf = bytearray()
    while time.time() < deadline:
        c = ser.read(1)
        if not c:
            continue
        if c == b"\n":
            return buf.decode("ascii", "replace").strip()
        if c != b"\r":
            buf += c
    return None


def one_image(ser, data, timeout):
    """Gửi một khung, trả về dict phản hồi (hoặc None nếu quá hạn)."""
    frame = SYNC + data
    for off in range(0, len(frame), CHUNK):
        ser.write(frame[off:off + CHUNK])
    ser.flush()
    deadline = time.time() + timeout
    while True:
        ln = read_line(ser, deadline)
        if ln is None:
            return None
        if not ln.startswith("M1S10K,") or ln.startswith("M1S10K,hello"):
            continue
        f = ln.split(",")
        if len(f) != 12:
            continue
        try:
            return dict(idx=int(f[1]), pred=int(f[2]),
                        crc_img=int(f[3], 16), crc_lg=int(f[4], 16),
                        conv1=int(f[5]), pool1=int(f[6]), conv2=int(f[7]),
                        pool2=int(f[8]), dense=int(f[9]), tot=int(f[10]),
                        instret=int(f[11]), raw=ln)
        except ValueError:
            continue


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", default="/dev/cu.usbserial-20250303171")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--n", type=int, default=10000)
    ap.add_argument("--variant", default="A-V1+DOT4+C1")
    ap.add_argument("--csv", default=None)
    ap.add_argument("--log", default=None)
    ap.add_argument("--timeout", type=float, default=5.0)
    ap.add_argument("--retry", type=int, default=3)
    ap.add_argument("--drain", type=float, default=2.0)
    ap.add_argument("--export", default=None, help="chỉ ghi ảnh int8 ra file nhị phân (cho Verilator)")
    ap.add_argument("--progress", type=int, default=250)
    args = ap.parse_args()

    print(f"nạp dữ liệu golden cho {args.n} ảnh...", flush=True)
    img_bytes, g_pred, g_crc, labels, n = load_golden(args.n)
    print(f"  xong: {n} ảnh · golden acc = {(g_pred == labels[:n]).mean()*100:.2f}%", flush=True)

    if args.export:
        with open(args.export, "wb") as f:
            for b in img_bytes:
                f.write(b)
        print(f"đã ghi {n} ảnh ({n*IMG_BYTES} byte) vào {args.export}")
        return 0

    import serial
    rows = []
    FIELDS = ["idx", "kit_idx", "label", "pred", "pred_golden", "crc_logit_ok",
              "crc_img_ok", "conv1", "pool1", "conv2", "pool2", "dense", "tot", "instret"]
    wcsv = None
    if args.csv:
        os.makedirs(os.path.dirname(args.csv) or ".", exist_ok=True)
        fcsv = open(args.csv, "w", newline="")
        wcsv = csv.DictWriter(fcsv, fieldnames=FIELDS)
        wcsv.writeheader()
    n_pred_ok = n_lab_ok = n_crc_lg_ok = n_crc_img_bad = n_retry = n_fail = 0
    t_start = time.time()
    with serial.Serial(args.port, args.baud, timeout=0.2) as ser:
        if args.drain > 0:
            t = time.time() + args.drain
            while time.time() < t:
                ser.read(4096)
        ser.reset_input_buffer()

        for i in range(n):
            r = None
            for attempt in range(args.retry):
                r = one_image(ser, img_bytes[i], args.timeout)
                if r is None:
                    n_retry += 1
                    ser.reset_input_buffer()
                    continue
                if r["crc_img"] != (zlib.crc32(img_bytes[i]) & 0xFFFFFFFF):
                    n_crc_img_bad += 1
                    n_retry += 1
                    ser.reset_input_buffer()
                    r = None
                    continue
                break
            if r is None:
                n_fail += 1
                print(f"  LỖI ảnh {i}: không nhận được khung đúng sau {args.retry} lần", flush=True)
                continue

            crc_ok = int(r["crc_lg"] == g_crc[i])
            pred_ok = int(r["pred"] == int(g_pred[i]))
            lab_ok = int(r["pred"] == int(labels[i]))
            n_crc_lg_ok += crc_ok
            n_pred_ok += pred_ok
            n_lab_ok += lab_ok
            rows.append(dict(idx=i, kit_idx=r["idx"], label=int(labels[i]),
                             pred=r["pred"], pred_golden=int(g_pred[i]),
                             crc_logit_ok=crc_ok, crc_img_ok=1,
                             conv1=r["conv1"], pool1=r["pool1"], conv2=r["conv2"],
                             pool2=r["pool2"], dense=r["dense"], tot=r["tot"],
                             instret=r["instret"]))
            if wcsv:
                wcsv.writerow(rows[-1])
                fcsv.flush()
            if not crc_ok:
                print(f"  CRC LOGIT LỆCH ở ảnh {i}: kit={r['crc_lg']:08X} golden={g_crc[i]:08X}", flush=True)

            done = i + 1
            if args.progress and done % args.progress == 0:
                el = time.time() - t_start
                eta = el / done * (n - done)
                print(f"  {done}/{n} · acc kit {n_lab_ok/done*100:.2f}% · "
                      f"khớp golden {n_pred_ok}/{done} · crc logit {n_crc_lg_ok}/{done} · "
                      f"còn ~{eta/60:.1f} phút", flush=True)

    el = time.time() - t_start
    tots = [r["tot"] for r in rows]
    med = statistics.median(tots) if tots else 0
    out = []
    out.append(f"biến thể       : {args.variant}")
    out.append(f"số ảnh gửi     : {n}  ·  nhận đúng khung: {len(rows)}  ·  thất bại: {n_fail}")
    out.append(f"gửi lại        : {n_retry} lần (trong đó CRC ảnh lệch: {n_crc_img_bad})")
    out.append(f"CRC logit khớp : {n_crc_lg_ok}/{len(rows)}  ({n_crc_lg_ok/max(len(rows),1)*100:.2f}%)")
    out.append(f"khớp golden    : {n_pred_ok}/{len(rows)}")
    out.append(f"ĐỘ CHÍNH XÁC TRÊN KIT: {n_lab_ok}/{len(rows)} = {n_lab_ok/max(len(rows),1)*100:.2f}%")
    if tots:
        out.append(f"chu kỳ/ảnh     : trung vị {med:,.0f} · nhỏ nhất {min(tots):,} · "
                   f"lớn nhất {max(tots):,} · lệch {max(tots)-min(tots)}")
        out.append(f"               : {med/27e6*1000:.1f} ms @27 MHz · {med/192064:.2f} chu kỳ/MAC")
    out.append(f"thời gian chạy : {el/60:.1f} phút")
    ok = (n_fail == 0 and len(rows) == n and n_crc_lg_ok == len(rows) and n_pred_ok == len(rows))
    out.append(("M1S10K_PASS " if ok else "M1S10K_FAIL ") +
               f"n={len(rows)} acc={n_lab_ok/max(len(rows),1)*100:.2f}% "
               f"crc={n_crc_lg_ok}/{len(rows)} golden={n_pred_ok}/{len(rows)}")
    txt = "\n".join(out)
    print("\n" + txt, flush=True)

    if wcsv:
        fcsv.close()
        print(f"đã ghi {len(rows)} dòng vào {args.csv}")
    if args.log:
        os.makedirs(os.path.dirname(args.log) or ".", exist_ok=True)
        Path(args.log).write_text(txt + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
