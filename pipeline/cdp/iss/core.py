"""ISS — bộ mô phỏng tập lệnh RV32IM + MMIO của soc_b.v + mô hình chu kỳ theo lõi.

Mục đích: đếm $n_c$ (số lệnh động theo lớp) để nuôi mô hình chi phí
$C=\\sum n_c\\lambda_c$ (docs/MO_HINH_CHI_PHI.md). Số chu kỳ do mô hình tính, KHÔNG
phải do mô phỏng RTL — và vì vậy phải được kiểm lại bằng Verilator (S2, phép kiểm K0).

Nạp đúng file `firmware.hex` mà RTL nạp ($readmemh), nên không có khâu dịch lại nào
có thể làm lệch. Bản đồ bộ nhớ lấy từ rtl/mycore/soc_b.v:
    0x0000_0000..0x0000_FFFF  RAM 64 KB
    0x1000_0000  UART data (ghi = gửi byte, đọc = byte nhận)
    0x1000_0004  UART status (bit0 tx_busy, bit1 rx_valid)
    0x1000_0010  bộ đếm phần cứng: ghi 1 = xoá và chạy
    0x1000_0014  giá trị bộ đếm
    0x1000_0020  LED

Khác biệt CÓ Ý THỨC so với RTL: UART ở đây không bao giờ "busy", nên vòng chờ
`while (UART_STAT & TX_BUSY)` chạy ít vòng hơn trên RTL. Việc này KHÔNG ảnh hưởng số
chu kỳ từng lớp (firmware đo từng lớp bằng rdcycle trước khi in), nhưng làm tổng chu
kỳ toàn phiên khác Verilator — nên chỉ so chu kỳ TỪNG LỚP, không so tổng phiên.
"""
from __future__ import annotations

import time
from pathlib import Path

from .ext import dot4 as ext_dot4
from .ext import pmax4 as ext_pmax4
from .ext import req as ext_req

# ---- lớp lệnh (thứ tự này là thứ tự cột trong mọi báo cáo) ----
# Tách `shift` khỏi `alu` và tách nhánh nhảy/không nhảy: trên mycore cả bốn đều
# 1 chu kỳ, nhưng PicoRV32 trả giá khác nhau -> cần tách để mô hình hiệu chuẩn được.
CLASSES = ("alu", "shift", "branch_taken", "branch_nt", "jal", "jalr", "load",
           "store", "mul", "div", "csr", "misc", "custom_dot4", "custom_req",
           "custom_pmax4")
(C_ALU, C_SHIFT, C_BRT, C_BRN, C_JAL, C_JALR, C_LD, C_ST, C_MUL, C_DIV, C_CSR,
 C_MISC, C_DOT4, C_REQ, C_PMAX4) = range(15)

RAM_WORDS = 16384
RAM_BYTES = RAM_WORDS * 4
M = 0xFFFFFFFF


class Trap(Exception):
    def __init__(self, pc, instr, why):
        super().__init__(f"trap tại pc=0x{pc:08x} instr=0x{instr:08x}: {why}")
        self.pc, self.instr, self.why = pc, instr, why


def load_hex(path: Path) -> bytearray:
    """Đọc firmware.hex (một từ 32 bit mỗi dòng, hex) giống $readmemh của Verilog."""
    mem = bytearray(RAM_BYTES)
    i = 0
    for ln in Path(path).read_text().split():
        mem[i:i + 4] = int(ln, 16).to_bytes(4, "little")
        i += 4
        if i >= RAM_BYTES:
            break
    return mem


class Window:
    """Một cửa sổ đo giữa hai lần đọc rdcycle — khớp đúng cách firmware tự đo."""
    __slots__ = ("idx", "cyc0", "cyc1", "ins0", "ins1", "classes", "pc_count", "prof",
                 "n_ldu")

    def __init__(self, idx, cyc0, ins0, pc_hist):
        self.idx, self.cyc0, self.ins0 = idx, cyc0, ins0
        self.cyc1 = self.ins1 = None
        self.classes = [0] * len(CLASSES)
        self.prof = None
        self.pc_count = {} if pc_hist else None
        # số cặp load-use trong CỬA SỔ này (chỉ đếm khi track_ldu=True)
        self.n_ldu = 0

    @property
    def cycles(self):
        return None if self.cyc1 is None else self.cyc1 - self.cyc0

    @property
    def instret(self):
        return None if self.ins1 is None else self.ins1 - self.ins0

    def as_dict(self):
        d = {"idx": self.idx, "cycles": self.cycles, "instret": self.instret,
             "classes": dict(zip(CLASSES, self.classes))}
        return d


class Prof:
    """Dữ liệu profile của MỘT cửa sổ đo (bật bằng Iss(profile=True)).

    Bốn phép đo mà profile 3 tầng và phân tích ILP/DLP/roofline cần
    (docs/PIPELINE_SPEC.md 2.2, docs/MO_HINH_CHI_PHI.md mục 3):

    - `pc`            số lần thực thi theo từng địa chỉ lệnh (tầng 3)
    - `edge`          số lần đi theo từng cạnh nhảy; cạnh có đích <= nguồn là
                      **cạnh nhảy ngược** -> nhận ra vòng lặp (tầng 2)
    - `as_addr`       kết quả của lệnh tại pc này bị dùng làm **địa chỉ** bao nhiêu lần
    - `to_branch`     ... bị dùng làm toán hạng **rẽ nhánh** bao nhiêu lần
    - `ld_bytes`/`st_bytes`  byte dữ liệu thực sự nạp/lưu -> byte trên mỗi MAC, roofline
    - `crit`          đường găng RAW qua thanh ghi (chiều cao đồ thị phụ thuộc)
                      -> IPC lý tưởng = số lệnh / đường găng
    - `stride`        với mỗi lệnh load: biểu đồ khoảng cách địa chỉ giữa hai lần
                      liên tiếp -> biết truy cập có liên tục không (DLP)
    """
    __slots__ = ("pc", "edge", "as_addr", "to_branch", "ld_bytes", "st_bytes",
                 "crit", "stride", "mulh", "n", "tainted", "to_mulh", "macchain",
                 "taken", "memdep")

    def __init__(self):
        self.pc = {}
        self.edge = {}
        self.as_addr = {}
        self.to_branch = {}
        self.ld_bytes = 0
        self.st_bytes = 0
        self.crit = 0
        self.stride = {}
        self.mulh = {}
        self.n = 0
        self.tainted = {}      # pc -> số lần chạy mà toán hạng đến TỪ một mulh
        self.to_mulh = {}      # pc -> số lần kết quả bị một mulh dùng làm toán hạng
        self.macchain = {}     # pc -> số lần toán hạng đến TỪ một mul/DOT4 (cộng dồn)
        self.taken = {}        # pc -> số lần lệnh nhánh này NHẢY (để tách lambda)
        self.memdep = {}       # (pc_store, pc_load) -> số lần load đọc đúng từ mà
                               # store đó vừa ghi (phụ thuộc QUA BỘ NHỚ — quyết định
                               # một vòng lặp có vector hoá được hợp lệ hay không)

    def as_dict(self, top=40):
        hot = sorted(self.pc.items(), key=lambda kv: -kv[1])[:top]
        back = {f"{a:#x}->{b:#x}": c for (a, b), c in self.edge.items() if b <= a}
        return {"n_instr": self.n, "crit_path": self.crit,
                "ipc_ideal": round(self.n / self.crit, 3) if self.crit else None,
                "ld_bytes": self.ld_bytes, "st_bytes": self.st_bytes,
                "hot_pc": [{"pc": f"{k:#x}", "n": v} for k, v in hot],
                "backedges": dict(sorted(back.items(), key=lambda kv: -kv[1])[:20]),
                "n_mulh": sum(self.mulh.values()),
                "n_tainted": sum(self.tainted.values()),
                "tainted": {f"{k:#x}": v for k, v in self.tainted.items()},
                "macchain": {f"{k:#x}": v for k, v in self.macchain.items()},
                "taken": {f"{k:#x}": v for k, v in self.taken.items()},
                "memdep": {f"{a:#x}->{b:#x}": c for (a, b), c in
                           sorted(self.memdep.items(), key=lambda kv: -kv[1])[:30]},
                "n_memdep": sum(self.memdep.values()),
                "to_mulh": {f"{k:#x}": v for k, v in self.to_mulh.items()},
                "as_addr": {f"{k:#x}": v for k, v in
                            sorted(self.as_addr.items(), key=lambda kv: -kv[1])[:40]},
                "to_branch": {f"{k:#x}": v for k, v in
                              sorted(self.to_branch.items(), key=lambda kv: -kv[1])[:40]},
                "stride": {f"{k:#x}": dict(sorted(v.items(), key=lambda kv: -kv[1])[:4])
                           for k, v in sorted(self.stride.items(),
                                              key=lambda kv: -sum(kv[1].values()))[:20]},
                }


class Iss:
    def __init__(self, hexfile, timing: dict, with_dot4=False, with_req=False,
                 pc_hist=False, profile=False, memdep=False, with_pmax4=False,
                 track_sp=False, track_ldu=False):
        self.mem = load_hex(hexfile)
        self.regs = [0] * 32
        self.pc = 0
        self.timing = timing
        self.cycle = int(timing.get("reset_cycles", 1))
        self.instret = 0
        self.with_dot4 = with_dot4
        self.with_req = with_req
        self.with_pmax4 = with_pmax4
        # track_sp: ghi lại giá trị NHỎ NHẤT của x2 (sp) để biết độ sâu ngăn xếp thật.
        # Cần cho quyết định thu RAM 64 KB -> 32 KB (bộ nhớ hai cổng chỉ vừa ở 32 KB).
        self.track_sp = track_sp
        self.min_sp = None
        # track_ldu: đếm cặp "load rồi lệnh NGAY SAU dùng thanh ghi vừa nạp".
        # Quyết định xem bộ nhớ hai cổng có thật đạt λ_load = 1 không: trong lõi 2 tầng,
        # đúng những cặp này cần đường chuyển tiếp, nếu không thì phải chèn 1 chu kỳ dừng.
        self.track_ldu = track_ldu
        self.n_load = 0
        self.n_load_use_next = 0
        self.pc_hist = pc_hist
        self.profile = profile
        self.memdep = memdep
        self.mem_writer = [0] * RAM_WORDS if memdep else None
        self.classes = [0] * len(CLASSES)
        self.pc_count = {} if pc_hist else None
        # số cặp load-use trong CỬA SỔ này (chỉ đếm khi track_ldu=True)
        self.n_ldu = 0
        self.uart = bytearray()
        self.hw_cnt = 0
        self.hw_run = False
        self.windows: list[Window] = []
        self._cur: Window | None = None
        self._n_rdcycle = 0
        self.lat = [int(timing[c]) for c in CLASSES]
        self.seconds = 0.0
        self.src_hash = None
        self.variant = None

    # ---------------- MMIO ----------------
    def _per_read(self, addr):
        a = addr & 0xFF
        if a == 0x00:
            return 0                      # không có byte nhận
        if a == 0x04:
            return 0                      # tx không bao giờ busy, rx không valid
        if a == 0x14:
            return self.hw_cnt & M
        return 0

    def _per_write(self, addr, val, strb):
        a = addr & 0xFF
        if a == 0x00:
            self.uart.append(val & 0xFF)
        elif a == 0x10:
            self.hw_run = bool(val & 1)
            if val & 1:
                self.hw_cnt = 0
        # 0x20 = LED: không cần mô hình

    # ---------------- chạy ----------------
    def run(self, stop_on=b"M1S,done", max_instr=200_000_000, max_windows=None):
        t0 = time.time()
        mem = self.mem
        regs = self.regs
        cls = self.classes
        lat = self.lat
        pc = self.pc
        cycle = self.cycle
        instret = self.instret
        pch = self.pc_count
        n_stop = len(stop_on)
        # trạng thái cho profile: ai ghi thanh ghi lần cuối, chiều cao phụ thuộc,
        # địa chỉ lần trước của mỗi lệnh load
        do_prof = self.profile
        lw = [0] * 32          # pc của lệnh ghi thanh ghi lần cuối
        ht = [0] * 32          # chiều cao đồ thị phụ thuộc của giá trị trong thanh ghi
        tn = [0] * 32          # "vết": giá trị này nằm trong chuỗi phụ thuộc sau một mulh
        last_addr = {}
        prof = None
        do_md = self.memdep
        mw = self.mem_writer
        tsp = self.track_sp
        min_sp = 1 << 32
        tldu = self.track_ldu
        prev_ld_rd = 0          # rd của lệnh load ngay trước, 0 nếu lệnh trước không phải load
        n_ld = 0
        n_ldu = 0
        try:
            while instret < max_instr:
                instr = (mem[pc] | (mem[pc + 1] << 8) | (mem[pc + 2] << 16)
                         | (mem[pc + 3] << 24))
                op = instr & 0x7F
                rd = (instr >> 7) & 0x1F
                f3 = (instr >> 12) & 7
                rs1 = (instr >> 15) & 0x1F
                rs2 = (instr >> 20) & 0x1F
                if pch is not None:
                    pch[pc] = pch.get(pc, 0) + 1
                    cur = self._cur
                    if cur is not None and cur.pc_count is not None:
                        cur.pc_count[pc] = cur.pc_count.get(pc, 0) + 1

                if tldu:
                    if prev_ld_rd:
                        # Đọc rs1 trừ lui/jal/auipc; đọc rs2 chỉ với dạng R/nhánh/store/custom
                        # (với dạng khác, bit [24:20] là immediate — cùng cái bẫy đã sửa ở
                        # phần chiều cao phụ thuộc).
                        use = (prev_ld_rd == rs1
                               and op != 0x37 and op != 0x6F and op != 0x17)
                        if not use and (op == 0x33 or op == 0x63
                                        or op == 0x23 or op == 0x0B):
                            use = (prev_ld_rd == rs2)
                        if use:
                            n_ldu += 1
                            _c = self._cur
                            if _c is not None:
                                _c.n_ldu += 1
                    if op == 0x03:
                        n_ld += 1
                        prev_ld_rd = rd
                    else:
                        prev_ld_rd = 0

                k = None          # lớp lệnh
                npc = pc + 4
                val = None       # giá trị ghi về

                if op == 0x13:                                  # OP-IMM
                    k = C_SHIFT if (f3 == 1 or f3 == 5) else C_ALU
                    a = regs[rs1]
                    imm = instr >> 20
                    if imm & 0x800:
                        imm -= 0x1000
                    if f3 == 0:
                        val = (a + imm) & M
                    elif f3 == 1:
                        val = (a << (rs2 & 0x1F)) & M
                    elif f3 == 2:
                        val = 1 if ((a ^ 0x80000000) < ((imm & M) ^ 0x80000000)) else 0
                    elif f3 == 3:
                        val = 1 if a < (imm & M) else 0
                    elif f3 == 4:
                        val = a ^ (imm & M)
                    elif f3 == 5:
                        sh = rs2 & 0x1F
                        if instr & 0x40000000:
                            val = ((a - 0x100000000) >> sh) & M if a & 0x80000000 \
                                else (a >> sh)
                        else:
                            val = a >> sh
                    elif f3 == 6:
                        val = a | (imm & M)
                    else:
                        val = a & (imm & M)
                elif op == 0x33:                                # OP
                    a = regs[rs1]
                    b = regs[rs2]
                    f7 = instr >> 25
                    if f7 == 1:                                 # RV32M
                        if f3 < 4:
                            k = C_MUL
                            sa = a - 0x100000000 if a & 0x80000000 else a
                            sb = b - 0x100000000 if b & 0x80000000 else b
                            if f3 == 0:
                                val = (a * b) & M
                            elif f3 == 1:
                                val = ((sa * sb) >> 32) & M
                            elif f3 == 2:
                                val = ((sa * b) >> 32) & M
                            else:
                                val = ((a * b) >> 32) & M
                        else:
                            k = C_DIV
                            sa = a - 0x100000000 if a & 0x80000000 else a
                            sb = b - 0x100000000 if b & 0x80000000 else b
                            if f3 == 4:
                                val = M if b == 0 else \
                                    (abs(sa) // abs(sb) * (1 if (sa < 0) == (sb < 0) else -1)) & M
                            elif f3 == 5:
                                val = M if b == 0 else (a // b) & M
                            elif f3 == 6:
                                if b == 0:
                                    val = a
                                else:
                                    r = abs(sa) % abs(sb)
                                    val = (-r if sa < 0 else r) & M
                            else:
                                val = a if b == 0 else (a % b) & M
                    else:
                        k = C_SHIFT if (f3 == 1 or f3 == 5) else C_ALU
                        if f3 == 0:
                            val = (a - b) & M if f7 == 0x20 else (a + b) & M
                        elif f3 == 1:
                            val = (a << (b & 0x1F)) & M
                        elif f3 == 2:
                            val = 1 if ((a ^ 0x80000000) < (b ^ 0x80000000)) else 0
                        elif f3 == 3:
                            val = 1 if a < b else 0
                        elif f3 == 4:
                            val = a ^ b
                        elif f3 == 5:
                            sh = b & 0x1F
                            if f7 == 0x20:
                                val = ((a - 0x100000000) >> sh) & M if a & 0x80000000 \
                                    else (a >> sh)
                            else:
                                val = a >> sh
                        elif f3 == 6:
                            val = a | b
                        else:
                            val = a & b
                elif op == 0x03:                                # LOAD
                    k = C_LD
                    imm = instr >> 20
                    if imm & 0x800:
                        imm -= 0x1000
                    addr = (regs[rs1] + imm) & M
                    if addr >= 0x10000000:
                        w = self._per_read(addr)
                        val = w
                    elif f3 == 0:
                        b0 = mem[addr]
                        val = (b0 - 256 if b0 & 0x80 else b0) & M
                    elif f3 == 4:
                        val = mem[addr]
                    elif f3 == 1:
                        if addr & 1:
                            raise Trap(pc, instr, "lh lệch địa chỉ")
                        h = mem[addr] | (mem[addr + 1] << 8)
                        val = (h - 65536 if h & 0x8000 else h) & M
                    elif f3 == 5:
                        if addr & 1:
                            raise Trap(pc, instr, "lhu lệch địa chỉ")
                        val = mem[addr] | (mem[addr + 1] << 8)
                    elif f3 == 2:
                        if addr & 3:
                            raise Trap(pc, instr, "lw lệch địa chỉ")
                        val = (mem[addr] | (mem[addr + 1] << 8) | (mem[addr + 2] << 16)
                               | (mem[addr + 3] << 24))
                    else:
                        raise Trap(pc, instr, "funct3 load không hợp lệ")
                elif op == 0x23:                                # STORE
                    k = C_ST
                    rd = 0          # trường rd ở đây là phần immediate, KHÔNG phải đích
                    imm = ((instr >> 25) << 5) | ((instr >> 7) & 0x1F)
                    if imm & 0x800:
                        imm -= 0x1000
                    addr = (regs[rs1] + imm) & M
                    d = regs[rs2]
                    if addr >= 0x10000000:
                        self._per_write(addr, d, f3)
                    elif f3 == 0:
                        mem[addr] = d & 0xFF
                    elif f3 == 1:
                        if addr & 1:
                            raise Trap(pc, instr, "sh lệch địa chỉ")
                        mem[addr] = d & 0xFF
                        mem[addr + 1] = (d >> 8) & 0xFF
                    elif f3 == 2:
                        if addr & 3:
                            raise Trap(pc, instr, "sw lệch địa chỉ")
                        mem[addr] = d & 0xFF
                        mem[addr + 1] = (d >> 8) & 0xFF
                        mem[addr + 2] = (d >> 16) & 0xFF
                        mem[addr + 3] = (d >> 24) & 0xFF
                    else:
                        raise Trap(pc, instr, "funct3 store không hợp lệ")
                elif op == 0x63:                                # BRANCH
                    a = regs[rs1]
                    b = regs[rs2]
                    if f3 == 0:
                        take = a == b
                    elif f3 == 1:
                        take = a != b
                    elif f3 == 4:
                        take = (a ^ 0x80000000) < (b ^ 0x80000000)
                    elif f3 == 5:
                        take = (a ^ 0x80000000) >= (b ^ 0x80000000)
                    elif f3 == 6:
                        take = a < b
                    elif f3 == 7:
                        take = a >= b
                    else:
                        raise Trap(pc, instr, "funct3 branch không hợp lệ")
                    if take:
                        k = C_BRT
                        imm = (((instr >> 31) << 12) | (((instr >> 7) & 1) << 11)
                               | (((instr >> 25) & 0x3F) << 5) | (((instr >> 8) & 0xF) << 1))
                        if imm & 0x1000:
                            imm -= 0x2000
                        npc = (pc + imm) & M
                    else:
                        k = C_BRN
                    rd = 0
                elif op == 0x6F:                                # JAL
                    k = C_JAL
                    imm = (((instr >> 31) << 20) | (((instr >> 12) & 0xFF) << 12)
                           | (((instr >> 20) & 1) << 11) | (((instr >> 21) & 0x3FF) << 1))
                    if imm & 0x100000:
                        imm -= 0x200000
                    val = npc
                    npc = (pc + imm) & M
                elif op == 0x67:                                # JALR
                    k = C_JALR
                    imm = instr >> 20
                    if imm & 0x800:
                        imm -= 0x1000
                    val = npc
                    npc = (regs[rs1] + imm) & ~1 & M
                elif op == 0x37:                                # LUI
                    k = C_ALU
                    val = instr & 0xFFFFF000
                elif op == 0x17:                                # AUIPC
                    k = C_ALU
                    val = (pc + (instr & 0xFFFFF000)) & M
                elif op == 0x73:                                # SYSTEM
                    if f3 == 0:
                        raise Trap(pc, instr, "ecall/ebreak")
                    k = C_CSR
                    csr = instr >> 20
                    if csr == 0xC00:
                        val = cycle & M
                        self._mark_rdcycle(cycle, instret)
                    elif csr == 0xC80:
                        val = (cycle >> 32) & M
                    elif csr == 0xC02:
                        val = instret & M
                    elif csr == 0xC82:
                        val = (instret >> 32) & M
                    else:
                        raise Trap(pc, instr, f"CSR 0x{csr:03x} không hỗ trợ")
                elif op == 0x0F:                                # FENCE / FENCE.I
                    k = C_MISC
                    rd = 0
                elif op == 0x0B:                                # custom-0
                    f7 = instr >> 25
                    if self.with_dot4 and f3 == 0 and f7 == 0:
                        k = C_DOT4
                        val = ext_dot4.sem(regs[rs1], regs[rs2])[0]
                    elif self.with_req and f3 == 1:
                        k = C_REQ
                        val = ext_req.sem(regs[rs1], regs[rs2], sh=f7 & 0x1F)[0]
                    elif self.with_pmax4 and f3 == 2 and f7 == 0:
                        k = C_PMAX4
                        val = ext_pmax4.sem(regs[rs1], regs[rs2])[0]
                    else:
                        raise Trap(pc, instr, "lệnh custom-0 không được bật")
                else:
                    raise Trap(pc, instr, f"opcode 0x{op:02x} không hợp lệ")

                if do_prof and prof is not None:
                    prof.n += 1
                    prof.pc[pc] = prof.pc.get(pc, 0) + 1
                    if npc != pc + 4:
                        e = (pc, npc)
                        prof.edge[e] = prof.edge.get(e, 0) + 1
                    if k == C_LD or k == C_ST:
                        w = lw[rs1]
                        prof.as_addr[w] = prof.as_addr.get(w, 0) + 1
                        if do_md and addr < RAM_BYTES:
                            wi = addr >> 2
                            if k == C_ST:
                                mw[wi] = pc
                            else:
                                sp = mw[wi]
                                if sp:
                                    key = (sp, pc)
                                    prof.memdep[key] = prof.memdep.get(key, 0) + 1
                        nb = 1 if (f3 & 3) == 0 else (2 if (f3 & 3) == 1 else 4)
                        if addr < 0x10000000:
                            if k == C_LD:
                                prof.ld_bytes += nb
                            else:
                                prof.st_bytes += nb
                            d = prof.stride.setdefault(pc, {})
                            pa = last_addr.get(pc)
                            if pa is not None:
                                st_ = addr - pa
                                d[st_] = d.get(st_, 0) + 1
                            last_addr[pc] = addr
                    elif k == C_BRT or k == C_BRN:
                        if k == C_BRT:
                            prof.taken[pc] = prof.taken.get(pc, 0) + 1
                        w = lw[rs1]
                        prof.to_branch[w] = prof.to_branch.get(w, 0) + 1
                        w = lw[rs2]
                        prof.to_branch[w] = prof.to_branch.get(w, 0) + 1
                    elif k == C_MUL and f3 != 0:
                        prof.mulh[pc] = prof.mulh.get(pc, 0) + 1
                        for r in (rs1, rs2):
                            w = lw[r]
                            prof.to_mulh[w] = prof.to_mulh.get(w, 0) + 1
                    # Chỉ các lệnh dạng R / nhánh / store / custom mới đọc rs2;
                    # với các lệnh khác, bit [24:20] là phần immediate.
                    h = ht[rs1]
                    t = tn[rs1]
                    if op == 0x33 or op == 0x63 or op == 0x23 or op == 0x0B:
                        if ht[rs2] > h:
                            h = ht[rs2]
                        t |= tn[rs2]
                    if op == 0x37 or op == 0x6F or op == 0x17:   # lui/jal/auipc
                        h = 0
                        t = 0
                    h += lat[k]
                    if h > prof.crit:
                        prof.crit = h
                    if t & 1:
                        prof.tainted[pc] = prof.tainted.get(pc, 0) + 1
                        # Lệnh đã có vết mà đọc toán hạng từ một lệnh CHƯA có vết thì
                        # lệnh kia là ĐẦU VÀO của chuỗi requantize — cách này bắt được
                        # `mul` song sinh của `mulh` (hai lệnh đọc cùng toán hạng nên
                        # không có quan hệ sản xuất-tiêu thụ giữa chúng).
                        if tn[rs1] == 0:
                            ww = lw[rs1]
                            prof.to_mulh[ww] = prof.to_mulh.get(ww, 0) + 1
                        if (op == 0x33 or op == 0x63 or op == 0x23) and tn[rs2] == 0:
                            ww = lw[rs2]
                            prof.to_mulh[ww] = prof.to_mulh.get(ww, 0) + 1
                    elif t & 2:
                        prof.macchain[pc] = prof.macchain.get(pc, 0) + 1
                    if rd:
                        ht[rd] = h
                        lw[rd] = pc
                        # vết: bit0 = sau một `mulh` (chuỗi requantize),
                        #      bit1 = sau một `mul`/DOT4 (chuỗi cộng dồn MAC)
                        if k == C_MUL:
                            if f3 != 0:
                                tn[rd] = 1
                            else:
                                # Phép nhân 64 bit (sat_rdhmul của requantize) sinh một
                                # `mul` và một `mulh` SONG SINH, đọc cùng toán hạng.
                                # `mul` không phải đầu vào của `mulh` nên vết không bắt
                                # được -> xem trước 2 lệnh kế để nhận ra cặp này.
                                sib = 0
                                for off in (4, 8):
                                    i2 = (mem[pc + off] | (mem[pc + off + 1] << 8)
                                          | (mem[pc + off + 2] << 16)
                                          | (mem[pc + off + 3] << 24))
                                    if ((i2 & 0x7F) == 0x33 and (i2 >> 25) == 1
                                            and 1 <= ((i2 >> 12) & 7) <= 3
                                            and ((i2 >> 15) & 0x1F) == rs1
                                            and ((i2 >> 20) & 0x1F) == rs2):
                                        sib = 1
                                        break
                                tn[rd] = 1 if sib else 2
                                if sib:
                                    prof.to_mulh[pc] = prof.to_mulh.get(pc, 0) + 1
                        elif k == C_DOT4:
                            tn[rd] = 2
                        elif k == C_LD:
                            tn[rd] = 0
                        else:
                            tn[rd] = t
                if rd and val is not None:
                    regs[rd] = val
                    if tsp and rd == 2 and val < min_sp:
                        min_sp = val
                cls[k] += 1
                cycle += lat[k]
                instret += 1
                if self.hw_run:
                    self.hw_cnt += lat[k]
                cur = self._cur
                if cur is not None:
                    cur.classes[k] += 1
                    if do_prof:
                        prof = cur.prof
                elif do_prof:
                    prof = None
                pc = npc

                if k == C_ST and self.uart and self.uart[-1] == 0x0A:
                    if self.uart[-n_stop - 2:] == stop_on + b"\r\n":
                        break
                    if max_windows and len(self.windows) >= max_windows:
                        break
        finally:
            self.pc, self.cycle, self.instret = pc, cycle, instret
            self.seconds = time.time() - t0
            if tsp:
                self.min_sp = None if min_sp == (1 << 32) else min_sp
            if tldu:
                self.n_load, self.n_load_use_next = n_ld, n_ldu
        self._parse_uart()
        return self

    # ---------------- cửa sổ đo ----------------
    def _mark_rdcycle(self, cycle, instret):
        """rdcycle lẻ MỞ một cửa sổ, rdcycle chẵn ĐÓNG nó — đúng như firmware đo."""
        self._n_rdcycle += 1
        if self._n_rdcycle % 2 == 1:
            self._cur = Window(len(self.windows), cycle, instret, self.pc_hist)
            if self.profile:
                self._cur.prof = Prof()
        else:
            w = self._cur
            if w is not None:
                w.cyc1, w.ins1 = cycle, instret
                self.windows.append(w)
            self._cur = None

    # ---------------- đọc lại đầu ra UART ----------------
    def _parse_uart(self):
        txt = self.uart.decode("ascii", "replace")
        self.uart_text = txt
        for ln in txt.splitlines():
            if ln.startswith("M1S,hello,"):
                a = ln.split(",")
                self.variant = a[3] if len(a) > 3 else None
            elif ln.startswith("M1S,src,"):
                self.src_hash = ln.split(",")[2]

    # ---------------- báo cáo ----------------
    def class_counts(self) -> dict:
        return dict(zip(CLASSES, self.classes))

    def model_cycles(self) -> int:
        """C = sum(n_c * lambda_c) + reset — đúng phương trình của mô hình."""
        return int(self.timing.get("reset_cycles", 1)) + sum(
            n * l for n, l in zip(self.classes, self.lat))

    def layer_windows(self, n_img=10, per_img=5) -> list[list[Window]]:
        """Nhóm cửa sổ theo ảnh: 5 cửa sổ (conv1 pool1 conv2 pool2 dense) mỗi ảnh."""
        out = []
        for i in range(n_img):
            sl = self.windows[i * per_img:(i + 1) * per_img]
            if len(sl) == per_img:
                out.append(sl)
        return out


def merge_profs(profs):
    """Cộng dồn Prof của nhiều ảnh thành một — để tổng chu kỳ phân loại so được
    với tổng chu kỳ của ĐÚNG những ảnh đó (không trộn trung vị với một ảnh)."""
    out = Prof()
    for q in profs:
        if q is None:
            continue
        out.n += q.n
        out.ld_bytes += q.ld_bytes
        out.st_bytes += q.st_bytes
        if q.crit > out.crit:
            out.crit = q.crit
        for name in ("pc", "as_addr", "to_branch", "mulh", "tainted", "to_mulh",
                     "macchain", "taken", "edge"):
            dst = getattr(out, name)
            for k, v in getattr(q, name).items():
                dst[k] = dst.get(k, 0) + v
        for k, h in q.stride.items():
            d = out.stride.setdefault(k, {})
            for kk, vv in h.items():
                d[kk] = d.get(kk, 0) + vv
    return out
