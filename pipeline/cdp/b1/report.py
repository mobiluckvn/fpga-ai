"""Sinh PROFILE.md cấp cho subagent mù ở vòng B1.

Chỉ chứa **sự thật về hiệu năng của chính biến thể hiện tại** và **bảng chu kỳ của
lõi đích**. KHÔNG chứa: danh mục mẫu tối ưu, tên bất kỳ tối ưu nào đã làm bằng tay,
số đo của biến thể khác, hay đường dẫn tài liệu. Đây là điều kiện của chế độ mù.
"""
from __future__ import annotations

import statistics as st
from pathlib import Path

import yaml

from .. import paths, targets, wrap
from ..iss.core import CLASSES, Iss, merge_profs
from ..iss.elf import FuncMap
from ..profile import SEM, tier3
from ..static_analysis import analyze_loop
from ..util import fmt_int

BYTES_PER_ACCESS = 4


def _timing():
    return yaml.safe_load((paths.CDP / "iss/timing/mycore.yaml").read_text())


def variant_report(hexf: Path, w: Path, out: str, n_img: int = 10):
    doc = _timing()
    lam = doc["profiles"]["fast_addr_1"]
    iss = Iss(hexf, lam, profile=True, memdep=True).run()
    blk = wrap.m1s_check_mod().parse_block(iss.uart_text.splitlines())
    groups = iss.layer_windows(n_img=n_img)
    elf = w / "experiment/m1s_b1" / out / "firmware.elf"
    fm = FuncMap(elf) if elf.exists() else None

    tot = int(st.median([sum(x.cycles for x in g) for g in groups]))
    L = []
    A = L.append
    A("# Hồ sơ hiệu năng của `kernels.c` hiện tại\n")
    A("Mọi số dưới đây do một bộ mô phỏng tập lệnh đếm trực tiếp khi chạy đúng firmware")
    A("này trên lõi đích, 10 ảnh đầu vào. Không có số nào là ước lượng.\n")
    A(f"**Tổng: {fmt_int(tot)} chu kỳ cho một ảnh.** Mô hình có "
      f"{fmt_int(targets.MAC_TOTAL)} phép nhân-cộng (MAC) cho một ảnh.\n")
    A("## Lõi đích: số chu kỳ mỗi lệnh\n")
    A("| lớp lệnh | chu kỳ |")
    A("|---|---:|")
    for k in ("alu", "shift", "branch_taken", "branch_nt", "jal", "jalr", "load",
              "store", "mul", "div"):
        A(f"| {k} | {lam[k]} |")
    A("")
    A("Lõi phát **một lệnh mỗi chu kỳ**, không đoán nhánh (nhảy hay không nhảy đều")
    A("bằng giá), không có cache. Bộ nhớ **một cổng**: mỗi lần truy cập dữ liệu chiếm")
    A(f"cổng nên load/store tốn {lam['load']} chu kỳ, và băng thông tối đa là")
    A(f"{BYTES_PER_ACCESS}/{lam['load']} = {BYTES_PER_ACCESS/lam['load']:g} byte/chu kỳ.")
    A("Có 31 thanh ghi dùng được (x1–x31).\n")
    A("## Chu kỳ theo lớp mạng và theo loại công việc\n")
    A("| lớp mạng | chu kỳ | MAC | byte dữ liệu | byte/MAC | "
      + " | ".join(SEM) + " |")
    A("|---|---:|---:|---:|---:|" + "---:|" * len(SEM))
    per_layer = {}
    for li, lay in enumerate(targets.LAYERS):
        ws = [g[li] for g in groups]
        mg = merge_profs([x.prof for x in ws])
        pd = mg.as_dict()
        pd["_pc_full"] = dict(mg.pc)
        t3 = tier3(pd, iss.mem, lam, fm)
        cyc = int(st.median([x.cycles for x in ws]))
        csum = sum(x.cycles for x in ws)
        byt = (mg.ld_bytes + mg.st_bytes) / n_img
        mac = targets.MAC_LAYER[lay]
        sh = {k: 100 * t3["cycles_by_sem"].get(k, 0) / max(csum, 1) for k in SEM}
        per_layer[lay] = {"cycles": cyc, "share": sh, "prof": pd, "bytes": byt}
        A(f"| {lay} | {fmt_int(cyc)} | {fmt_int(mac) if mac else '—'} | "
          f"{fmt_int(byt)} | {byt/mac:.2f} |" if mac else
          f"| {lay} | {fmt_int(cyc)} | — | {fmt_int(byt)} | — |")
        L[-1] = L[-1] + " " + " | ".join(f"{sh[k]:.1f}" for k in SEM) + " |"
    A("")
    A("Nghĩa của các loại công việc: `mac` phép nhân và phép cộng dồn ngay sau nó · ")
    A("`load_data`/`store_data` truy cập dữ liệu · `addr` lệnh tính địa chỉ cho truy cập ·")
    A("`loop_ctrl` lệnh điều khiển vòng lặp · `requant` chuỗi lượng tử hoá lại ·")
    A("`other` còn lại.\n")
    A("## Các vòng lặp nóng nhất\n")
    for lay in targets.LAYERS:
        pd = per_layer[lay]["prof"]
        loops = []
        for e, trips in list(pd["backedges"].items())[:2]:
            a, b = (int(x, 16) for x in e.split("->"))
            loops.append(analyze_loop(iss.mem, lam, b, a, pd["_pc_full"],
                                      pd["memdep"], pd["stride"], trips))
        if not loops:
            continue
        A(f"**{lay}**\n")
        A("| số vòng | chu kỳ/vòng | lệnh/vòng | thanh ghi dùng | **còn trống** | "
          "mang theo vòng | chuỗi phụ thuộc bắt buộc | phụ thuộc qua bộ nhớ nội vòng | "
          "nạp liên tục 1 byte |")
        A("|---:|---:|---:|---:|---:|---|---:|---:|---:|")
        for d in loops:
            A(f"| {fmt_int(d['trips'])} | {d['cycles_per_trip']} | "
              f"{round(d['dynamic_instr']/max(d['trips'],1),1)} | {d['n_regs_used']} | "
              f"**{d['n_regs_free']}** | "
              f"{','.join('x'+str(r) for r in d['loop_carried_regs']) or '—'} | "
              f"{d['recurrence_cycles']} | {fmt_int(d['n_memdep_in_loop'])} | "
              f"{str(d['stride1_share_pct'])+' %' if d['stride1_share_pct'] is not None else '—'} |")
        A("")
    A("Cột **còn trống** là số thanh ghi chưa dùng trong thân vòng đó: nếu nhỏ thì thêm")
    A("biến tạm sẽ làm trình biên dịch phải tràn thanh ghi ra bộ nhớ và mất lợi ích.")
    A("`phụ thuộc qua bộ nhớ nội vòng` = 0 nghĩa là không có lệnh nạp nào trong vòng đọc")
    A("ô mà một lệnh lưu trong cùng vòng vừa ghi.\n")
    meas = {"median_cycles": tot,
            "layers": {k: v["cycles"] for k, v in per_layer.items()},
            "bit_exact": wrap.check_golden(blk)["ok"] if blk else None}
    return "\n".join(L) + "\n", meas
