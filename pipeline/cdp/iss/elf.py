"""Đọc bảng ký hiệu ELF32 little-endian (đủ cho firmware RV32).

Chỉ cần symtab để gán mỗi địa chỉ lệnh về một HÀM — tầng 1 của profile 3 tầng
(docs/PIPELINE_SPEC.md mục 2.2). Không dùng thư viện ngoài.
"""
from __future__ import annotations

import struct
from pathlib import Path

STT_FUNC = 2


def _u(fmt, b, off):
    return struct.unpack_from("<" + fmt, b, off)


def symbols(path: Path) -> list[dict]:
    b = Path(path).read_bytes()
    if b[:4] != b"\x7fELF" or b[4] != 1:
        raise ValueError(f"{path}: không phải ELF32")
    e_shoff, = _u("I", b, 0x20)
    e_shentsize, e_shnum, e_shstrndx = _u("HHH", b, 0x2E)
    secs = []
    for i in range(e_shnum):
        o = e_shoff + i * e_shentsize
        name, typ, flags, addr, off, size, link, info, align, entsize = _u("IIIIIIIIII", b, o)
        secs.append(dict(name=name, type=typ, addr=addr, off=off, size=size,
                         link=link, entsize=entsize))
    shstr = secs[e_shstrndx]

    def sname(x):
        s = b.index(b"\0", shstr["off"] + x)
        return b[shstr["off"] + x:s].decode()

    out = []
    for s in secs:
        if s["type"] != 2:                     # SHT_SYMTAB
            continue
        strtab = secs[s["link"]]
        n = s["size"] // (s["entsize"] or 16)
        for i in range(n):
            o = s["off"] + i * s["entsize"]
            st_name, st_value, st_size, st_info, st_other, st_shndx = _u("IIIBBH", b, o)
            e = b.index(b"\0", strtab["off"] + st_name)
            nm = b[strtab["off"] + st_name:e].decode()
            if nm and (st_info & 0xF) == STT_FUNC and st_size:
                out.append({"name": nm, "addr": st_value, "size": st_size})
    out.sort(key=lambda d: d["addr"])
    return out


class FuncMap:
    """Tra địa chỉ lệnh -> tên hàm, bằng tìm nhị phân trên bảng ký hiệu."""

    def __init__(self, path: Path):
        self.syms = symbols(path)
        self.starts = [s["addr"] for s in self.syms]

    def of(self, pc: int) -> str:
        import bisect
        i = bisect.bisect_right(self.starts, pc) - 1
        if i < 0:
            return "?"
        s = self.syms[i]
        return s["name"] if pc < s["addr"] + s["size"] else "?"

    def names(self) -> list[str]:
        return [s["name"] for s in self.syms]
