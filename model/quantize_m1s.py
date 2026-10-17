#!/usr/bin/env python3
"""Lượng tử hoá M1-S về int8, đo độ chính xác, xuất weights.h + ảnh thử + golden.

Các bước:
  1. Nạp trọng số float (model/m1s_float.npz) và MNIST.
  2. Hiệu chuẩn: chạy mô hình float trên CAL ảnh train, lấy max|activation| sau ReLU
     của từng lớp -> thang đo S_out của lớp đó.
  3. Lượng tử hoá đối xứng (zero-point = 0): trọng số int8, bias int32,
     cặp (M0, shift) cho mỗi lớp conv.
  4. Chạy golden int8 (model/golden_m1s.py — đúng từng bit với firmware) trên toàn bộ
     10.000 ảnh test, in độ chính xác int8 và so với float.
  5. Xuất:
       fw/weights.h   — trọng số int8/bias int32/M0/shift + NIMG ảnh thử + nhãn
                        + CRC32 golden của từng lớp cho từng ảnh thử
       model/m1s_int8.npz — cùng dữ liệu, dạng numpy, để các script khác dùng lại
"""
from __future__ import annotations

import argparse
import zlib
from pathlib import Path

import numpy as np

import golden_m1s as G
import mnist

HERE = Path(__file__).resolve().parent


def relu(x):
    return np.maximum(x, 0.0)


def float_forward(x, w1, b1, w2, b2, w3, b3):
    """Chạy mô hình float bằng numpy, trả về các activation sau ReLU + logits."""
    n = x.shape[0]
    # conv1: valid, 1 -> 8
    a1 = np.zeros((n, 8, 26, 26), dtype=np.float64)
    for oc in range(8):
        for ky in range(3):
            for kx in range(3):
                a1[:, oc] += x[:, ky:ky + 26, kx:kx + 26] * w1[oc, 0, ky, kx]
        a1[:, oc] += b1[oc]
    a1 = relu(a1)
    p1 = a1.reshape(n, 8, 13, 2, 13, 2).max(axis=(3, 5))
    # conv2: valid, 8 -> 16
    a2 = np.zeros((n, 16, 11, 11), dtype=np.float64)
    for oc in range(16):
        for ic in range(8):
            for ky in range(3):
                for kx in range(3):
                    a2[:, oc] += p1[:, ic, ky:ky + 11, kx:kx + 11] * w2[oc, ic, ky, kx]
        a2[:, oc] += b2[oc]
    a2 = relu(a2)
    p2 = a2[:, :, :10, :10].reshape(n, 16, 5, 2, 5, 2).max(axis=(3, 5))
    flat = p2.reshape(n, -1)
    logit = flat @ w3.T + b3
    return a1, p1, a2, p2, logit


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--float", default=str(HERE / "m1s_float.npz"))
    ap.add_argument("--cal", type=int, default=512, help="số ảnh dùng hiệu chuẩn")
    ap.add_argument("--nimg", type=int, default=10, help="số ảnh thử nhúng vào firmware")
    ap.add_argument("--ntest", type=int, default=10000, help="số ảnh để đo độ chính xác int8")
    ap.add_argument("--header", default=str(HERE.parent / "fw" / "weights.h"))
    ap.add_argument("--npz", default=str(HERE / "m1s_int8.npz"))
    args = ap.parse_args()

    d = np.load(args.float)
    w1f, b1f = d["w1"].astype(np.float64), d["b1"].astype(np.float64)
    w2f, b2f = d["w2"].astype(np.float64), d["b2"].astype(np.float64)
    w3f, b3f = d["w3"].astype(np.float64), d["b3"].astype(np.float64)
    float_acc = float(d["float_acc"])

    tx, ty, ex, ey = mnist.load()
    print("# Lượng tử hoá M1-S")
    print(f"độ chính xác float (từ lúc huấn luyện): {float_acc*100:.2f}%")

    # ---------- 1. hiệu chuẩn trên ảnh đã lượng tử hoá đầu vào ----------
    # Dùng chính thang đo của đầu vào int8 để hiệu chuẩn, nên activation float ở đây
    # tương thích với đường int8.
    S0 = 1.0 / 127.0
    cal_u8 = tx[:args.cal]
    cal_q = G.quant_images(cal_u8)[:, :, :, 0].astype(np.float64)   # [N,28,28] 0..127
    cal_x = cal_q * S0                                                          # về thang thực
    a1, p1, a2, p2, logit = float_forward(cal_x, w1f, b1f, w2f, b2f, w3f, b3f)
    max_a1 = float(a1.max())
    max_a2 = float(a2.max())
    print(f"hiệu chuẩn trên {args.cal} ảnh: max a1 = {max_a1:.4f}, max a2 = {max_a2:.4f}")

    # ---------- 2. lượng tử hoá ----------
    Sw1 = float(np.abs(w1f).max()) / 127.0
    Sw2 = float(np.abs(w2f).max()) / 127.0
    Sw3 = float(np.abs(w3f).max()) / 127.0
    S1 = max_a1 / 127.0          # thang đầu ra lớp 1
    S2 = max_a2 / 127.0          # thang đầu ra lớp 2

    # torch cho [Cout,Cin,ky,kx]; golden/firmware dùng channels-last [Cout,ky,kx,Cin]
    w1q = np.clip(np.rint(w1f / Sw1), -127, 127).astype(np.int8).transpose(0, 2, 3, 1).copy()
    w2q = np.clip(np.rint(w2f / Sw2), -127, 127).astype(np.int8).transpose(0, 2, 3, 1).copy()
    # Dense: torch làm phẳng theo (C,H,W); ta làm phẳng theo (H,W,C) nên phải hoán vị cột
    w3q = np.clip(np.rint(w3f / Sw3), -127, 127).astype(np.int8)
    w3q = (w3q.reshape(G.NCLS, G.C2, G.POOL2, G.POOL2)
               .transpose(0, 2, 3, 1)
               .reshape(G.NCLS, G.NFLAT).copy())
    b1q = np.rint(b1f / (S0 * Sw1)).astype(np.int64)
    b2q = np.rint(b2f / (S1 * Sw2)).astype(np.int64)
    b3q = np.rint(b3f / (S2 * Sw3)).astype(np.int64)
    for name, b in (("b1", b1q), ("b2", b2q), ("b3", b3q)):
        if np.abs(b).max() >= 2**31:
            raise SystemExit(f"LỖI: {name} vượt int32 ({np.abs(b).max()})")
    b1q, b2q, b3q = (b.astype(np.int32) for b in (b1q, b2q, b3q))

    m0_1, sh_1 = G.quantize_multiplier((S0 * Sw1) / S1)
    m0_2, sh_2 = G.quantize_multiplier((S1 * Sw2) / S2)
    print(f"thang đo   : S0={S0:.6g} Sw1={Sw1:.6g} S1={S1:.6g} Sw2={Sw2:.6g} S2={S2:.6g} Sw3={Sw3:.6g}")
    print(f"requantize: lớp1 M0={m0_1} shift={sh_1}  ·  lớp2 M0={m0_2} shift={sh_2}")

    q = dict(w1=w1q, b1=b1q, w2=w2q, b2=b2q, w3=w3q, b3=b3q,
             m0_1=m0_1, sh_1=sh_1, m0_2=m0_2, sh_2=sh_2)

    # ---------- 3. độ chính xác int8 trên tập test ----------
    n = min(args.ntest, len(ex))
    print(f"đang chạy golden int8 trên {n} ảnh test...")
    ok = 0
    preds = np.zeros(n, dtype=np.int8)
    for i in range(n):
        p, _ = G.infer(ex[i], q)
        preds[i] = p
        ok += int(p == ey[i])
        if (i + 1) % 2000 == 0:
            print(f"  {i+1}/{n}  acc tạm {ok/(i+1)*100:.2f}%")
    int8_acc = ok / n
    print(f"\nĐộ chính xác int8 ({n} ảnh): {int8_acc*100:.2f}%")
    print(f"Độ chính xác float            : {float_acc*100:.2f}%")
    delta = (float_acc - int8_acc) * 100
    print(f"Chênh                     : {delta:+.2f} điểm %  "
          f"(tiêu chí kế hoạch: không quá 1 điểm %) -> "
          f"{'ĐẠT' if delta <= 1.0 else 'KHÔNG ĐẠT'}")

    # ---------- 4. ảnh thử + CRC32 golden từng lớp ----------
    img_idx = list(range(args.nimg))
    imgs_q = []
    crc_rows = []
    for i in img_idx:
        pred, logit_i, L = G.infer(ex[i], q, want_layers=True)
        imgs_q.append(L["x0"][:, :, 0])
        crc_rows.append(dict(
            idx=i, label=int(ey[i]), pred=pred,
            crc_a1=zlib.crc32(np.ascontiguousarray(L["a1"]).tobytes()) & 0xFFFFFFFF,
            crc_p1=zlib.crc32(np.ascontiguousarray(L["p1"]).tobytes()) & 0xFFFFFFFF,
            crc_a2=zlib.crc32(np.ascontiguousarray(L["a2"]).tobytes()) & 0xFFFFFFFF,
            crc_p2=zlib.crc32(np.ascontiguousarray(L["p2"]).tobytes()) & 0xFFFFFFFF,
            crc_lg=zlib.crc32(np.asarray(logit_i, dtype="<i4").tobytes()) & 0xFFFFFFFF,
        ))
    print(f"\n{args.nimg} ảnh thử nhúng vào firmware:")
    for r in crc_rows:
        print(f"  ảnh {r['idx']:2d}  nhãn {r['label']}  dự đoán {r['pred']}  "
              f"crc a1={r['crc_a1']:08X} p1={r['crc_p1']:08X} a2={r['crc_a2']:08X} "
              f"p2={r['crc_p2']:08X} logit={r['crc_lg']:08X}")

    # ---------- 5. xuất ----------
    np.savez(args.npz, **{k: v for k, v in q.items()},
             imgs=np.stack(imgs_q), labels=ey[:args.nimg],
             preds=np.array([r["pred"] for r in crc_rows], dtype=np.int8),
             int8_acc=np.float64(int8_acc), float_acc=np.float64(float_acc),
             S0=S0, Sw1=Sw1, S1=S1, Sw2=Sw2, S2=S2, Sw3=Sw3)
    write_header(args.header, q, np.stack(imgs_q), ey[:args.nimg], crc_rows,
                 int8_acc, float_acc)
    print(f"\nĐã lưu {args.npz}\nĐã lưu {args.header}")
    return 0


def c_arr(name, arr, ctype, per_line):
    """Mọi mảng đều thẳng hàng 4 byte: lệnh DOT4 nạp 4 byte một lần bằng `lw`."""
    vals = [str(int(v)) for v in np.asarray(arr).reshape(-1)]
    lines = ["    " + ", ".join(vals[i:i + per_line]) + ","
             for i in range(0, len(vals), per_line)]
    return (f"static const {ctype} {name}[{len(vals)}] __attribute__((aligned(4))) = {{\n"
            + "\n".join(lines) + "\n};\n")


def write_header(path, q, imgs, labels, crc_rows, int8_acc, float_acc):
    n = len(imgs)
    hdr = f"""/* M1-S int8 — SINH TỰ ĐỘNG bởi model/quantize_m1s.py. KHÔNG sửa tay.
 *
 * Kiến trúc (đầu vào 28x28x1 int8, không đệm biên):
 *   Conv 3x3 1->8  + bias + ReLU + requantize -> 26x26x8   48.672 MAC
 *   MaxPool 2x2                               -> 13x13x8
 *   Conv 3x3 8->16 + bias + ReLU + requantize -> 11x11x16  139.392 MAC
 *   MaxPool 2x2                               ->  5x5x16
 *   Dense 400->10 + bias (giữ int32, argmax)  -> 10          4.000 MAC
 *                                               tổng       192.064 MAC
 *
 * Độ chính xác: float {float_acc*100:.2f}% · int8 {int8_acc*100:.2f}% (10.000 ảnh test MNIST)
 * Lượng tử hoá đối xứng, zero-point = 0. requantize kiểu gemmlowp (M0, shift).
 *
 * BỐ CỤC: channels-last. Activation [H][W][C], trọng số conv [Cout][ky][kx][Cin],
 * dense làm phẳng theo (H,W,C) nên m1s_w3 đã được HOÁN VỊ CỘT so với PyTorch.
 * Lý do: lệnh DOT4 cộng dồn 4 cặp int8 liền địa chỉ và cần thẳng hàng 4 byte.
 * Mọi CRC32 golden dưới đây tính trên đúng bố cục này.
 */
#ifndef WEIGHTS_H
#define WEIGHTS_H

#define M1S_IMG     28
#define M1S_C1      8
#define M1S_OUT1    26
#define M1S_POOL1   13
#define M1S_C2      16
#define M1S_OUT2    11
#define M1S_POOL2   5
#define M1S_NCLS    10
#define M1S_M0_1    {q['m0_1']}
#define M1S_SH_1    {q['sh_1']}
#define M1S_M0_2    {q['m0_2']}
#define M1S_SH_2    {q['sh_2']}
#define M1S_NIMG    {n}
#define M1S_MAC     192064

{c_arr("m1s_w1", q["w1"], "signed char", 9)}
{c_arr("m1s_b1", q["b1"], "int", 8)}
{c_arr("m1s_w2", q["w2"], "signed char", 18)}
{c_arr("m1s_b2", q["b2"], "int", 8)}
{c_arr("m1s_w3", q["w3"], "signed char", 20)}
{c_arr("m1s_b3", q["b3"], "int", 10)}
/* {n} ảnh thử, đã lượng tử hoá về int8 [0,127], thứ tự hàng trước */
{c_arr("m1s_imgs", imgs, "signed char", 28)}
{c_arr("m1s_labels", labels, "unsigned char", 16)}
{c_arr("m1s_pred_golden", [r['pred'] for r in crc_rows], "unsigned char", 16)}
/* CRC32 golden từng lớp cho từng ảnh thử: a1, p1, a2, p2, logit */
{c_arr("m1s_crc_a1", [r['crc_a1'] for r in crc_rows], "unsigned int", 4)}
{c_arr("m1s_crc_p1", [r['crc_p1'] for r in crc_rows], "unsigned int", 4)}
{c_arr("m1s_crc_a2", [r['crc_a2'] for r in crc_rows], "unsigned int", 4)}
{c_arr("m1s_crc_p2", [r['crc_p2'] for r in crc_rows], "unsigned int", 4)}
{c_arr("m1s_crc_logit", [r['crc_lg'] for r in crc_rows], "unsigned int", 4)}
#endif /* WEIGHTS_H */
"""
    Path(path).write_text(hdr)


if __name__ == "__main__":
    raise SystemExit(main())
