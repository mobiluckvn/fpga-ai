"""cdp profile — profile 3 tầng từ trace của ISS (SPEC 2.2, bước S3).

Tầng 1  hàm / lớp mạng        : chu kỳ, số lệnh, n_c theo lớp lệnh, byte, đường găng
Tầng 2  khối cơ bản / vòng lặp: cạnh nhảy ngược -> vòng lặp, số vòng, độ dài thân
Tầng 3  mẫu lệnh              : mỗi lệnh ĐỘNG được gán một lớp NGỮ NGHĨA
                                mac | load_data | store_data | addr | loop_ctrl |
                                requant | other

Cách gán lớp ngữ nghĩa — tất định, chỉ từ dữ liệu ISS đo được, không có hệ số tay:
  requant    : lệnh nằm trong chuỗi phụ thuộc của một `mulh` (vết lan truyền trong
               ISS), hoặc chính là `mulh`, hoặc kết quả của nó bị `mulh` dùng làm
               toán hạng. `sat_rdhmul` của requantize là phép nhân 64 bit nên trên
               RV32 luôn sinh đúng một `mul` + một `mulh` -> đây là dấu nhận dạng
               chắc chắn, không phải suy đoán.
  mac        : `mul` thường, `DOT4`, **và các lệnh cộng dồn ngay sau chúng** (vết
               lan truyền bit "sau mul" trong ISS) — vì nhân-cộng là một phép toán,
               tách `add` cộng dồn ra khỏi `mul` thì tỷ trọng MAC bị báo thiếu
  load_data  : **mọi** lệnh nạp dữ liệu. Lệnh bộ nhớ luôn thuộc lớp bộ nhớ, kể cả
               khi nó nằm trong chuỗi requantize — vì nó tiêu thụ băng thông, và đó
               là thứ roofline quan tâm. Nếu không, cùng một lệnh `sb` sẽ đổi lớp
               giữa hai biến thể và sinh chênh lệch giả.
  store_data : như trên, cho lệnh lưu
  addr       : lệnh ALU mà **kết quả bị dùng làm địa chỉ** của load/store ở >= 50 %
               số lần chạy (ISS đếm trực tiếp khi thực thi)
  loop_ctrl  : nhánh là **cạnh nhảy ngược**, hoặc lệnh mà kết quả bị một nhánh như
               vậy dùng làm toán hạng ở >= 50 % số lần chạy
  other      : còn lại (hằng số, ghi/đọc thanh ghi phục vụ gọi hàm, …)
Thứ tự ưu tiên khi một lệnh thoả nhiều điều kiện: requant > mac > load/store > addr
> loop_ctrl > other.
"""
from __future__ import annotations

import json
import statistics as st

from . import ledger, paths, spec as spec_mod, targets, wrap
from .iss import load_timing, run_one
from .iss.core import CLASSES
from .iss.elf import FuncMap
from .util import fmt_int, rel

STEP = "S3"
SEM = ("mac", "load_data", "store_data", "addr", "loop_ctrl", "requant", "other")


def class_of(instr: int) -> str:
    """Lớp lệnh (để tra lambda) của một từ lệnh — cùng quy ước với cdp/iss/core.py."""
    op = instr & 0x7F
    f3 = (instr >> 12) & 7
    f7 = instr >> 25
    if op == 0x13:
        return "shift" if f3 in (1, 5) else "alu"
    if op == 0x33:
        if f7 == 1:
            return "mul" if f3 < 4 else "div"
        return "shift" if f3 in (1, 5) else "alu"
    if op == 0x03:
        return "load"
    if op == 0x23:
        return "store"
    if op == 0x63:
        # Trả về "branch_taken"; tier3 sẽ tách nhảy/không nhảy bằng SỐ LIỆU ĐỘNG
        # (prof.taken), vì giải mã tĩnh không biết được.
        return "branch_taken"
    if op == 0x6F:
        return "jal"
    if op == 0x67:
        return "jalr"
    if op in (0x37, 0x17):
        return "alu"
    if op == 0x73:
        return "csr"
    if op == 0x0F:
        return "misc"
    if op == 0x0B:
        return "custom_req" if f3 == 1 else "custom_dot4"
    return "alu"


def _instr_at(mem, pc):
    return mem[pc] | (mem[pc + 1] << 8) | (mem[pc + 2] << 16) | (mem[pc + 3] << 24)


def tier3(prof: dict, mem, lam: dict, fm: FuncMap | None) -> dict:
    """Gán lớp ngữ nghĩa cho từng địa chỉ lệnh, rồi cộng dồn số lệnh và số chu kỳ."""
    pcs = {int(d["pc"], 16): d["n"] for d in prof["hot_pc"]}
    # hot_pc chỉ giữ top N -> dùng bản đầy đủ nếu có
    pcs = prof.get("_pc_full", pcs)
    taint = {int(k, 16): v for k, v in prof.get("tainted", {}).items()}
    to_mulh = {int(k, 16): v for k, v in prof.get("to_mulh", {}).items()}
    macch = {int(k, 16): v for k, v in prof.get("macchain", {}).items()}
    as_addr = {int(k, 16): v for k, v in prof.get("as_addr", {}).items()}
    taken = {int(k, 16): v for k, v in prof.get("taken", {}).items()}
    to_br = {int(k, 16): v for k, v in prof.get("to_branch", {}).items()}
    back_src = set()
    for e in prof.get("backedges", {}):
        a, b = e.split("->")
        back_src.add(int(a, 16))
    n_sem = dict.fromkeys(SEM, 0)
    c_sem = dict.fromkeys(SEM, 0)
    per_pc = {}
    for pc, n in pcs.items():
        instr = _instr_at(mem, pc)
        cl = class_of(instr)
        is_mulh = cl == "mul" and ((instr >> 12) & 7) != 0
        if cl == "load":
            sem = "load_data"
        elif cl == "store":
            sem = "store_data"
        elif taint.get(pc, 0) >= 0.5 * n or is_mulh or to_mulh.get(pc, 0) >= 0.5 * n:
            sem = "requant"
        elif cl == "mul" or cl == "custom_dot4":
            sem = "mac"
        elif macch.get(pc, 0) >= 0.5 * n and cl in ("alu", "shift"):
            sem = "mac"
        elif cl == "custom_req":
            sem = "requant"
        elif as_addr.get(pc, 0) >= 0.5 * n:
            sem = "addr"
        elif pc in back_src or to_br.get(pc, 0) >= 0.5 * n:
            sem = "loop_ctrl"
        else:
            sem = "other"
        if cl == "branch_taken":
            # Giải mã TĨNH không biết nhánh có nhảy hay không; số liệu động biết.
            nt = taken.get(pc, 0)
            lamc = (nt * lam["branch_taken"] + (n - nt) * lam["branch_nt"]) / n if n else 1
        else:
            lamc = lam.get(cl, 1)
        n_sem[sem] += n
        c_sem[sem] += n * lamc
        per_pc[f"{pc:#x}"] = {"n": n, "class": cl, "sem": sem,
                              "func": fm.of(pc) if fm else None}
    return {"n_by_sem": n_sem, "cycles_by_sem": c_sem, "per_pc": per_pc}


def tier2(prof: dict, mem, lam: dict) -> list:
    """Vòng lặp từ cạnh nhảy ngược: số vòng, độ dài thân, chu kỳ trong thân."""
    pcs = prof.get("_pc_full", {})
    out = []
    for e, cnt in prof.get("backedges", {}).items():
        a, b = (int(x, 16) for x in e.split("->"))
        body = {pc: n for pc, n in pcs.items() if b <= pc <= a}
        cyc = sum(n * lam.get(class_of(_instr_at(mem, pc)), 1) for pc, n in body.items())
        out.append({"backedge": e, "trips": cnt, "body_instr_static": len(body),
                    "body_instr_dynamic": sum(body.values()), "cycles_in_body": cyc})
    return sorted(out, key=lambda d: -d["cycles_in_body"])


def profile_target(t, w, run, n_img=10) -> dict:
    iss = run_one(w, t, run, profile=True)
    lam, meta = load_timing(t)
    fm = None
    elf = w / t.fw_dir / t.fw_id / "firmware.elf"
    if elf.exists():
        try:
            fm = FuncMap(elf)
        except Exception:                                   # noqa: BLE001
            fm = None
    groups = iss.layer_windows(n_img=n_img)
    layers = {}
    for li, lay in enumerate(targets.LAYERS):
        ws = [g[li] for g in groups]
        acc = dict.fromkeys(CLASSES, 0)
        for wd in ws:
            for c, n in zip(CLASSES, wd.classes):
                acc[c] += n
        # Gộp profile của CẢ 10 ảnh: tổng chu kỳ phân loại phải so được với tổng
        # chu kỳ của đúng 10 ảnh đó (bài học mục 1.3: không trộn phạm vi).
        from .iss.core import merge_profs
        mg = merge_profs([x.prof for x in ws])
        pd = mg.as_dict() if mg.n else {}
        if mg.n:
            pd["_pc_full"] = dict(mg.pc)
        layers[lay] = {
            "cycles_median": int(st.median([x.cycles for x in ws])),
            "instret_median": int(st.median([x.instret for x in ws])),
            "cycles_sum": sum(x.cycles for x in ws),
            "instret_sum": sum(x.instret for x in ws),
            "n_img": len(ws),
            "classes_per_image": {c: v / len(ws) for c, v in acc.items()},
            "crit_path": pd.get("crit_path"),
            "ipc_ideal": pd.get("ipc_ideal"),
            "ld_bytes": pd.get("ld_bytes"),
            "st_bytes": pd.get("st_bytes"),
            "n_mulh": pd.get("n_mulh"),
            "stride": pd.get("stride"),
            "mac": targets.MAC_LAYER[lay],
            "tier2_loops": tier2(pd, iss.mem, lam)[:6] if pd else [],
            "tier3": tier3(pd, iss.mem, lam, fm) if pd else {},
        }
    return {"target": t.name, "core": t.core, "timing_model": meta,
            "total_cycles_median": int(st.median(
                [sum(wd.cycles for wd in g) for g in groups])),
            "layers": layers,
            "functions": fm.names() if fm else None,
            "iss_seconds": round(iss.seconds, 2)}


def main(args, run) -> int:
    w = wrap.shadow_tree(getattr(args, "work", "s1"), say=run.say)
    if getattr(args, "all", False):
        names = [t.name for t in targets.table()]
    elif args.spec:
        names = [spec_mod.load(args.spec).target.name]
    elif getattr(args, "target", None):
        names = list(args.target)
    else:
        run.say("cần --spec, --target (lặp được), hoặc --all")
        run.finish("fail")
        return 1

    out = {}
    for name in names:
        t = targets.get(name)
        run.say("")
        run.say(f"## profile {t.name} ({t.hw})")
        pr = profile_target(t, w, run)
        out[name] = pr
        tot = pr["total_cycles_median"]
        run.say("")
        run.say("    | lớp | chu kỳ | mac | load | store | addr | loop_ctrl | requant | other |")
        run.say("    |---|---:|---:|---:|---:|---:|---:|---:|---:|")
        agg = dict.fromkeys(SEM, 0)
        # `cycles_by_sem` tính trên profile ĐÃ GỘP 10 ảnh (merge_profs), nên mẫu số
        # phải là `cycles_sum` của đúng 10 ảnh đó — KHÔNG phải trung vị 1 ảnh. Chia
        # sai phạm vi cho tỷ lệ gấp 10 lần (đã xảy ra: tổng cộng ra 1000 %).
        tot_sum = sum(pr["layers"][l]["cycles_sum"] for l in targets.LAYERS)
        for lay in targets.LAYERS:
            d = pr["layers"][lay]
            c = d["tier3"].get("cycles_by_sem", {})
            for k in SEM:
                agg[k] += c.get(k, 0)
            run.say(f"    | {lay} | {fmt_int(d['cycles_median'])} | "
                    + " | ".join(f"{100*c.get(k,0)/max(d['cycles_sum'],1):.1f} %"
                                 for k in SEM) + " |")
        run.say(f"    | **tổng** | **{fmt_int(tot)}** | "
                + " | ".join(f"**{100*agg[k]/max(tot_sum,1):.1f} %**" for k in SEM) + " |")
        pr["cycles_sum_all_layers"] = tot_sum
        pr["totals_by_sem"] = agg

    run.path("profile.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    run.say("")
    run.say(f"=> ĐẠT · {len(out)} cấu hình · profile.json")
    run.finish("ok", {"targets": list(out), "file": "profile.json"})
    return 0
