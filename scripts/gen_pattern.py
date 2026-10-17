#!/usr/bin/env python3
"""F3 — sinh mẫu 64 KB cho BSRAM và in CRC32 kỳ vọng.

Sinh `pattern.hex`: 16.384 từ 32 bit (= 65.536 byte = 64 KB), mỗi dòng một từ dạng
8 chữ số hex, để `$readmemh` đọc trực tiếp.

Nguồn số: LFSR Fibonacci 32 bit, đa thức x^32 + x^22 + x^2 + x^1 + 1
(phản hồi = bit31 ^ bit21 ^ bit1 ^ bit0), hạt giống cố định → tái lập được.

In hai CRC32 kỳ vọng (chuẩn zlib: đa thức phản chiếu 0xEDB88320, khởi tạo 0xFFFFFFFF,
đảo bit cuối), tính trên dòng byte theo **thứ tự little-endian của từng từ**:
  ROM = CRC32 của chính mẫu trong pattern.hex
  RW  = CRC32 của mẫu thứ hai mà phần cứng tự ghi: data2(a) = (a ^ 0xA5A5A5A5) với a là
        địa chỉ 14 bit mở rộng 0 lên 32 bit.
"""
from __future__ import annotations

import argparse
import zlib
from pathlib import Path

WORDS = 16384          # 16384 * 4 byte = 64 KB
SEED = 0xACE12345
MASK2 = 0xA5A5A5A5


def lfsr_words(n: int, seed: int = SEED):
    s = seed & 0xFFFFFFFF
    for _ in range(n):
        yield s
        fb = ((s >> 31) ^ (s >> 21) ^ (s >> 1) ^ s) & 1
        s = ((s << 1) | fb) & 0xFFFFFFFF


def to_bytes_le(words) -> bytes:
    out = bytearray()
    for w in words:
        out += w.to_bytes(4, "little")
    return bytes(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="pattern.hex", help="file hex sẽ ghi")
    ap.add_argument("--words", type=int, default=WORDS)
    ap.add_argument("--seed", type=lambda s: int(s, 0), default=SEED,
                    help="hạt giống LFSR (dùng để làm phép phản chứng)")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    rom = list(lfsr_words(args.words, args.seed))
    rw = [(a ^ MASK2) & 0xFFFFFFFF for a in range(args.words)]

    path = Path(args.out)
    path.write_text("".join(f"{w:08x}\n" for w in rom))

    crc_rom = zlib.crc32(to_bytes_le(rom)) & 0xFFFFFFFF
    crc_rw = zlib.crc32(to_bytes_le(rw)) & 0xFFFFFFFF

    if not args.quiet:
        print(f"# F3 gen_pattern")
        print(f"file            : {path} ({args.words} từ 32 bit = {args.words*4} byte)")
        print(f"LFSR seed       : 0x{args.seed:08X}, đa thức x^32+x^22+x^2+x^1+1")
        print(f"mẫu thứ hai     : data2(a) = (a ^ 0x{MASK2:08X})")
        print(f"từ đầu / cuối   : {rom[0]:08x} ... {rom[-1]:08x}")
        print(f"CRC32_ROM_EXPECT: {crc_rom:08X}")
        print(f"CRC32_RW_EXPECT : {crc_rw:08X}")
    else:
        print(f"{crc_rom:08X} {crc_rw:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
