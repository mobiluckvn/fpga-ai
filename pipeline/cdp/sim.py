"""cdp sim — chạy Verilator qua Makefile có sẵn và đối chứng từng con số.

Bốn phép kiểm cho mỗi lần chạy (tiêu chí ĐẠT của S1):
  1. chu kỳ TỪNG LỚP, TỪNG ẢNH = sim.log đã ghi của giai đoạn trước, BẰNG TUYỆT ĐỐI
  2. trung vị chu kỳ/ảnh = số trong docs/KET_QUA_TONG_HOP.md
  3. CRC32 của cả 5 tensor × 10 ảnh và dự đoán = golden Python (fw/weights.h)
  4. SRC_HASH firmware tự báo = dấu vân tay mã nguồn hiện tại
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

from . import build as build_mod, provenance
from . import ledger, paths, spec as spec_mod, targets, wrap
from .util import fmt_int, rel

STEP = "S1"


def run_sim(w: Path, t, run) -> dict:
    c = wrap.make(w, t.make_dir, t.t_sim, mvars=t.make_vars, run=run,
                  log_name=f"make-{t.t_sim}.log", timeout=7200)
    log = w / t.make_dir / t.var_dir / "sim.log"
    return {"target": t.t_sim, "rc": c.rc, "seconds": round(c.seconds, 1),
            "sim_log": str(log) if log.exists() else None}


def evaluate(blk: dict, ref: dict, t, src_hash: str, run) -> dict:
    g = wrap.golden()
    cmp_ = wrap.compare_cycles(blk, ref)
    med = wrap.median_total(blk)
    med_ref = wrap.median_total(ref)
    gold = wrap.check_golden(blk, g)
    src_ok = blk.get("src") == src_hash

    run.say("")
    run.say(f"    biến thể firmware tự báo : {blk.get('variant')} "
            f"(mong đợi {t.fw_variant}) {'✓' if blk.get('variant') == t.fw_variant else '✗'}")
    run.say(f"    SRC_HASH firmware tự báo : {blk.get('src')} "
            f"(hiện tại {src_hash}) {'✓' if src_ok else '✗'}")
    run.say(f"    trung vị chu kỳ/ảnh      : {fmt_int(med)} "
            f"· bảng {fmt_int(t.expect_total_median)} "
            f"· sim.log cũ {fmt_int(med_ref)}")
    run.say(f"    chu kỳ từng lớp từng ảnh : "
            + ("BẰNG TUYỆT ĐỐI với sim.log cũ" if cmp_["equal"]
               else f"LỆCH {cmp_['n_diff']} ô"))
    for d in cmp_["diffs"][:10]:
        run.say(f"        ảnh {d['img']} {d['col']}: {d.get('got')} "
                f"≠ {d.get('ref')} (lệch {d.get('delta')})")
    run.say(f"    CRC 5 tensor × {gold['n_img']} ảnh + dự đoán = golden : "
            + ("ĐẠT" if gold["ok"] else "KHÔNG ĐẠT"))
    for p in gold["problems"][:8]:
        run.say("        " + p)

    layers = {}
    for lay in targets.LAYERS:
        layers[lay] = int(st.median([blk["cyc"][i][lay] for i in sorted(blk["cyc"])]))
    run.say("")
    run.say("    | lớp | chu kỳ (trung vị) | % tổng | MAC | chu kỳ/MAC |")
    run.say("    |---|---:|---:|---:|---:|")
    for lay in targets.LAYERS:
        mac = targets.MAC_LAYER[lay]
        v = layers[lay]
        cpm = f"{v/mac:.2f}" if mac else "—"
        run.say(f"    | {lay} | {fmt_int(v)} | {100*v/med:.1f} % | "
                f"{fmt_int(mac) if mac else '—'} | {cpm} |")

    ok = bool(cmp_["equal"] and gold["ok"] and src_ok
              and med == t.expect_total_median
              and blk.get("variant") == t.fw_variant)
    return {"pass": ok, "median_total": med, "median_ref": med_ref,
            "expect_total": t.expect_total_median,
            "variant_reported": blk.get("variant"), "src_reported": blk.get("src"),
            "src_ok": src_ok, "cycles_equal": cmp_["equal"],
            "cycles_diffs": cmp_["diffs"], "golden": gold,
            "layers_median": layers,
            "ms_27mhz": round(med / (targets.CLOCK_MHZ * 1e6) * 1000, 1),
            "cycles_per_mac": round(med / targets.MAC_TOTAL, 2)}


def main(args, run) -> int:
    if not args.spec:
        run.say("cần --spec <đặc tả.yaml>")
        run.finish("fail")
        return 1
    s = spec_mod.load(args.spec)
    t = s.target
    run.target = t.name
    run.say(f"# cdp sim · đặc tả {s.path.name} → cấu hình {t.name} ({t.hw})")

    w = wrap.shadow_tree(args.work, fresh=args.fresh, say=run.say)
    res = {"target": t.name, "spec": rel(s.path),
           "work": rel(w), "src_hash": run.src_hash}

    res["firmware"] = build_mod.ensure_firmware(w, t, run)
    if "error" in res["firmware"]:
        run.say("=> KHÔNG ĐẠT (firmware)")
        run.finish("fail", res)
        return 1

    res["sim"] = run_sim(w, t, run)
    blk = wrap.parse_m1s(Path(res["sim"]["sim_log"])) if res["sim"]["sim_log"] else None
    if not blk:
        run.say("=> KHÔNG ĐẠT: không đọc được khối M1S trong sim.log")
        run.finish("fail", res)
        return 1
    res["sim"]["total_sim_cycles"] = wrap.sim_total_cycles(Path(res["sim"]["sim_log"]))

    ref_path = wrap.recorded_sim_log(t)
    ref = wrap.parse_m1s(ref_path)
    res["reference_sim_log"] = rel(ref_path)
    if not ref:
        run.say(f"=> KHÔNG ĐẠT: không đọc được log đối chứng {ref_path}")
        run.finish("fail", res)
        return 1

    # SRC_HASH phải tính theo fw_root của CHÍNH cấu hình này, không phải của
    # experiment/m1s cho mọi cấu hình (xem provenance.src_hash_for).
    res["src_hash_target"] = provenance.src_hash_for(t)
    res["check"] = evaluate(blk, ref, t, res["src_hash_target"], run)
    s_path = s.path

    con = ledger.connect()
    rows = wrap.measurement_rows(blk, run.id, t.name, "verilator", run.src_hash)
    n = ledger.insert_measurements(con, rows)
    # Một dòng `candidates` cho mỗi cấu hình tái tạo: origin = human_replay
    # (SPEC mục 3 — đây là "ứng viên" do NGƯỜI đã làm, pipeline chỉ tái tạo lại).
    ledger.upsert_candidate(
        con, f"replay.{t.name}", origin="human_replay", round=0,
        title=f"tái tạo {t.name} ({t.hw})",
        spec_json={"target": t.as_dict(), "spec": rel(s_path)},
        status="measured_sim" if res["check"]["pass"] else "rejected",
        measured_cycles_sim=res["check"]["median_total"],
        crc_ok=1 if res["check"]["golden"]["ok"] else 0,
        src_hash=run.src_hash, git_commit=run.git.get("commit"), run_id=run.id)
    con.close()
    res["measurements_written"] = n

    # giữ bản sao log thô trong thư mục chạy
    run.path("sim.log").write_text(Path(res["sim"]["sim_log"]).read_text())
    run.path("sim.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))

    ok = res["check"]["pass"]
    run.say("")
    run.say(f"=> {'ĐẠT' if ok else 'KHÔNG ĐẠT'} · {fmt_int(res['check']['median_total'])} "
            f"chu kỳ/ảnh = {res['check']['ms_27mhz']} ms @ 27 MHz · "
            f"{res['check']['cycles_per_mac']} chu kỳ/MAC · "
            f"{n} dòng vào bảng measurements")
    run.finish("ok" if ok else "fail", res)
    return 0 if ok else 1
