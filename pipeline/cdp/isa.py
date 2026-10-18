"""Giải mã trường lệnh RV32IM — dùng cho phân tích TĨNH.

Phân tích động (ISS) biết mỗi lệnh chạy bao nhiêu lần; phân tích tĩnh cần biết mỗi
lệnh **đọc/ghi thanh ghi nào**, và điều đó phụ thuộc dạng lệnh: bit [24:20] là `rs2`
ở dạng R/S/B nhưng là phần immediate ở dạng I; bit [11:7] là `rd` ở dạng R/I/U/J
nhưng là phần immediate ở dạng S/B. Nhầm chỗ này đã gây một lỗi thật ở S3 (xem
docs/LOG.md: trường `rd` của `store`).
"""
from __future__ import annotations

# opcode -> dạng lệnh
FORMAT = {
    0x37: "U", 0x17: "U",                      # lui, auipc
    0x6F: "J",                                 # jal
    0x67: "I", 0x03: "I", 0x13: "I", 0x73: "I", 0x0F: "I",   # jalr, load, op-imm, system, fence
    0x23: "S",                                 # store
    0x63: "B",                                 # branch
    0x33: "R", 0x0B: "R",                      # op, custom-0
}
WRITES_RD = {"R", "I", "U", "J"}
READS_RS1 = {"R", "I", "S", "B"}
READS_RS2 = {"R", "S", "B"}


def fields(instr: int) -> dict:
    op = instr & 0x7F
    fmt = FORMAT.get(op)
    f3 = (instr >> 12) & 7
    out = {
        "op": op, "fmt": fmt, "f3": f3, "f7": instr >> 25,
        "rd": (instr >> 7) & 0x1F if fmt in WRITES_RD else None,
        "rs1": (instr >> 15) & 0x1F if fmt in READS_RS1 else None,
        "rs2": (instr >> 20) & 0x1F if fmt in READS_RS2 else None,
    }
    # lui/auipc không đọc thanh ghi nào; jal cũng vậy; fence là nop
    if op in (0x37, 0x17, 0x6F) or op == 0x0F:
        out["rs1"] = out["rs2"] = None
    if op == 0x73 and f3 == 0:                 # ecall/ebreak
        out["rd"] = out["rs1"] = None
    if out["rd"] == 0:                         # ghi x0 = không ghi gì
        out["rd"] = None
    return out


def reads(instr: int) -> list[int]:
    f = fields(instr)
    return [r for r in (f["rs1"], f["rs2"]) if r is not None and r != 0]


def writes(instr: int) -> int | None:
    return fields(instr)["rd"]


def is_mem(instr: int) -> str | None:
    op = instr & 0x7F
    return "load" if op == 0x03 else ("store" if op == 0x23 else None)


def is_branch(instr: int) -> bool:
    return (instr & 0x7F) == 0x63


# ---------------- không gian mã lệnh ----------------
# Bảy opcode "custom" và opcode chuẩn mà RV32IM đã dùng (RISC-V spec, bảng opcode-map).
RV32IM_OPCODES = {
    0x03: "LOAD", 0x0F: "MISC-MEM", 0x13: "OP-IMM", 0x17: "AUIPC", 0x1B: "OP-IMM-32",
    0x23: "STORE", 0x2F: "AMO", 0x33: "OP", 0x37: "LUI", 0x3B: "OP-32",
    0x63: "BRANCH", 0x67: "JALR", 0x6F: "JAL", 0x73: "SYSTEM",
}
CUSTOM_OPCODES = {0x0B: "custom-0", 0x2B: "custom-1", 0x5B: "custom-2", 0x7B: "custom-3"}
