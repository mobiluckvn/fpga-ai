"""Lệnh tùy biến REQ — ngữ nghĩa LẤY ĐÚNG TỪ RTL.

Nguồn: rtl/mycore/mycore.v (khối "lệnh tùy biến REQ (cổng B5)").
    custom-0 (opcode 0001011), funct3 = 001, funct7 = số bit dịch (hằng lúc biên dịch)
    rd = clamp( RoundingDivideByPOT( SatRoundingDoublingHighMul(ReLU(rs1), rs2), sh ), 0, 127 )

Đúng theo RTL từng bước (tên biến giữ nguyên để đối chiếu được):
    md_a    = rs1[31] ? 0 : rs1            (ReLU, làm ở S_EXEC)
    prod_u  = md_a * md_b                  (nhân KHÔNG DẤU 32x32 -> 64)
    req_t64 = prod_u + 0x4000_0000
    req_t   = req_t64[62:31]               (32 bit)
    req_q   = (req_t >> sh) + (1 nếu (req_t & mask) > (mask >> 1))
    req_val = min(req_q, 127)

Vì sao nhân KHÔNG DẤU là đủ (ghi chú trong RTL): ReLU đặt acc >= 0, còn m0 từ
quantize_multiplier luôn trong [2^30, 2^31) nên dương; hai toán hạng không âm thì
tích không dấu trùng tích có dấu.
"""
from __future__ import annotations

NAME = "req"
OPCODE = 0x0B          # custom-0
FUNCT3 = 0b001
FUNCT7 = None          # funct7 mang số bit dịch, không phải mã lệnh
TIMING_KEY = "custom_req"


def sem(rs1: int, rs2: int, state=None, sh: int = 0):
    md_a = 0 if (rs1 & 0x8000_0000) else rs1
    prod_u = (md_a * rs2) & 0xFFFF_FFFF_FFFF_FFFF
    req_t64 = (prod_u + 0x4000_0000) & 0xFFFF_FFFF_FFFF_FFFF
    req_t = (req_t64 >> 31) & 0xFFFF_FFFF
    mask = ((1 << sh) - 1) & 0xFFFF_FFFF
    rem = req_t & mask
    thr = mask >> 1
    q = ((req_t >> sh) + (1 if rem > thr else 0)) & 0xFFFF_FFFF
    return (127 if q > 127 else q), state
