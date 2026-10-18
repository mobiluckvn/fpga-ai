"""cdp iss — chạy ISS và đối chứng với Verilator (bước S2, phép kiểm K0/K1).

Lý thuyết: docs/MO_HINH_CHI_PHI.md. ISS đếm $n_c$; mô hình chu kỳ cho $\\lambda_c$;
$C=\\sum n_c\\lambda_c$. Với mycore, $\\lambda$ **đọc từ RTL** nên kỳ vọng khớp TUYỆT ĐỐI.
Với PicoRV32, $\\lambda$ **hiệu chuẩn** (`cdp iss --calibrate picorv32`) nên phải báo sai số.

Cách đối chứng: ISS chạy chính `firmware.hex` đó, và firmware **tự in** số chu kỳ từng
lớp qua UART bằng `rdcycle` của chính nó. Vì vậy đầu ra UART của ISS có đúng định dạng
`M1S,*` như `sim.log` của Verilator, và so sánh là so hai khối cùng định dạng.
"""
from __future__ import annotations

import json
import statistics as st
from pathlib import Path

import yaml

from .. import build as build_mod
from .. import ledger, paths, spec as spec_mod, targets, wrap
from ..util import fmt_int, rel
from .core import CLASSES, Iss

STEP = "S2"
TIMING_DIR = Path(__file__).resolve().parent / "timing"


def load_timing(t: targets.Target) -> tuple[dict, dict]:
    """Chọn mô hình chu kỳ cho một cấu hình. Trả (bảng lambda, siêu dữ liệu)."""
    if t.core == "mycore":
        doc = yaml.safe_load((TIMING_DIR / "mycore.yaml").read_text())
        key = f"fast_addr_{int(t.rtl_params.get('FAST_ADDR', 1))}"
        if int(t.rtl_params.get("DUAL_PORT", 0)):
            key += "_dual_port"
        prof = doc["profiles"][key]
        meta = {"core": "mycore", "profile": key, "deterministic": True,
                "source": doc["derived_from"], "file": "timing/mycore.yaml"}
    else:
        f = TIMING_DIR / "picorv32.yaml"
        if not f.exists():
            raise FileNotFoundError(
                "chưa có pipeline/cdp/iss/timing/picorv32.yaml — "
                "chạy `./cdp iss --calibrate picorv32` trước")
        doc = yaml.safe_load(f.read_text())
        prof = doc["profiles"]["default"]
        meta = {"core": "picorv32", "profile": "default", "deterministic": False,
                "source": doc.get("derived_from"), "file": "timing/picorv32.yaml",
                "calibration": doc.get("calibration")}
    missing = [c for c in CLASSES if c not in prof]
    if missing:
        raise ValueError(f"mô hình chu kỳ thiếu lớp lệnh: {missing}")
    return prof, meta


def run_one(w: Path, t: targets.Target, run, pc_hist: bool = False,
            profile: bool = False, memdep: bool = False,
            max_instr: int = 400_000_000) -> Iss:
    fw = build_mod.fw_paths(w, t)["hex"]
    prof, meta = load_timing(t)
    run.say(f"    mô hình chu kỳ: {meta['file']} · hồ sơ {meta['profile']} "
            f"· {'tất định (đọc từ RTL)' if meta['deterministic'] else 'hiệu chuẩn'}")
    iss = Iss(fw, prof,
              with_dot4=bool(t.rtl_params.get("WITH_DOT4", 0)),
              with_req=bool(t.rtl_params.get("WITH_REQ", 0)),
              with_pmax4=bool(t.rtl_params.get("WITH_PMAX4", 0)),
              pc_hist=pc_hist, profile=profile,
              memdep=memdep).run(max_instr=max_instr)
    run.say(f"    ISS: {fmt_int(iss.instret)} lệnh · {iss.seconds:.1f} s "
            f"({iss.instret/max(iss.seconds,1e-9)/1000:.0f}k lệnh/s)")
    iss.timing_meta = meta
    return iss


def compare_with_verilator(iss: Iss, t: targets.Target, run, ref_log: Path | None = None):
    """So từng lớp từng ảnh giữa ISS và Verilator, và CRC với golden Python."""
    m1s = wrap.m1s_check_mod()
    blk = m1s.parse_block(iss.uart_text.splitlines())
    ref_log = ref_log or wrap.recorded_sim_log(t)
    ref = wrap.parse_m1s(ref_log)
    out = {"ref_log": rel(ref_log)}
    if not blk:
        out["error"] = "ISS không in đủ khối M1S (chạy chưa xong?)"
        return out, blk
    cmp_ = wrap.compare_cycles(blk, ref) if ref else {"equal": None, "n_diff": None,
                                                      "diffs": []}
    gold = wrap.check_golden(blk)
    med = wrap.median_total(blk)
    med_ref = wrap.median_total(ref) if ref else None
    out.update({
        "median_total_iss": med, "median_total_verilator": med_ref,
        "expect_total": t.expect_total_median,
        "cycles_equal": cmp_["equal"], "n_diff": cmp_["n_diff"],
        "diffs": cmp_["diffs"][:20],
        "golden_ok": gold["ok"], "golden_problems": gold["problems"],
        "variant_reported": blk.get("variant"), "src_reported": blk.get("src"),
        "model_cycles_total": iss.model_cycles(),
        "classes": iss.class_counts(),
    })
    if med and med_ref:
        out["rel_err_pct"] = round(100.0 * (med - med_ref) / med_ref, 4)
    # sai số từng lớp từng ảnh, tính theo phần trăm (dùng cho PicoRV32)
    errs = []
    for i in sorted(set(blk["cyc"]) & set(ref["cyc"] if ref else {})):
        for lay in targets.LAYERS + ("total",):
            a, b = blk["cyc"][i][lay], ref["cyc"][i][lay]
            if b:
                errs.append(abs(a - b) / b * 100.0)
    if errs:
        out["layer_err_max_pct"] = round(max(errs), 4)
        out["layer_err_mean_pct"] = round(sum(errs) / len(errs), 4)
    return out, blk


def layer_class_table(iss: Iss, n_img=10) -> dict:
    """n_c theo từng lớp mạng, cộng dồn trên các ảnh + trung vị chu kỳ mỗi lớp."""
    groups = iss.layer_windows(n_img=n_img)
    out = {}
    for li, lay in enumerate(targets.LAYERS):
        acc = {c: 0 for c in CLASSES}
        cyc, ins = [], []
        for g in groups:
            w = g[li]
            for c, n in zip(CLASSES, w.classes):
                acc[c] += n
            cyc.append(w.cycles)
            ins.append(w.instret)
        nimg = max(len(groups), 1)
        out[lay] = {"classes_per_image": {c: v / nimg for c, v in acc.items()},
                    "cycles_median": int(st.median(cyc)) if cyc else None,
                    "instret_median": int(st.median(ins)) if ins else None}
    return out


def _report_one(iss: Iss, t: targets.Target, cmp_out: dict, run) -> bool:
    det = iss.timing_meta["deterministic"]
    run.say("")
    run.say(f"    biến thể firmware tự báo : {cmp_out.get('variant_reported')} "
            f"(mong đợi {t.fw_variant})")
    run.say(f"    SRC_HASH                 : {cmp_out.get('src_reported')}")
    run.say(f"    trung vị ISS / Verilator : {fmt_int(cmp_out.get('median_total_iss'))}"
            f" / {fmt_int(cmp_out.get('median_total_verilator'))}"
            + (f"  (sai số {cmp_out.get('rel_err_pct')} %)"
               if cmp_out.get("rel_err_pct") is not None else ""))
    if cmp_out.get("cycles_equal"):
        run.say("    từng lớp × từng ảnh      : BẰNG TUYỆT ĐỐI với Verilator")
    else:
        run.say(f"    từng lớp × từng ảnh      : lệch {cmp_out.get('n_diff')} ô · "
                f"sai số lớn nhất {cmp_out.get('layer_err_max_pct')} % · "
                f"trung bình {cmp_out.get('layer_err_mean_pct')} %")
        for d in cmp_out.get("diffs", [])[:5]:
            run.say(f"        ảnh {d['img']} {d['col']}: {d.get('got')} "
                    f"≠ {d.get('ref')} (lệch {d.get('delta')})")
    run.say(f"    CRC 5 tensor × 10 ảnh    : "
            + ("khớp golden" if cmp_out.get("golden_ok") else "LỆCH"))
    ok = bool(cmp_out.get("golden_ok"))
    if det:
        ok = ok and bool(cmp_out.get("cycles_equal"))
    else:
        ok = ok and (cmp_out.get("layer_err_max_pct") is not None
                     and cmp_out["layer_err_max_pct"] <= 2.0)
    run.say(f"    => {'ĐẠT' if ok else 'KHÔNG ĐẠT'} "
            f"(tiêu chí: {'bằng tuyệt đối' if det else 'sai số ≤ 2 %'})")
    return ok


def main(args, run) -> int:
    from . import calibrate as cal_mod                      # nạp muộn
    w = wrap.shadow_tree(getattr(args, "work", "s1"), say=run.say)

    if getattr(args, "calibrate", None):
        return cal_mod.main(args, run, w)

    if getattr(args, "check_k1", False):
        from . import checks
        return checks.main(args, run, w)

    if getattr(args, "all", False):
        names = [t.name for t in targets.table()]
    elif args.spec:
        names = [spec_mod.load(args.spec).target.name]
    elif getattr(args, "target", None):
        names = [args.target]
    else:
        run.say("cần --spec <đặc tả.yaml>, hoặc --target <tên>, hoặc --all")
        run.finish("fail")
        return 1

    res = {"configs": {}, "work": rel(w)}
    allok = True
    con = ledger.connect()
    for name in names:
        t = targets.get(name)
        run.say("")
        run.say(f"## {t.name} ({t.hw}) · firmware {t.fw_id}")
        fw = build_mod.ensure_firmware(w, t, run)
        if "error" in fw:
            res["configs"][name] = {"error": "không dựng được firmware"}
            allok = False
            continue
        try:
            iss = run_one(w, t, run, pc_hist=getattr(args, "pc_hist", False))
        except FileNotFoundError as exc:
            run.say(f"    BỎ QUA: {exc}")
            res["configs"][name] = {"skipped": str(exc)}
            allok = False
            continue
        cmp_out, blk = compare_with_verilator(iss, t, run)
        ok = _report_one(iss, t, cmp_out, run) if "error" not in cmp_out else False
        if "error" in cmp_out:
            run.say(f"    LỖI: {cmp_out['error']}")
        allok &= ok
        cmp_out["layers"] = layer_class_table(iss)
        cmp_out["pass"] = ok
        cmp_out["iss_seconds"] = round(iss.seconds, 2)
        cmp_out["timing_model"] = iss.timing_meta
        res["configs"][name] = cmp_out
        if blk:
            ledger.insert_measurements(
                con, wrap.measurement_rows(blk, run.id, t.name, "iss", run.src_hash))
        run.path("uart", f"{t.name}.txt").write_text(iss.uart_text)
    con.close()

    run.path("iss.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    run.say("")
    run.say("| cấu hình | lõi | ISS | Verilator | sai số lớn nhất | ĐẠT |")
    run.say("|---|---|---:|---:|---:|---|")
    for name, c in res["configs"].items():
        if "median_total_iss" not in c:
            run.say(f"| {name} | — | — | — | — | BỎ QUA |")
            continue
        run.say(f"| {name} | {targets.get(name).core} | "
                f"{fmt_int(c['median_total_iss'])} | "
                f"{fmt_int(c['median_total_verilator'])} | "
                f"{c.get('layer_err_max_pct', 0)} % | "
                f"{'ĐẠT' if c['pass'] else 'KHÔNG'} |")
    run.say("")
    run.say(f"=> {'ĐẠT' if allok else 'KHÔNG ĐẠT'}")
    run.finish("ok" if allok else "fail", res)
    return 0 if allok else 1
