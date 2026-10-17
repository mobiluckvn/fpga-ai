#!/usr/bin/env python3
"""F7 — sinh dữ liệu int8 và kết quả golden cho hai bài kernel.

Bài A — tích vô hướng int8:
    100 cặp vector int8 dài 1.024, tích vô hướng cộng dồn vào int32.
    GHI CHÚ SAI LỆCH SO VỚI KẾ HOẠCH: lưu rời 100 cặp cần 100*2*1024 = 204.800 byte,
    vượt RAM 64 KB. Thay vào đó lưu một "pool" POOL byte int8 và lấy 100 cặp CỬA SỔ
    khác offset trong pool. Vẫn là 100 phép tích vô hướng dài 1.024 trên dữ liệu khác
    nhau, nhưng chỉ tốn POOL byte. Offset tất định (xem off_a/off_b).

Bài B — một lớp Conv 3x3 giống conv1 của M1-S:
    ảnh 28x28 int8, 1 kênh vào, 8 kênh ra, trọng số int8, bias int32, ReLU trên int32,
    rồi requantize về int8 bằng (M0 int32, shift) kiểu gemmlowp:
        acc  = Σ img * w            (int32)
        acc += bias[oc]
        acc  = max(acc, 0)                      <- ReLU
        q    = rdiv_pot(sat_rdhmul(acc, M0), shift)
        out  = clamp(q, -128, 127)
    Hai hàm sat_rdhmul / rdiv_pot cài ĐÚNG như gemmlowp (xem bên dưới) và được cài lại
    y hệt trong C, nên kết quả khớp từng bit.
    Đầu ra 26x26x8 = 5.408 byte (không đệm biên, "valid").

Sinh ra `f7_data.h` và in CRC32 kỳ vọng của đầu ra từng bài.
"""
from __future__ import annotations

import argparse
import zlib
from pathlib import Path

import numpy as np

SEED = 0x5EED_F007
POOL = 8192          # byte int8 dùng chung cho bài A
NPAIR = 100
VLEN = 1024
IMG = 28
K = 3
OCH = 8
OUT = IMG - K + 1    # 26, không đệm biên
TARGET_MAX_OUT = 110  # chọn M0/shift sao cho acc lớn nhất ra khoảng giá trị này


# ---------- số học requantize, bản Python (phải khớp bản C từng bit) ----------
def s32(v: int) -> int:
    """Gói về int32 bù hai."""
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >> 31 else v


def sat_rdhmul(a: int, b: int) -> int:
    """SaturatingRoundingDoublingHighMul của gemmlowp."""
    if a == b == -(1 << 31):
        return (1 << 31) - 1
    ab = a * b
    nudge = (1 << 30) if ab >= 0 else (1 - (1 << 30))
    return s32((ab + nudge) >> 31)


def rdiv_pot(x: int, exp: int) -> int:
    """RoundingDivideByPOT của gemmlowp (làm tròn nửa lên xa 0)."""
    if exp == 0:
        return x
    mask = (1 << exp) - 1
    remainder = x & mask
    threshold = (mask >> 1) + (1 if x < 0 else 0)
    return (x >> exp) + (1 if remainder > threshold else 0)


def quantize_multiplier(real_m: float):
    """Tách hệ số thực (0,1) thành (M0 int32 trong [2^30, 2^31), shift >= 0)."""
    assert 0.0 < real_m < 1.0, real_m
    shift = 0
    m = real_m
    while m < 0.5:
        m *= 2.0
        shift += 1
    q = int(round(m * (1 << 31)))
    if q == (1 << 31):
        q //= 2
        shift -= 1
    return q, shift


# ---------- bài A ----------
def task_a(pool: np.ndarray):
    offs = []
    results = []
    span = POOL - VLEN
    for i in range(NPAIR):
        oa = (i * 71) % span
        ob = ((i * 131) + 3000) % span
        offs.append((oa, ob))
        a = pool[oa:oa + VLEN].astype(np.int32)
        b = pool[ob:ob + VLEN].astype(np.int32)
        acc = int(np.dot(a, b))          # |acc| <= 1024*128*128 = 16.777.216, vừa int32
        results.append(s32(acc))
    raw = b"".join((r & 0xFFFFFFFF).to_bytes(4, "little") for r in results)
    return offs, results, zlib.crc32(raw) & 0xFFFFFFFF


# ---------- bài B ----------
def task_b(img: np.ndarray, w: np.ndarray, bias: np.ndarray):
    # acc int32 cho mọi vị trí và kênh
    acc = np.zeros((OCH, OUT, OUT), dtype=np.int64)
    for oc in range(OCH):
        for ky in range(K):
            for kx in range(K):
                acc[oc] += (img[ky:ky + OUT, kx:kx + OUT].astype(np.int64)
                            * int(w[oc, ky, kx]))
    acc += bias.astype(np.int64)[:, None, None]
    acc = np.maximum(acc, 0)                       # ReLU trên int32
    max_acc = int(acc.max())
    real_m = TARGET_MAX_OUT / max_acc
    m0, shift = quantize_multiplier(real_m)

    out = np.zeros((OCH, OUT, OUT), dtype=np.int8)
    for oc in range(OCH):
        for y in range(OUT):
            for x in range(OUT):
                q = rdiv_pot(sat_rdhmul(int(acc[oc, y, x]), m0), shift)
                out[oc, y, x] = max(-128, min(127, q))
    # thứ tự byte: oc chậm nhất, rồi y, rồi x — đúng thứ tự firmware ghi
    raw = out.tobytes(order="C")
    return out, m0, shift, max_acc, zlib.crc32(raw) & 0xFFFFFFFF


def c_array(name: str, arr, ctype: str, per_line: int = 16) -> str:
    vals = [str(int(v)) for v in np.asarray(arr).reshape(-1)]
    lines = []
    for i in range(0, len(vals), per_line):
        lines.append("    " + ", ".join(vals[i:i + per_line]) + ",")
    return f"static const {ctype} {name}[{len(vals)}] = {{\n" + "\n".join(lines) + "\n};\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="f7_data.h")
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=SEED)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    pool = rng.integers(-128, 128, size=POOL, dtype=np.int16).astype(np.int8)
    img = rng.integers(-128, 128, size=(IMG, IMG), dtype=np.int16).astype(np.int8)
    w = rng.integers(-64, 65, size=(OCH, K, K), dtype=np.int16).astype(np.int8)
    bias = rng.integers(-4096, 4097, size=OCH, dtype=np.int32)

    offs, res_a, crc_a = task_a(pool)
    out_b, m0, shift, max_acc, crc_b = task_b(img, w, bias)

    hdr = f"""/* F7 — dữ liệu kernel int8, SINH TỰ ĐỘNG bởi scripts/gen_f7_data.py. KHÔNG sửa tay.
 *
 * seed = 0x{args.seed:08X}
 * Bài A: {NPAIR} cặp cửa sổ dài {VLEN} trong pool {POOL} byte  -> {NPAIR*VLEN} MAC
 * Bài B: Conv {K}x{K}, 1 -> {OCH} kênh, ảnh {IMG}x{IMG}, ra {OUT}x{OUT}x{OCH} -> {OUT*OUT*OCH*K*K} MAC
 *        requantize: M0 = {m0}, shift = {shift}  (acc lớn nhất sau ReLU = {max_acc})
 * CRC32 kỳ vọng: A = 0x{crc_a:08X}   B = 0x{crc_b:08X}
 */
#ifndef F7_DATA_H
#define F7_DATA_H

#define F7_POOL      {POOL}
#define F7_NPAIR     {NPAIR}
#define F7_VLEN      {VLEN}
#define F7_IMG       {IMG}
#define F7_K         {K}
#define F7_OCH       {OCH}
#define F7_OUT       {OUT}
#define F7_M0        {m0}
#define F7_SHIFT     {shift}
#define F7_CRC_A     0x{crc_a:08X}u
#define F7_CRC_B     0x{crc_b:08X}u
#define F7_MAC_A     {NPAIR*VLEN}
#define F7_MAC_B     {OUT*OUT*OCH*K*K}

{c_array("f7_pool", pool, "signed char", 24)}
/* offset của từng cặp trong pool: {{off_a, off_b}} */
{c_array("f7_off", np.array(offs, dtype=np.int32), "unsigned short", 16)}
{c_array("f7_img", img, "signed char", 28)}
{c_array("f7_w", w, "signed char", 9)}
{c_array("f7_bias", bias, "int", 8)}
#endif /* F7_DATA_H */
"""
    Path(args.out).write_text(hdr)

    if args.quiet:
        print(f"{crc_a:08X} {crc_b:08X}")
    else:
        print("# F7 gen_f7_data")
        print(f"file            : {args.out} ({len(hdr)} byte)")
        print(f"seed            : 0x{args.seed:08X}")
        print(f"Bài A           : {NPAIR} cặp x {VLEN} = {NPAIR*VLEN:,} MAC, pool {POOL} byte")
        print(f"  dot[0], dot[1]: {res_a[0]}, {res_a[1]}")
        print(f"  dot min/max   : {min(res_a)} / {max(res_a)}")
        print(f"  CRC32_A       : {crc_a:08X}")
        print(f"Bài B           : Conv {K}x{K} 1->{OCH} kênh, {IMG}x{IMG} -> {OUT}x{OUT}x{OCH}"
              f" = {OUT*OUT*OCH*K*K:,} MAC")
        print(f"  acc max (ReLU): {max_acc}")
        print(f"  M0, shift     : {m0}, {shift}")
        print(f"  out min/max   : {int(out_b.min())} / {int(out_b.max())}")
        print(f"  CRC32_B       : {crc_b:08X}")
        print(f"Dữ liệu tĩnh    : pool {POOL} + ảnh {IMG*IMG} + w {OCH*K*K} + bias {OCH*4}"
              f" + off {NPAIR*4} = {POOL + IMG*IMG + OCH*K*K + OCH*4 + NPAIR*4:,} byte")
        print(f"Đệm đầu ra (.bss): {OUT*OUT*OCH:,} byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
