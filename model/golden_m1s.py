#!/usr/bin/env python3
"""Golden int8 của M1-S — bản tham chiếu ĐÚNG TỪNG BIT với firmware trên kit.

BỐ CỤC DỮ LIỆU: channels-last, tức activation lưu theo thứ tự [H][W][C] và trọng số
theo [Cout][ky][kx][Cin]. Lý do: lệnh tùy biến DOT4 cộng dồn 4 cặp int8 liền nhau
trong bộ nhớ và **cần địa chỉ thẳng hàng 4 byte** (lõi bật CATCH_MISALIGN). Với
channels-last, 4 kênh vào liền nhau nằm liền địa chỉ, nên conv2 (Cin=8) dùng được
đúng 2 lệnh DOT4 cho mỗi vị trí kernel, không bỏ sót MAC nào.
Mọi CRC32 và thứ tự làm phẳng trong tài liệu này đều theo bố cục này.

Phép tính (giống hệt kernel C):

  conv:   acc  = Σ_{ky,kx,ic} x[y+ky][x+kx][ic] · w[oc][ky][kx][ic]      (int32)
          acc += b[oc]
          acc  = max(acc, 0)                                   <- ReLU trên int32
          out  = clamp(rdiv_pot(sat_rdhmul(acc, M0), shift), 0, 127)
  pool:   max 2x2 trên int8 (lấy sàn: 26->13, 11->5)
  dense:  acc = Σ x[i] · w[c][i] + b[c], giữ int32 rồi argmax (không requantize)

Lượng tử hoá đối xứng, zero-point = 0:
  đầu vào   x0 = round(pixel/255 · 127), clamp [0,127]        -> S0 = 1/127
  trọng số  Sw = max|W|/127
  bias      bq = round(B / (S_in·Sw))                          (int32)
  đầu ra    S_out từ hiệu chuẩn; M_real = (S_in·Sw)/S_out      -> (M0, shift)
"""
from __future__ import annotations

import numpy as np

IMG = 28
OUT1, POOL1, C1 = 26, 13, 8
OUT2, POOL2, C2 = 11, 5, 16
NCLS = 10
NFLAT = POOL2 * POOL2 * C2          # 400, theo thứ tự (H,W,C)


# ---------- số học requantize (khớp từng bit với C) ----------
def s32(v: int) -> int:
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
    """RoundingDivideByPOT của gemmlowp."""
    if exp == 0:
        return x
    mask = (1 << exp) - 1
    remainder = x & mask
    threshold = (mask >> 1) + (1 if x < 0 else 0)
    return (x >> exp) + (1 if remainder > threshold else 0)


def quantize_multiplier(real_m: float):
    """Hệ số thực trong (0,1) -> (M0 int32 trong [2^30, 2^31), shift >= 0)."""
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


def requant(acc: int, m0: int, shift: int) -> int:
    q = rdiv_pot(sat_rdhmul(acc, m0), shift)
    return 127 if q > 127 else (0 if q < 0 else q)


def requant_vec(acc: np.ndarray, m0: int, shift: int) -> np.ndarray:
    """Bản vector hoá của requant, CHỈ cho acc >= 0 (tức sau ReLU).

    Đúng từng bit với bản vô hướng trong trường hợp đó:
      - acc >= 0 nên ab = acc·M0 >= 0 -> nudge luôn là +2^30, không cần rẽ nhánh;
      - acc != INT32_MIN nên không rơi vào nhánh bão hoà của sat_rdhmul;
      - x >= 0 nên threshold của rdiv_pot là mask>>1, không +1.
    `test_requant_equiv()` kiểm hai bản khớp nhau trên dữ liệu ngẫu nhiên.
    """
    a = acc.astype(np.int64)
    assert a.min() >= 0, "requant_vec chỉ dùng cho acc >= 0"
    x = (a * np.int64(m0) + np.int64(1 << 30)) >> np.int64(31)
    if shift:
        mask = np.int64((1 << shift) - 1)
        rem = x & mask
        x = (x >> np.int64(shift)) + (rem > (mask >> np.int64(1))).astype(np.int64)
    return np.clip(x, 0, 127).astype(np.int8)


def test_requant_equiv(n: int = 20000, seed: int = 7) -> None:
    rng = np.random.default_rng(seed)
    for m0, shift in ((1936565777, 8), (1073741824, 0), (2147483647, 15),
                      (1138411053, 8), (1108363094, 8)):
        acc = rng.integers(0, 2 ** 30, size=n, dtype=np.int64)
        acc[:5] = [0, 1, 2 ** 30 - 1, 127, 2 ** 20]
        vec = requant_vec(acc, m0, shift)
        sca = np.array([requant(int(v), m0, shift) for v in acc], dtype=np.int8)
        assert np.array_equal(vec, sca), f"lệch ở M0={m0} shift={shift}"


# ---------- lượng tử hoá ảnh ----------
def quant_images(batch_u8: np.ndarray) -> np.ndarray:
    """uint8 [N,28,28] -> int8 [N,28,28,1] trong [0,127] (channels-last)."""
    q = np.rint(batch_u8.astype(np.float64) / 255.0 * 127.0)
    return np.clip(q, 0, 127).astype(np.int8)[:, :, :, None]


# ---------- các lớp, channels-last, theo lô ----------
def conv_relu_requant_b(x: np.ndarray, w: np.ndarray, b: np.ndarray,
                        m0: int, shift: int) -> np.ndarray:
    """x int8 [N,H,W,Cin], w int8 [Cout,3,3,Cin], b int32 [Cout]
       -> int8 [N,H-2,W-2,Cout].
    Cộng dồn trong int64; ở quy mô M1-S |acc| <= 9·8·127·127 < 2^24 nên không tràn int32.
    """
    n, h, wd, cin = x.shape
    cout = w.shape[0]
    oh, ow = h - 2, wd - 2
    acc = np.zeros((n, oh, ow, cout), dtype=np.int64)
    xi = x.astype(np.int64)
    for oc in range(cout):
        s = np.zeros((n, oh, ow), dtype=np.int64)
        for ky in range(3):
            for kx in range(3):
                for ic in range(cin):
                    k = int(w[oc, ky, kx, ic])
                    if k:
                        s += xi[:, ky:ky + oh, kx:kx + ow, ic] * k
        acc[:, :, :, oc] = s + int(b[oc])
    acc = np.maximum(acc, 0)                      # ReLU trên int32
    return requant_vec(acc, m0, shift)


def maxpool2_b(x: np.ndarray) -> np.ndarray:
    """int8 [N,H,W,C] -> int8 [N,H//2,W//2,C], lấy sàn."""
    n, h, w, c = x.shape
    oh, ow = h // 2, w // 2
    xs = x[:, :oh * 2, :ow * 2, :].reshape(n, oh, 2, ow, 2, c)
    return xs.max(axis=(2, 4)).astype(np.int8)


def dense_i32_b(x: np.ndarray, w: np.ndarray, b: np.ndarray) -> np.ndarray:
    """x int8 [N,400], w int8 [10,400], b int32 [10] -> int32 [N,10]."""
    return (x.astype(np.int64) @ w.astype(np.int64).T + b.astype(np.int64)[None, :])


def infer_batch(imgs_u8: np.ndarray, q: dict, want_layers: bool = False):
    """Suy luận lô ảnh uint8 [N,28,28]. Trả về (preds [N] int8, logits [N,10] int32)."""
    x0 = quant_images(imgs_u8)                                  # [N,28,28,1]
    a1 = conv_relu_requant_b(x0, q["w1"], q["b1"], q["m0_1"], q["sh_1"])   # [N,26,26,8]
    p1 = maxpool2_b(a1)                                                     # [N,13,13,8]
    a2 = conv_relu_requant_b(p1, q["w2"], q["b2"], q["m0_2"], q["sh_2"])   # [N,11,11,16]
    p2 = maxpool2_b(a2)                                                     # [N,5,5,16]
    flat = p2.reshape(p2.shape[0], -1)                          # (H,W,C) -> 400
    logit = dense_i32_b(flat, q["w3"], q["b3"])
    preds = np.argmax(logit, axis=1).astype(np.int8)
    if want_layers:
        return preds, logit, {"x0": x0, "a1": a1, "p1": p1, "a2": a2, "p2": p2}
    return preds, logit


def infer(img_u8: np.ndarray, q: dict, want_layers: bool = False):
    out = infer_batch(img_u8[None, ...], q, want_layers)
    if want_layers:
        preds, logit, L = out
        return int(preds[0]), logit[0], {k: v[0] for k, v in L.items()}
    preds, logit = out
    return int(preds[0]), logit[0]
