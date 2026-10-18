"""cdp static — phân tích TĨNH trên mã máy, ba việc mà phân tích động không trả lời được.

Vì sao cần: phân tích động (ISS) cho biết chu kỳ đi vào đâu, nhưng để **đề xuất một
lệnh mới** còn phải biết ba thứ chỉ đọc được từ mã:

1. **Áp lực thanh ghi** trong vòng nóng. Một lệnh mới cần 2 thanh ghi nguồn + 1 đích.
   Nếu vòng đó đã dùng gần hết 31 thanh ghi thì trình biên dịch phải tràn (spill) và
   lợi ích bị ăn mất. Đây là lý do `REQ_BENCH` đo 9,56 chu kỳ/requantize nhưng thực tế
   tiết kiệm 16,6 — cạm bẫy số 6 của docs/KET_QUA_TONG_HOP.md.
2. **Phụ thuộc mang theo vòng lặp** (loop-carried dependence): qua thanh ghi và qua
   bộ nhớ. Quyết định một vòng có **vector hoá được hợp lệ** hay không, và đặt một
   chặn dưới: chu kỳ/vòng >= độ dài chuỗi hồi quy.
3. **Chỗ trống trong không gian mã lệnh**: đặt lệnh mới vào đâu mà không đụng lệnh có.

Phương pháp và giới hạn của nó, ghi rõ:
- Áp lực thanh ghi tính bằng **khoảng sống trong thân vòng** (từ lần dùng đầu tới lần
  dùng cuối của mỗi thanh ghi, theo thứ tự địa chỉ lệnh). Đây là **chặn trên** của áp
  lực thật: một thanh ghi có thể chết giữa hai lần dùng mà cách tính này không thấy.
- Thân vòng lấy là khoảng địa chỉ [đích cạnh nhảy ngược, nguồn cạnh nhảy ngược], theo
  **cạnh đã thực sự chạy** (số liệu động). Nhánh trong thân làm phép tính thành gần đúng.
- Phụ thuộc qua bộ nhớ lấy từ ISS: chỉ tính cặp (store, load) mà **cả hai** nằm trong
  cùng thân vòng — nếu không thì đó là phụ thuộc giữa các lớp, không chặn vector hoá.
"""
from __future__ import annotations

import json

from . import isa, paths, spec as spec_mod, targets, wrap
from .iss import load_timing, run_one
from .iss.core import merge_profs
from .iss.elf import FuncMap
from .profile import class_of
from .util import fmt_int, rel

STEP = "S3"
NREG = 32


def _instr_at(mem, pc):
    return mem[pc] | (mem[pc + 1] << 8) | (mem[pc + 2] << 16) | (mem[pc + 3] << 24)


def analyze_loop(mem, lam, lo, hi, pc_count, memdep, stride, trips) -> dict:
    """Phân tích tĩnh một thân vòng [lo, hi] (địa chỉ lệnh)."""
    body = [(pc, _instr_at(mem, pc)) for pc in range(lo, hi + 4, 4)
            if pc_count.get(pc, 0) > 0]
    n = len(body)
    first, last = {}, {}
    written, carried, live_in = set(), set(), set()
    height = [0] * NREG                  # chiều cao chuỗi phụ thuộc trong thân
    for i, (pc, w) in enumerate(body):
        f = isa.fields(w)
        rs = [r for r in (f["rs1"], f["rs2"]) if r]
        for r in rs + ([f["rd"]] if f["rd"] else []):
            first.setdefault(r, i)
            last[r] = i
        for r in rs:
            if r not in written:
                live_in.add(r)
        h = max([height[r] for r in rs], default=0) + lam.get(class_of(w), 1)
        if f["rd"]:
            height[f["rd"]] = h
            written.add(f["rd"])
    carried = {r for r in live_in if r in written}

    # áp lực: số thanh ghi có khoảng sống phủ vị trí i
    peak, peak_at = 0, None
    for i in range(n):
        k = sum(1 for r in first if first[r] <= i <= last[r])
        if k > peak:
            peak, peak_at = k, i

    # phụ thuộc qua bộ nhớ NỘI vòng: cả store và load đều trong thân
    md_in = {k: v for k, v in memdep.items()
             if lo <= int(k.split("->")[0], 16) <= hi
             and lo <= int(k.split("->")[1], 16) <= hi}

    # DLP: khoảng cách địa chỉ của các lệnh load trong thân
    n1 = nall = 0
    for pc_s, hist in stride.items():
        if not (lo <= int(pc_s, 16) <= hi):
            continue
        for k, v in hist.items():
            nall += v
            if abs(int(k)) == 1:
                n1 += v

    cyc = sum(pc_count.get(pc, 0) * lam.get(class_of(_instr_at(mem, pc)), 1)
              for pc in range(lo, hi + 4, 4))
    rec = max([height[r] for r in carried], default=0)
    return {
        "body": f"{lo:#x}..{hi:#x}", "static_instr": n,
        "dynamic_instr": sum(pc_count.get(pc, 0) for pc in range(lo, hi + 4, 4)),
        "trips": trips, "cycles_in_body": cyc,
        "cycles_per_trip": round(cyc / trips, 2) if trips else None,
        "regs_used": sorted(first), "n_regs_used": len(first),
        "n_regs_free": 31 - len(first),
        "peak_live": peak, "peak_at_instr": peak_at,
        "loop_carried_regs": sorted(carried),
        "recurrence_cycles": rec,
        "slack_vs_recurrence_x": round(cyc / trips / rec, 2) if (trips and rec) else None,
        "memdep_in_loop": md_in, "n_memdep_in_loop": sum(md_in.values()),
        "stride1_share_pct": round(100 * n1 / nall, 1) if nall else None,
        "lanes_possible_8bit": 4 if (nall and n1 / nall > 0.5) else None,
    }


def encoding_space(mem, pc_count) -> dict:
    """Mã lệnh nào đã dùng, chỗ nào còn trống."""
    used = {}
    for pc, k in pc_count.items():
        w = _instr_at(mem, pc)
        op = w & 0x7F
        used.setdefault(op, set()).add((w >> 12) & 7)
    core_custom = {0: "DOT4 (funct3=000, funct7=0000000)", 1: "REQ (funct3=001, funct7=số bit dịch)"}
    free_c0 = [f"{f:03b}" for f in range(8) if f not in core_custom]
    return {
        "opcodes_used_by_firmware": {f"{op:#04x}": sorted(f"{x:03b}" for x in fs)
                                     for op, fs in sorted(used.items())},
        "custom0_used": core_custom,
        "custom0_free_funct3": free_c0,
        "custom_opcodes_free": {f"{op:#04x}": name for op, name in
                                isa.CUSTOM_OPCODES.items() if op != 0x0B},
        "note": ("custom-0 (0x0B) đã dùng funct3 000 (DOT4) và 001 (REQ) — xem "
                 "rtl/mycore/mycore.v. Còn 6 mã funct3 trong custom-0, mỗi mã lại có "
                 "128 giá trị funct7, cộng toàn bộ custom-1/2/3 còn trống."),
    }


def main(args, run) -> int:
    w = wrap.shadow_tree(getattr(args, "work", "s1"), say=run.say)
    if args.spec:
        names = [spec_mod.load(args.spec).target.name]
    elif getattr(args, "target", None):
        names = list(args.target)
    else:
        names = ["B-V1", "B-V3"]
        run.say("    (không chỉ định cấu hình — mặc định B-V1 và B-V3)")
    topn = getattr(args, "loops", 3) or 3

    out = {}
    for name in names:
        t = targets.get(name)
        run.say("")
        run.say(f"## {t.name} ({t.hw})")
        iss = run_one(w, t, run, profile=True, memdep=True)
        lam, _ = load_timing(t)
        elf = w / t.fw_dir / t.fw_id / "firmware.elf"
        fm = FuncMap(elf) if elf.exists() else None
        groups = iss.layer_windows(n_img=10)
        res = {"target": name, "layers": {}}
        for li, lay in enumerate(targets.LAYERS):
            mg = merge_profs([g[li].prof for g in groups])
            pd = mg.as_dict()
            pcc = dict(mg.pc)
            loops = []
            for e, trips in list(pd["backedges"].items())[:topn]:
                a, b = (int(x, 16) for x in e.split("->"))
                d = analyze_loop(iss.mem, lam, b, a, pcc, pd["memdep"],
                                 pd["stride"], trips)
                d["backedge"] = e
                d["func"] = fm.of(b) if fm else None
                loops.append(d)
            res["layers"][lay] = {"cycles_sum10": sum(g[li].cycles for g in groups),
                                  "loops": loops}
            if not loops:
                continue
            run.say("")
            run.say(f"    ### {lay}")
            run.say("    | thân vòng | hàm | số vòng | ck/vòng | thanh ghi dùng | "
                    "còn trống | đỉnh sống | mang theo vòng | chuỗi hồi quy | dư địa | "
                    "phụ thuộc bộ nhớ nội vòng | load liên tục |")
            run.say("    |---|---|---:|---:|---:|---:|---:|---|---:|---:|---:|---:|")
            for d in loops:
                run.say(f"    | `{d['body']}` | {d['func']} | {fmt_int(d['trips'])} | "
                        f"{d['cycles_per_trip']} | {d['n_regs_used']} | "
                        f"**{d['n_regs_free']}** | {d['peak_live']} | "
                        f"{','.join('x'+str(r) for r in d['loop_carried_regs']) or '—'} | "
                        f"{d['recurrence_cycles']} | "
                        f"{str(d['slack_vs_recurrence_x'])+'×' if d['slack_vs_recurrence_x'] else '—'} | "
                        f"{fmt_int(d['n_memdep_in_loop'])} | "
                        f"{str(d['stride1_share_pct'])+' %' if d['stride1_share_pct'] is not None else '—'} |")
        res["encoding_space"] = encoding_space(iss.mem, dict(merge_profs(
            [g[li].prof for g in groups for li in range(5)]).pc))
        out[name] = res

    run.path("static.json").write_text(json.dumps(out, indent=2, ensure_ascii=False))
    enc = next(iter(out.values()))["encoding_space"]
    run.say("")
    run.say("## Không gian mã lệnh")
    run.say(f"    custom-0 (0x0b) đã dùng funct3: 000 (DOT4), 001 (REQ)")
    run.say(f"    custom-0 còn trống funct3     : {', '.join(enc['custom0_free_funct3'])}")
    run.say(f"    opcode custom còn trống hoàn toàn: "
            f"{', '.join(f'{k} ({v})' for k, v in enc['custom_opcodes_free'].items())}")
    run.say("")
    run.say(f"=> ĐẠT · {len(out)} cấu hình · static.json")
    run.finish("ok", {"targets": list(out)})
    return 0
