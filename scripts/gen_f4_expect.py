#!/usr/bin/env python3
"""F4 — tính giá trị tích luỹ kỳ vọng của bài kiểm khối nhân.

Phần cứng mỗi chu kỳ:
  - lấy hai từ 32 bit a, b từ hai LFSR (cùng đa thức với F3: x^32+x^22+x^2+x^1+1,
    phản hồi = bit31^bit21^bit1^bit0, bước: s <- {s[30:0], fb})
  - tính dot = Σ_{i=0..3} int8(a[8i+7:8i]) * int8(b[8i+7:8i])   (có dấu)
  - acc <- (acc + dot) mod 2^32
Chạy đúng N = 2^20 = 1.048.576 chu kỳ, dùng giá trị LFSR TRƯỚC khi bước (mẫu đầu = hạt giống).

In ACC_EXPECT dạng 8 chữ số hex (không dấu, bù hai).
"""
from __future__ import annotations

import argparse

SEED_A = 0x12345678
SEED_B = 0x9ABCDEF0
N = 1 << 20


def step(s: int) -> int:
    fb = ((s >> 31) ^ (s >> 21) ^ (s >> 1) ^ s) & 1
    return ((s << 1) | fb) & 0xFFFFFFFF


def s8(v: int) -> int:
    return v - 256 if v >= 128 else v


def dot4(a: int, b: int) -> int:
    t = 0
    for i in range(4):
        t += s8((a >> (8 * i)) & 0xFF) * s8((b >> (8 * i)) & 0xFF)
    return t


def accumulate(n: int = N, seed_a: int = SEED_A, seed_b: int = SEED_B):
    a, b = seed_a, seed_b
    acc = 0
    dmin, dmax = None, None
    for _ in range(n):
        d = dot4(a, b)
        acc = (acc + d) & 0xFFFFFFFF
        dmin = d if dmin is None or d < dmin else dmin
        dmax = d if dmax is None or d > dmax else dmax
        a = step(a)
        b = step(b)
    return acc, a, b, dmin, dmax


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--cycles", type=int, default=N)
    ap.add_argument("--seed-a", type=lambda s: int(s, 0), default=SEED_A)
    ap.add_argument("--seed-b", type=lambda s: int(s, 0), default=SEED_B)
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    acc, a_end, b_end, dmin, dmax = accumulate(args.cycles, args.seed_a, args.seed_b)
    if args.quiet:
        print(f"{acc:08X}")
    else:
        print("# F4 giá trị kỳ vọng")
        print(f"số chu kỳ      : {args.cycles} (= 2^{args.cycles.bit_length()-1})")
        print(f"hạt giống A/B  : 0x{args.seed_a:08X} / 0x{args.seed_b:08X}")
        print(f"LFSR cuối A/B  : 0x{a_end:08X} / 0x{b_end:08X}")
        print(f"dot nhỏ/lớn    : {dmin} / {dmax}  (biên lý thuyết ±4*128*128 = ±65536)")
        print(f"ACC_EXPECT     : {acc:08X}  ({acc} không dấu, "
              f"{acc - (1 << 32) if acc >> 31 else acc} có dấu)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
