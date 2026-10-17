#!/usr/bin/env python3
"""F8 — sinh dữ liệu cho bài A viết lại bằng DOT4, và CRC32 golden.

Dùng ĐÚNG pool của F7 (cùng seed, cùng module `gen_f7_data`), nhưng offset được
làm **thẳng hàng 4 byte** vì phiên bản DOT4 nạp dữ liệu bằng `lw` (4 byte một lần)
và lõi bật CATCH_MISALIGN nên truy cập lệch sẽ sinh trap.

Vì vậy CRC32 của bài A ở F8 khác CRC ở F7 (dữ liệu khác offset), nhưng:
  - trong cùng một lần chạy F8, bản vô hướng và bản DOT4 dùng CÙNG dữ liệu
    -> so sánh chu kỳ là công bằng tuyệt đối;
  - số chu kỳ của bản vô hướng không phụ thuộc offset (cùng số vòng, cùng mã)
    -> vẫn so sánh được với 4.921.446 chu kỳ của F7.

Sinh `f8_data.h` và in CRC32 kỳ vọng.
"""
from __future__ import annotations

import argparse
import importlib.util
import zlib
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent


def load_f7():
    spec = importlib.util.spec_from_file_location("gen_f7_data", HERE / "gen_f7_data.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def s32(v: int) -> int:
    v &= 0xFFFFFFFF
    return v - (1 << 32) if v >> 31 else v


def c_array(name: str, arr, ctype: str, per_line: int, attr: str = "") -> str:
    vals = [str(int(v)) for v in np.asarray(arr).reshape(-1)]
    lines = []
    for i in range(0, len(vals), per_line):
        lines.append("    " + ", ".join(vals[i:i + per_line]) + ",")
    return (f"static const {ctype} {name}[{len(vals)}]{attr} = {{\n"
            + "\n".join(lines) + "\n};\n")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default="f8_data.h")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    f7 = load_f7()
    rng = np.random.default_rng(f7.SEED)
    pool = rng.integers(-128, 128, size=f7.POOL, dtype=np.int16).astype(np.int8)
    # (các mảng sau của F7 không dùng ở F8, nhưng phải rút cùng thứ tự để pool giống hệt)

    span = f7.POOL - f7.VLEN
    offs = []
    results = []
    for i in range(f7.NPAIR):
        oa = ((i * 71) % span) & ~3          # thẳng hàng 4 byte
        ob = (((i * 131) + 3000) % span) & ~3
        offs.append((oa, ob))
        a = pool[oa:oa + f7.VLEN].astype(np.int32)
        b = pool[ob:ob + f7.VLEN].astype(np.int32)
        results.append(s32(int(np.dot(a, b))))

    raw = b"".join((r & 0xFFFFFFFF).to_bytes(4, "little") for r in results)
    crc = zlib.crc32(raw) & 0xFFFFFFFF

    hdr = f"""/* F8 — dữ liệu bài A (DOT4), SINH TỰ ĐỘNG bởi scripts/gen_f8_data.py. KHÔNG sửa tay.
 *
 * Pool giống hệt F7 (seed 0x{f7.SEED:08X}); offset được làm THẲNG HÀNG 4 BYTE để dùng `lw`.
 * {f7.NPAIR} cặp x {f7.VLEN} = {f7.NPAIR*f7.VLEN} MAC; mỗi cặp {f7.VLEN//4} lệnh DOT4
 * -> tổng {f7.NPAIR*f7.VLEN//4} lệnh DOT4.
 * CRC32 kỳ vọng của {f7.NPAIR} kết quả int32 (little-endian) = 0x{crc:08X}
 */
#ifndef F8_DATA_H
#define F8_DATA_H

#define F8_POOL      {f7.POOL}
#define F8_NPAIR     {f7.NPAIR}
#define F8_VLEN      {f7.VLEN}
#define F8_MAC_A     {f7.NPAIR*f7.VLEN}
#define F8_NDOT4     {f7.NPAIR*f7.VLEN//4}
#define F8_CRC_A     0x{crc:08X}u

{c_array("f8_pool", pool, "signed char", 24, " __attribute__((aligned(4)))")}
/* offset thẳng hàng 4 byte của từng cặp: {{off_a, off_b}} */
{c_array("f8_off", np.array(offs, dtype=np.int32), "unsigned short", 16)}
#endif /* F8_DATA_H */
"""
    Path(args.out).write_text(hdr)

    if args.quiet:
        print(f"{crc:08X}")
    else:
        print("# F8 gen_f8_data")
        print(f"file            : {args.out} ({len(hdr)} byte)")
        print(f"pool            : {f7.POOL} byte, seed 0x{f7.SEED:08X} (giống F7)")
        print(f"offset          : thẳng hàng 4 byte; cặp 0 = {offs[0]}, cặp 1 = {offs[1]}")
        print(f"MAC             : {f7.NPAIR*f7.VLEN:,}  ·  số lệnh DOT4 = {f7.NPAIR*f7.VLEN//4:,}")
        print(f"dot[0], dot[1]  : {results[0]}, {results[1]}")
        print(f"dot min/max     : {min(results)} / {max(results)}")
        print(f"CRC32_A         : {crc:08X}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
