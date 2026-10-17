#!/usr/bin/env python3
"""Chuyển file .bin thành file hex từ 32 bit cho $readmemh.

Mỗi dòng một từ 32 bit, 8 chữ số hex, thứ tự byte LITTLE-ENDIAN (đúng như RISC-V
đọc từ bộ nhớ). Đệm 0 cho đủ số từ nếu cần.

Dùng: bin2hex.py <in.bin> <out.hex> [--words N]
"""
from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("inp")
    ap.add_argument("out")
    ap.add_argument("--words", type=int, default=None,
                    help="đệm 0 cho đủ N từ (mặc định: chỉ ghi phần có dữ liệu)")
    args = ap.parse_args()

    data = Path(args.inp).read_bytes()
    if len(data) % 4:
        data += b"\x00" * (4 - len(data) % 4)
    words = [int.from_bytes(data[i:i + 4], "little") for i in range(0, len(data), 4)]
    if args.words:
        if len(words) > args.words:
            raise SystemExit(f"LỖI: firmware {len(words)} từ > RAM {args.words} từ")
        words += [0] * (args.words - len(words))
    Path(args.out).write_text("".join(f"{w:08x}\n" for w in words))
    print(f"{args.inp} -> {args.out}: {len(data)} byte, {len(words)} từ 32 bit")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
