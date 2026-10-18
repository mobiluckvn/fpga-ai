"""Lệnh tùy biến PMAX4 — ứng viên do S5 sinh ra (4/6 lần chạy AI mù đề xuất).

Đây là **mô hình tham chiếu duy nhất** cho ngữ nghĩa PMAX4: ISS dùng nó để chạy, và
RTL phải khớp với nó trên vector ngẫu nhiên (SPEC 4.3 điều 1).

    custom-0 (opcode 0001011), funct3 = 010, funct7 = 0000000
    rd[i] = max( (int8)rs1[i], (int8)rs2[i] )   cho i = 0..3   (bốn làn 8 bit)

Dùng cho max-pooling: bố cục activation là channels-last nên **4 kênh liền địa chỉ**
gói đúng vào một từ 32 bit; mỗi lệnh lấy max cho 4 kênh một lượt. Phép toán không đổi
giá trị nào so với mã C (`a > b ? a : b` trên int8), nên CRC phải khớp golden y nguyên.

Vì sao max CÓ DẤU: activation int8 sau requantize nằm trong [0,127] ở mạng này, nhưng
lệnh định nghĩa trên int8 có dấu để đúng về mặt tập lệnh và dùng lại được cho mô hình
khác có activation âm.
"""
from __future__ import annotations

NAME = "pmax4"
OPCODE = 0x0B          # custom-0
FUNCT3 = 0b010
FUNCT7 = 0b0000000
TIMING_KEY = "custom_pmax4"


def _s8(b: int) -> int:
    return b - 256 if b & 0x80 else b


def sem(rs1: int, rs2: int, state=None):
    out = 0
    for i in range(4):
        a = _s8((rs1 >> (8 * i)) & 0xFF)
        b = _s8((rs2 >> (8 * i)) & 0xFF)
        m = a if a > b else b
        out |= (m & 0xFF) << (8 * i)
    return out & 0xFFFFFFFF, state
