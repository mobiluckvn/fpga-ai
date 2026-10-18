"""cdp b1 — vòng tối ưu PHẦN MỀM có AI hỗ trợ (bước S4), chế độ mù.

Kiến trúc: `cdp` làm phần tất định, AI làm phần đề xuất. Hai phần chạy xen kẽ:

    cdp b1 prepare            sinh experiment/m1s_b1/ + cổng kiểm (kernels_v0.c = B-V0)
    cdp b1 sandbox            dựng pipeline/runs/<id>/sandbox/ cho vòng hiện tại
    (người điều phối gọi subagent MÙ, nó ghi cand_*.c vào sandbox đó)
    cdp b1 eval  --sandbox …  dựng + đo từng ứng viên, chấm, cập nhật bản tốt nhất

Vì sao tách làm hai lệnh: subagent chỉ được đọc đúng các file trong sandbox (SPEC 4.6),
và mọi con số phán quyết phải do công cụ tất định tạo ra (SPEC 0.1). `cdp` không tự gọi
AI — người điều phối gọi, và lời gọi được ghi lại trong `ai/` của thư mục chạy.

Giới hạn phải ghi rõ: chế độ mù ở đây được bảo đảm bằng **chỉ thị**, không bằng
sandbox hệ điều hành — subagent vẫn chạy trên cùng hệ thống file. Mọi file được cấp
đều ghi trong meta.json để người đọc tự kiểm.
"""
from __future__ import annotations

import json
import shutil
import statistics as st
from pathlib import Path

import yaml

from .. import ledger, paths, targets, wrap
from ..iss.core import Iss
from ..util import fmt_int, rel
from . import prepare as prep_mod
from .report import variant_report

STEP = "S4"
STATE = paths.PIPELINE / "runs" / "b1_state.json"
B1 = paths.ROOT / "experiment" / "m1s_b1"
BASE = targets.get("B-V0")          # điểm xuất phát: C thẳng trên mycore gốc
GOAL = targets.get("B-V1")          # mốc thủ công cần so (KHÔNG cấp cho subagent)


def _timing():
    doc = yaml.safe_load((paths.CDP / "iss/timing/mycore.yaml").read_text())
    return doc["profiles"]["fast_addr_1"]


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text())
    return {"round": 0, "best_kernels": "kernels_v0.c", "best_cycles": None,
            "history": []}


def save_state(s: dict) -> None:
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=2, ensure_ascii=False))


def build_variant(w: Path, kernels_rel: str, out: str, run) -> Path | None:
    """make fw KERNELS=<file> OUT=<dir> trong cây bóng."""
    c = wrap.make(w, "experiment/m1s_b1", "fw", mvars={"KERNELS": kernels_rel,
                                                       "OUT": out},
                  run=run, log_name=f"make-fw-{out}.log")
    hexf = w / "experiment/m1s_b1" / out / "firmware.hex"
    return hexf if (c.ok and hexf.exists()) else None


def measure(hexf: Path) -> dict:
    """Chạy ISS, trả chu kỳ/lớp + CRC đúng bit hay không. Đây là phán quyết."""
    iss = Iss(hexf, _timing()).run()
    blk = wrap.m1s_check_mod().parse_block(iss.uart_text.splitlines())
    if not blk:
        return {"ok": False, "error": "firmware không in đủ khối M1S"}
    gold = wrap.check_golden(blk)
    tot = [blk["cyc"][i]["total"] for i in sorted(blk["cyc"])]
    layers = {lay: int(st.median([blk["cyc"][i][lay] for i in sorted(blk["cyc"])]))
              for lay in targets.LAYERS}
    return {"ok": True, "bit_exact": gold["ok"], "problems": gold["problems"],
            "median_cycles": int(st.median(tot)), "layers": layers,
            "instret": int(st.median([blk["cyc"][i]["instret"] for i in sorted(blk["cyc"])])),
            "src_hash": blk.get("src"), "iss_seconds": round(iss.seconds, 1)}


# --------------------------------------------------------------- lệnh con
def cmd_prepare(args, run) -> int:
    run.say("# cdp b1 prepare — tách kernel C thẳng ra file riêng, rồi KIỂM")
    info = prep_mod.main_prepare(say=run.say)
    if info["leaked"]:
        run.say(f"=> KHÔNG ĐẠT: còn lọt macro {info['leaked']} trong kernels_v0.c")
        run.finish("fail", info)
        return 1
    w = wrap.shadow_tree(getattr(args, "work", "s1"), say=run.say)
    run.say("")
    run.say("## Cổng kiểm: bản tách ra phải cho ĐÚNG số của B-V0")
    hexf = build_variant(w, "kernels_v0.c", "v0", run)
    if not hexf:
        run.finish("fail", {"error": "không dựng được firmware gốc"})
        return 1
    m = measure(hexf)
    ref = wrap.parse_m1s(wrap.recorded_sim_log(BASE))
    blk_ok = m["median_cycles"] == BASE.expect_total_median
    iss = Iss(hexf, _timing()).run()
    cmp_ = wrap.compare_cycles(wrap.m1s_check_mod().parse_block(
        iss.uart_text.splitlines()), ref)
    run.say(f"    trung vị chu kỳ/ảnh : {fmt_int(m['median_cycles'])} "
            f"(B-V0 đã đo {fmt_int(BASE.expect_total_median)})")
    run.say(f"    từng lớp × từng ảnh : "
            + ("BẰNG TUYỆT ĐỐI" if cmp_["equal"] else f"LỆCH {cmp_['n_diff']} ô"))
    run.say(f"    CRC 5 tensor × 10 ảnh: "
            + ("khớp golden" if m["bit_exact"] else "LỆCH"))
    ok = bool(blk_ok and cmp_["equal"] and m["bit_exact"])
    if ok:
        s = load_state()
        s["best_cycles"] = m["median_cycles"]
        s["baseline_cycles"] = m["median_cycles"]
        save_state(s)
    run.say("")
    run.say(f"=> {'ĐẠT' if ok else 'KHÔNG ĐẠT'} (hạ tầng B1 "
            + ("đáng tin, bắt đầu vòng lặp được" if ok else "SAI — không được dùng") + ")")
    run.finish("ok" if ok else "fail",
               {"gate": ok, "measure": m, "cycles_equal": cmp_["equal"]})
    return 0 if ok else 1


def cmd_sandbox(args, run) -> int:
    s = load_state()
    rnd = s["round"] + 1
    w = wrap.shadow_tree(getattr(args, "work", "s1"), say=run.say)
    sb = run.path("sandbox")
    sb.mkdir(parents=True, exist_ok=True)
    cur = B1 / s["best_kernels"] if (B1 / s["best_kernels"]).exists() else \
        paths.ROOT / s["best_kernels"]
    shutil.copy(cur, sb / "kernels.c")

    # profile của CHÍNH biến thể hiện tại — đây là thứ duy nhất nói về hiệu năng
    out = f"cur_r{rnd}"
    hexf = build_variant(w, str(Path(cur).name) if Path(cur).parent == B1
                         else str(cur), out, run)
    if not hexf:
        run.finish("fail", {"error": "không dựng được biến thể hiện tại"})
        return 1
    rep, meas = variant_report(hexf, w, out)
    (sb / "PROFILE.md").write_text(rep)
    shutil.copy(paths.PIPELINE / "prompts" / "b1_sw_opt.md", sb / "TASK.md")
    files = sorted(p.name for p in sb.iterdir())
    run.say("")
    run.say(f"## sandbox vòng {rnd}: {rel(sb)}")
    run.say(f"    file được cấp: {', '.join(files)}")
    run.say(f"    biến thể hiện tại: {s['best_kernels']} · "
            f"{fmt_int(meas['median_cycles'])} chu kỳ/ảnh")
    run.say("")
    run.say("    Bước tiếp theo (người điều phối làm): gọi subagent MÙ với đúng ba file")
    run.say("    trên, yêu cầu ghi tối đa 3 ứng viên cand_a.c / cand_b.c / cand_c.c vào")
    run.say(f"    {rel(sb)}, rồi chạy:")
    run.say(f"      ./cdp b1 eval --sandbox {rel(sb)}")
    run.finish("ok", {"round": rnd, "sandbox": rel(sb), "files_given": files,
                      "current_cycles": meas["median_cycles"],
                      "blind_note": ("chế độ mù bảo đảm bằng chỉ thị, không bằng "
                                     "sandbox hệ điều hành")})
    return 0


def cmd_eval(args, run) -> int:
    sb = Path(args.sandbox)
    if not sb.is_absolute():
        sb = paths.ROOT / sb
    if not sb.exists():
        run.say(f"không thấy sandbox {sb}")
        run.finish("fail")
        return 1
    s = load_state()
    rnd = s["round"] + 1
    w = wrap.shadow_tree(getattr(args, "work", "s1"), say=run.say)
    cands = sorted(sb.glob("cand_*.c"))
    if not cands:
        run.say(f"không có ứng viên nào (cand_*.c) trong {rel(sb)}")
        run.finish("fail")
        return 1
    run.say(f"# cdp b1 eval — vòng {rnd} · {len(cands)} ứng viên")
    base = s.get("baseline_cycles") or BASE.expect_total_median
    best_prev = s.get("best_cycles") or base
    con = ledger.connect()
    rows = []
    for i, c in enumerate(cands):
        tag = f"r{rnd}{c.stem.split('_')[-1]}"
        dst = B1 / "rounds" / f"{tag}.c"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(c, dst)
        # cây bóng cần thấy file mới
        wrap.shadow_tree(getattr(args, "work", "s1"), say=lambda *a: None)
        hexf = build_variant(w, f"rounds/{tag}.c", tag, run)
        if not hexf:
            rows.append({"cand": c.name, "tag": tag, "built": False,
                         "note": "không biên dịch được"})
            run.say(f"    {c.name}: KHÔNG biên dịch được")
            continue
        m = measure(hexf)
        rows.append({"cand": c.name, "tag": tag, "built": True, **m})
        verdict = ("ĐÚNG BIT" if m.get("bit_exact") else "SAI KẾT QUẢ")
        sp = base / m["median_cycles"] if m.get("median_cycles") else None
        run.say(f"    {c.name}: {fmt_int(m.get('median_cycles'))} chu kỳ "
                f"({sp:.3f}× so B-V0) · {verdict}")
        for p in m.get("problems", [])[:3]:
            run.say(f"        {p}")
        ledger.upsert_candidate(
            con, f"b1.{tag}", origin="ai", round=rnd, level=None,
            title=f"B1 vòng {rnd} ứng viên {c.stem.split('_')[-1]}",
            spec_json={"kernels": f"experiment/m1s_b1/rounds/{tag}.c",
                       "sandbox": rel(sb)},
            status="measured_sim" if m.get("bit_exact") else "rejected",
            measured_cycles_sim=m.get("median_cycles"),
            crc_ok=1 if m.get("bit_exact") else 0,
            src_hash=m.get("src_hash"), git_commit=run.git.get("commit"),
            run_id=run.id)
    con.close()

    valid = [r for r in rows if r.get("bit_exact")]
    best = min(valid, key=lambda r: r["median_cycles"]) if valid else None
    s["round"] = rnd
    rec = {"round": rnd, "sandbox": rel(sb), "candidates": rows,
           "best_this_round": best["tag"] if best else None,
           "best_cycles_this_round": best["median_cycles"] if best else None}
    improved_pct = None
    if best and best["median_cycles"] < best_prev:
        improved_pct = 100.0 * (best_prev - best["median_cycles"]) / best_prev
        s["best_kernels"] = f"rounds/{best['tag']}.c"
        s["best_cycles"] = best["median_cycles"]
    rec["improved_pct"] = improved_pct
    s["history"].append(rec)
    save_state(s)

    run.say("")
    run.say(f"    tốt nhất vòng này : "
            + (f"{best['tag']} · {fmt_int(best['median_cycles'])} chu kỳ" if best
               else "không có ứng viên nào đúng bit"))
    run.say(f"    bản tốt nhất hiện tại: {s['best_kernels']} · "
            f"{fmt_int(s['best_cycles'])} chu kỳ "
            f"({base / s['best_cycles']:.3f}× so B-V0)")
    run.say(f"    cải thiện vòng này: "
            + (f"{improved_pct:.2f} %" if improved_pct else "0 %"))
    run.say(f"    mốc thủ công (KHÔNG cấp cho subagent): B-V1 = "
            f"{fmt_int(GOAL.expect_total_median)} chu kỳ "
            f"({base / GOAL.expect_total_median:.3f}× so B-V0)")
    hist = [h.get("improved_pct") or 0.0 for h in s["history"]]
    stop = len(hist) >= 2 and hist[-1] < 2.0 and hist[-2] < 2.0
    run.say("")
    run.say(f"=> {'DỪNG' if stop else 'tiếp vòng sau'} "
            + ("(2 vòng liên tiếp cải thiện < 2 %)" if stop else ""))
    run.path("round.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
    run.finish("ok", {"round": rnd, "best": s["best_kernels"],
                      "best_cycles": s["best_cycles"], "stop": stop})
    return 0


def main(args, run) -> int:
    act = getattr(args, "action", None)
    if act == "prepare":
        return cmd_prepare(args, run)
    if act == "sandbox":
        return cmd_sandbox(args, run)
    if act == "eval":
        return cmd_eval(args, run)
    run.say("dùng: cdp b1 prepare | sandbox | eval --sandbox <đường dẫn>")
    run.finish("fail")
    return 1
