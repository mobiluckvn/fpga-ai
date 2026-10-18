"""Lệnh tùy biến DOT4 — ngữ nghĩa LẤY ĐÚNG TỪ RTL.

Nguồn: rtl/mycore/mycore.v (khối "lệnh tùy biến DOT4") và rtl/ext/pcpi_dot4.v.
Mã hoá giống nhánh A để dùng được đúng firmware đó:
    custom-0 (opcode 0001011), funct3 = 000, funct7 = 0000000
    rd = sum_{i=0..3} (int8)rs1[i] * (int8)rs2[i]          (mở rộng dấu lên 32 bit)

File này là **mô hình tham chiếu duy nhất** cho ngữ nghĩa DOT4: ISS dùng nó để chạy,
và `cdp verify` dùng chính nó để kiểm RTL bằng vector ngẫu nhiên (SPEC 2.1).
"""
from __future__ import annotations

NAME = "dot4"
OPCODE = 0x0B          # custom-0
FUNCT3 = 0b000
FUNCT7 = 0b0000000
TIMING_KEY = "custom_dot4"


def _s8(b: int) -> int:
    return b - 256 if b & 0x80 else b


def sem(rs1: int, rs2: int, state=None):
    """rd = tổng 4 tích int8 x int8. rs1, rs2 là số 32 bit không dấu."""
    acc = 0
    for i in range(4):
        acc += _s8((rs1 >> (8 * i)) & 0xFF) * _s8((rs2 >> (8 * i)) & 0xFF)
    return acc & 0xFFFFFFFF, state
