"""Bảng 14 cấu hình ĐÃ ĐO của giai đoạn trước (docs/KET_QUA_TONG_HOP.md mục 1).

Bảng này là bản ĐỌC MÁY của những gì Makefile đã có làm được: mỗi dòng ghi đích
make, thư mục build, cờ biên dịch, tham số RTL, nhãn CSV và số chu kỳ trung vị đã
công bố. cdp dùng nó để (a) phân giải một đặc tả YAML về đúng một cấu hình,
(b) đối chứng khi tái tạo ở S1, (c) quét cả 14 cấu hình ở S2.

Nguồn của từng trường — KHÔNG trường nào do suy đoán:
  cờ, đích make, tham số RTL : experiment/m1s/Makefile · rtl/mycore/Makefile
  nhãn biến thể firmware báo : experiment/m1s/main.c (macro VARIANT)
  chu kỳ trung vị            : results/experiment/m1s/m1s.csv · results/branch_b/m1s_b.csv
                               với định nghĩa trung vị = int(statistics.median(10 ảnh)),
                               đúng như scripts/branch_b_table.py — đã kiểm khớp
                               cả 14 số trong docs/KET_QUA_TONG_HOP.md
"""
from __future__ import annotations

from dataclasses import dataclass, field

from . import paths

MAC_TOTAL = 192064
MAC_LAYER = {"conv1": 48672, "pool1": 0, "conv2": 139392, "pool2": 0, "dense": 4000}
LAYERS = ("conv1", "pool1", "conv2", "pool2", "dense")
CLOCK_MHZ = 27.0


@dataclass(frozen=True)
class Target:
    name: str                       # tên trong bảng kết quả, vd "B-V3"
    row: int                        # số dòng trong docs/KET_QUA_TONG_HOP.md mục 1
    branch: str                     # "A" (PicoRV32) hoặc "B" (mycore)
    core: str                       # "picorv32" | "mycore"
    hw: str                         # mô tả phần cứng như trong bảng
    fw_id: str                      # thư mục firmware nhánh A: v0 v1 v2 v1d v1dc v1dcr
    fw_flags: frozenset             # macro -D ĐÚNG như Makefile truyền
    fw_variant: str                 # chuỗi VARIANT firmware tự báo qua UART
    rtl_params: dict                # tham số RTL phân biệt cấu hình
    make_dir: str                   # thư mục chạy make (tương đối gốc dự án)
    var_dir: str                    # thư mục build của biến thể
    make_vars: dict = field(default_factory=dict)   # biến truyền cho make
    kit_csv: str = ""               # CSV số đo kit đã có
    kit_csv_label: str = ""         # nhãn trong cột bien_the của CSV đó
    expect_total_median: int = 0    # chu kỳ/ảnh, trung vị 10 ảnh

    # ---- đích make, suy ra theo quy ước của chính hai Makefile ----
    @property
    def fw_dir(self) -> str:
        """Firmware LUÔN dựng trong experiment/m1s — nhánh B dùng lại đúng file hex đó."""
        return "experiment/m1s"

    @property
    def t_fw(self) -> str:
        return f"fw-{self.fw_id}"

    @property
    def t_sim(self) -> str:
        return f"sim-{self.var_dir}"

    @property
    def t_build(self) -> str:
        return f"build-{self.var_dir}"

    @property
    def t_load(self) -> str:
        return f"load-{self.var_dir}"

    @property
    def t_check(self) -> str:
        return f"check-{self.var_dir}"

    @property
    def sim_log(self) -> str:
        return f"{self.make_dir}/{self.var_dir}/sim.log"

    @property
    def ms(self) -> float:
        return self.expect_total_median / (CLOCK_MHZ * 1e6) * 1000.0

    def as_dict(self) -> dict:
        d = {k: getattr(self, k) for k in
             ("name", "row", "branch", "core", "hw", "fw_id", "fw_variant",
              "make_dir", "var_dir", "kit_csv", "kit_csv_label",
              "expect_total_median")}
        d["fw_flags"] = sorted(self.fw_flags)
        d["rtl_params"] = dict(self.rtl_params)
        d["make_vars"] = dict(self.make_vars)
        d["fw_dir"] = self.fw_dir
        d["make_targets"] = {"fw": self.t_fw, "sim": self.t_sim, "build": self.t_build,
                             "load": self.t_load, "check": self.t_check}
        d["sim_log"] = self.sim_log
        d["ms_27mhz"] = round(self.ms, 1)
        return d


_A = "experiment/m1s"
_B = "rtl/mycore"
_CSVA = "results/experiment/m1s/m1s.csv"
_CSVB = "results/branch_b/m1s_b.csv"

# Cờ biên dịch của từng thư mục firmware — đọc thẳng từ experiment/m1s/Makefile.
FW_FLAGS = {
    "v0":    frozenset(),
    "v1":    frozenset({"OPT_KERNELS"}),
    "v2":    frozenset({"USE_DOT4"}),
    "v1d":   frozenset({"USE_DOT4", "OPT_KERNELS"}),
    "v1dc":  frozenset({"USE_DOT4", "OPT_KERNELS", "CONV1_DOT4", "REQ_BENCH"}),
    "v1dcr": frozenset({"USE_DOT4", "OPT_KERNELS", "CONV1_DOT4", "USE_REQ"}),
    "v10k":  frozenset({"USE_DOT4", "OPT_KERNELS", "CONV1_DOT4", "STREAM_10K"}),
}

FW_VARIANT = {   # macro VARIANT trong main.c
    "v0": "A-V0", "v1": "A-V1", "v2": "A-V2", "v1d": "A-V1+DOT4",
    "v1dc": "A-V1+DOT4+C1", "v1dcr": "A-V1+DOT4+C1+REQ",
    "v10k": "A-V1+DOT4+C1",
}

TARGETS: dict[str, Target] = {}


def _add(t: Target) -> None:
    TARGETS[t.name] = t


# ---------------- nhánh A: PicoRV32 (6 cấu hình) ----------------
for _row, _name, _fw, _hw, _dot4, _req, _med in [
    (1, "A-V0",          "v0",    "PicoRV32",                  0, 0, 8987660),
    (2, "A-V1",          "v1",    "PicoRV32",                  0, 0, 6217634),
    (3, "A-V2",          "v2",    "PicoRV32 + DOT4",           1, 0, 5758001),
    (4, "A-V1+DOT4",     "v1d",   "PicoRV32 + DOT4",           1, 0, 2917079),
    (5, "A-V1+DOT4+C1",  "v1dc",  "PicoRV32 + DOT4",           1, 0, 2450494),
    (6, "A-V3",          "v1dcr", "PicoRV32 + DOT4 + REQ",     1, 1, 1842219),
]:
    _add(Target(name=_name, row=_row, branch="A", core="picorv32", hw=_hw,
                fw_id=_fw, fw_flags=FW_FLAGS[_fw], fw_variant=FW_VARIANT[_fw],
                rtl_params={"WITH_DOT4": _dot4, "WITH_REQ": _req},
                make_dir=_A, var_dir=_fw,
                kit_csv=_CSVA, kit_csv_label=FW_VARIANT[_fw],
                expect_total_median=_med))

# ---------------- nhánh B: mycore (8 cấu hình) ----------------
for _row, _name, _fw, _vdir, _fa, _dot4, _req, _hw, _med in [
    (7,  "B-V0r",         "v0",    "bv0r",   0, 0, 0, "mycore (địa chỉ ghi thanh ghi)", 3750617),
    (8,  "B-V1r",         "v1",    "bv1r",   0, 0, 0, "mycore (địa chỉ ghi thanh ghi)", 2713235),
    (9,  "B-V0",          "v0",    "bv0",    1, 0, 0, "mycore",                         1978697),
    (10, "B-V1",          "v1",    "bv1",    1, 0, 0, "mycore",                         1459993),
    (11, "B-V2",          "v2",    "bv2",    1, 1, 0, "mycore + DOT4",                  1169050),
    (12, "B-V1+DOT4",     "v1d",   "bv1d",   1, 1, 0, "mycore + DOT4",                   631130),
    (13, "B-V1+DOT4+C1",  "v1dc",  "bv1dc",  1, 1, 0, "mycore + DOT4",                   487865),
    (14, "B-V3",          "v1dcr", "bv1dcr", 1, 1, 1, "mycore + DOT4 + REQ",             365992),
]:
    _add(Target(name=_name, row=_row, branch="B", core="mycore", hw=_hw,
                fw_id=_fw, fw_flags=FW_FLAGS[_fw], fw_variant=FW_VARIANT[_fw],
                rtl_params={"FAST_ADDR": _fa, "WITH_DOT4": _dot4, "WITH_REQ": _req,
                            "WITH_MULDIV": 1},
                make_dir=_B, var_dir=_vdir,
                make_vars={"FAST_ADDR": _fa, "WITH_DOT4": _dot4, "WITH_REQ": _req},
                kit_csv=_CSVB, kit_csv_label=_vdir,
                expect_total_median=_med))

BASELINE = TARGETS["A-V0"]


def get(name: str) -> Target:
    if name not in TARGETS:
        raise KeyError(f"không có cấu hình {name!r}; có: {', '.join(TARGETS)}")
    return TARGETS[name]


def resolve(core: str, flags, rtl_params: dict | None = None) -> Target:
    """Phân giải (lõi, tập cờ, tham số RTL) về đúng một cấu hình.

    Cờ nhận cả dạng '-DUSE_DOT4' và 'USE_DOT4'.
    """
    want = frozenset(f.removeprefix("-D") for f in (flags or []))
    rtl_params = rtl_params or {}
    cands = [t for t in TARGETS.values() if t.core == core and t.fw_flags == want]
    if not cands:
        known = {t.name: sorted(t.fw_flags) for t in TARGETS.values() if t.core == core}
        raise ValueError(
            f"không cấu hình nào của lõi {core!r} có đúng tập cờ {sorted(want)}.\n"
            f"Các tập cờ đã biết: {known}")
    if len(cands) > 1:
        narrowed = []
        for t in cands:
            if all(str(t.rtl_params.get(k)) == str(v) for k, v in rtl_params.items()):
                narrowed.append(t)
        cands = narrowed
    if len(cands) != 1:
        raise ValueError(
            "tham số RTL chưa đủ để phân giải: còn "
            f"{[t.name for t in cands] or 'không còn cấu hình nào'}. "
            "Hãy ghi rõ các tham số phân biệt (vd FAST_ADDR, WITH_DOT4, WITH_REQ).")
    return cands[0]


def table() -> list[Target]:
    return sorted(TARGETS.values(), key=lambda t: t.row)
