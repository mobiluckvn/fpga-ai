"""cdp estimate — dự báo cho từng ứng viên, GHI TRƯỚC khi hiện thực (SPEC 0.3).

Ba mức dự báo, phân biệt rõ vì độ tin cậy khác nhau hẳn:

**A. Đổi λ (tầng L3) — CHÍNH XÁC theo mô hình.**
   ΔC = Σ_c n_c · Δλ_c. Không cần viết RTL, không cần đổi firmware. Mô hình này đã
   khớp tuyệt đối với RTL trên 14 cấu hình (S2) và cả trên mã mới do AI sinh (S4),
   nên dự báo ở đây có cùng độ tin cậy với một phép đo.

**B. Gộp/vector hoá một mẫu lệnh (L1/L2) — CHẶN DƯỚI của lợi ích.**
   ΔC = n_mẫu · (Σ_{i∈mẫu} λ_i − λ_mới). Đây là **chặn dưới**: nó chỉ tính phần lệnh
   bị thay trực tiếp, không tính việc biến đổi mã còn cắt thêm chi phí tính địa chỉ và
   điều khiển vòng. Số đo thật sẽ TỐT HƠN dự báo này — và mức tốt hơn bao nhiêu chính
   là một kết quả của PQ1.

**C. Chặn trên kiểu Amdahl — cho MỌI ứng viên.**
   Nếu xoá sạch lớp công việc bị nhắm tới: tăng tốc ≤ 1/(1−f). Dùng cho L4/L5 và cho
   mọi ứng viên chưa đủ đặc tả để tính A hoặc B. Đây là **chặn trên**, không phải dự báo.

Mọi con số dùng n_c **đo được** từ ISS, và λ **đọc từ RTL**. Không có hệ số tay.
"""
from __future__ import annotations

import csv
import json
import statistics as st
from pathlib import Path

import yaml

from . import ledger, paths, targets
from .util import fmt_int, rel

STEP = "S6"
SEM = ("mac", "load_data", "store_data", "addr", "loop_ctrl", "requant", "other")


def _lam(t: targets.Target) -> dict:
    doc = yaml.safe_load((paths.CDP / "iss/timing/mycore.yaml").read_text())
    return doc["profiles"][f"fast_addr_{int(t.rtl_params.get('FAST_ADDR', 1))}"]


def _load(name: str) -> tuple[dict, dict]:
    an = json.loads((paths.RESULTS_PIPE / "S3" / "analysis.json").read_text())[name]
    pr = json.loads((paths.RESULTS_PIPE / "S3" / "profile.json").read_text())[name]
    return an, pr


def nc_per_image(pr: dict, layers=None) -> dict:
    """Số lệnh động theo lớp lệnh, cho một ảnh, cộng trên các lớp mạng chỉ định."""
    out = {}
    for l in (layers or targets.LAYERS):
        for k, v in pr["layers"][l].get("classes_per_image", {}).items():
            out[k] = out.get(k, 0) + v
    return out


# ------------------------------------------------------- A. đổi λ (chính xác)
def est_lambda(base: str, dlam: dict) -> dict:
    t = targets.get(base)
    an, pr = _load(base)
    lam = _lam(t)
    nc = nc_per_image(pr)
    C = an["total_cycles"]
    d = 0.0
    terms = []
    for cls, new in dlam.items():
        n = nc.get(cls, 0)
        old = lam.get(cls)
        if old is None or not n:
            continue
        delta = n * (old - new)
        d += delta
        terms.append({"class": cls, "n_c": round(n, 1), "lambda_old": old,
                      "lambda_new": new, "delta_cycles": round(delta, 1)})
    Cp = C - d
    return {"method": "A_lambda_exact", "base_cycles": C,
            "predicted_cycles": int(round(Cp)),
            "predicted_speedup": round(C / Cp, 4) if Cp > 0 else None,
            "formula": "ΔC = Σ n_c·(λ_cũ − λ_mới)", "terms": terms,
            "confidence": ("chính xác theo mô hình đã kiểm khớp tuyệt đối với RTL "
                           "trên 14 cấu hình (S2) và trên mã mới (S4)")}


# ------------------------------------------------- B. gộp mẫu lệnh (chặn dưới)
def est_pattern(base: str, name: str, layers: list[str], per_group: dict,
                replaced_per_group: dict, groups: float, note: str) -> dict:
    """ΔC = số_nhóm · (Σ λ của lệnh bị thay − Σ λ của lệnh mới)."""
    t = targets.get(base)
    an, _pr = _load(base)
    lam = _lam(t)
    before = sum(lam[c] * k for c, k in replaced_per_group.items())
    after = sum(lam.get(c, 1) * k for c, k in per_group.items())
    d = groups * (before - after)
    C = an["total_cycles"]
    Cp = C - d
    return {"method": "B_pattern_lower_bound", "base_cycles": C,
            "predicted_cycles": int(round(Cp)),
            "predicted_speedup": round(C / Cp, 4) if Cp > 0 else None,
            "formula": "ΔC = n_nhóm · (Σλ_bị_thay − Σλ_mới)",
            "groups": groups, "layers": layers,
            "cycles_per_group_before": before, "cycles_per_group_after": after,
            "replaced_per_group": replaced_per_group, "new_per_group": per_group,
            "confidence": "CHẶN DƯỚI — không tính phần cắt thêm chi phí địa chỉ/vòng lặp",
            "note": note}


# -------------------------------------------- C. chặn trên Amdahl (mọi ứng viên)
def est_ceiling(base: str, classes: list[str], layers=None) -> dict:
    an, _ = _load(base)
    C = an["total_cycles"]
    if layers:
        cyc = sum(an["layers"][l]["cycles_by_sem"].get(c, 0) / 10.0
                  for l in layers for c in classes)
    else:
        cyc = sum(an["cycles_by_sem_total"].get(c, 0) for c in classes)
    f = cyc / C
    return {"method": "C_amdahl_ceiling", "base_cycles": C,
            "targeted_cycles": int(round(cyc)), "fraction": round(f, 4),
            "max_speedup": round(1 / (1 - f), 4) if f < 1 else None,
            "formula": "tăng tốc ≤ 1/(1−f)", "classes": classes, "layers": layers,
            "confidence": "CHẶN TRÊN, không phải dự báo"}


# --------------------------------------------------- dự báo cấu trúc cho ứng viên ưu tiên
def priority_estimates() -> list[dict]:
    """Dự báo chi tiết cho các ứng viên sẽ hiện thực. Mọi tham số lấy từ số ĐO.

    Ba trong số này đã có số đo thật của giai đoạn trước (DOT4, bố cục, REQ), nên so
    được ngay — đó là phép kiểm PQ1 cho tầng L1/L2 mà KHÔNG cần viết thêm RTL.
    """
    out = []
    an_b1, pr_b1 = _load("B-V1")
    lam = _lam(targets.get("B-V1"))

    # --- DOT4: nhân-cộng 4 làn. Áp được ở conv2 và dense (kênh vào liền địa chỉ);
    #     conv1 KHÔNG áp được vì cửa sổ 3x3 không liền 4 byte -> cần đổi bố cục trước.
    mac = targets.MAC_LAYER
    groups = (mac["conv2"] + mac["dense"]) / 4.0
    e = est_pattern("B-V1", "DOT4", ["conv2", "dense"],
                    per_group={"load": 2, "custom_dot4": 1, "alu": 1},
                    replaced_per_group={"load": 4, "mul": 4, "alu": 4},
                    groups=groups,
                    note=("Mỗi nhóm 4 MAC: trước = 4 nạp byte + 4 nhân + 4 cộng dồn; "
                          "sau = 2 nạp từ 32 bit + 1 lệnh 4 làn + 1 cộng dồn. "
                          "conv1 không áp được: cửa sổ 3×3 không liền 4 byte."))
    e.update({"candidate": "DOT4 (nhân-cộng SIMD 4 làn int8)", "level": "L2",
              "measured_target": "B-V1+DOT4", "measured_cycles": 631130})
    out.append(e)

    # --- Bố cục dữ liệu: cho conv1 dùng được lệnh 4 làn. Dự báo bằng cách áp cùng
    #     mô hình nhóm-4 cho conv1, trừ chi phí phụ (ghi đệm 4 pha).
    an_d, pr_d = _load("B-V1+DOT4")
    g1 = mac["conv1"] / 4.0
    e2 = est_pattern("B-V1+DOT4", "LAYOUT", ["conv1"],
                     per_group={"load": 2, "custom_dot4": 1, "alu": 1},
                     replaced_per_group={"load": 4, "mul": 4, "alu": 4},
                     groups=g1,
                     note=("Áp cùng mô hình nhóm-4 cho conv1 sau khi đổi bố cục. "
                           "CHƯA trừ chi phí dựng đệm bố cục (ghi thêm ~3,6 KB/ảnh), "
                           "nên đây là chặn dưới của chi phí và chặn trên của lợi ích."))
    e2.update({"candidate": "Bố cục dữ liệu cho conv1 dùng được lệnh 4 làn",
               "level": "L2", "measured_target": "B-V1+DOT4+C1",
               "measured_cycles": 487865})
    out.append(e2)

    # --- REQ: gộp chuỗi lượng tử hoá lại thành MỘT lệnh (2 chu kỳ, đi qua khối nhân).
    an_c, pr_c = _load("B-V1+DOT4+C1")
    n_req = 26 * 26 * 8 + 11 * 11 * 16          # số lần requantize mỗi ảnh (cấu trúc)
    cyc_req = an_c["cycles_by_sem_total"]["requant"]
    C = an_c["total_cycles"]
    new = n_req * lam["custom_req"]
    Cp = C - (cyc_req - new)
    out.append({
        "candidate": "REQ (gộp chuỗi lượng tử hoá lại thành một lệnh)", "level": "L1",
        "method": "B2_class_replacement_lower_bound", "base_config": "B-V1+DOT4+C1",
        "base_cycles": C, "predicted_cycles": int(round(Cp)),
        "predicted_speedup": round(C / Cp, 4),
        "formula": "ΔC = (chu kỳ lớp `requant` đo được) − n_lần · λ_lệnh_mới",
        "terms": [{"requant_cycles_measured": int(cyc_req), "n_calls": n_req,
                   "lambda_new": lam["custom_req"], "new_cycles": new}],
        "confidence": ("CHẶN DƯỚI — chỉ tính phần profile đã gán vào lớp `requant`; "
                       "phần số học của phép nhân 64 bit bị gán vào lớp `mac` không "
                       "được tính vào đây"),
        "measured_target": "B-V3", "measured_cycles": 365992})

    # --- PMAX4: lệnh lấy max 4 làn cho hai lớp pooling (ứng viên MỚI, chưa ai làm).
    an_v3, pr_v3 = _load("B-V3")
    cp = est_ceiling("B-V3", ["other", "loop_ctrl", "addr", "load_data"],
                     layers=["pool1", "pool2"])
    cp.update({"candidate": "PMAX4 (lấy max gói 4 làn int8 cho pooling)", "level": "L2",
               "base_config": "B-V3",
               "note": ("Hai lớp pooling không có phép nhân nào nên DOT4 vô dụng ở đó. "
                        "Đây là chặn trên: xoá sạch công việc so sánh/chọn + nạp + "
                        "điều khiển vòng của hai lớp đó.")})
    out.append(cp)

    # --- L3: bộ nhớ hai cổng, và nhân 1 chu kỳ — dự báo CHÍNH XÁC theo mô hình.
    for name, dl, lv in (
            ("Bộ nhớ hai cổng (load/store 2 → 1 chu kỳ)", {"load": 1, "store": 1}, "L3"),
            ("Nhân 1 chu kỳ (λ_mul 2 → 1)", {"mul": 1}, "L3"),
            # Trên B-V3 thì n_mul = 0 (mọi MAC đã là lệnh 4 làn, requantize đã là một
            # lệnh), nên "nhân 1 chu kỳ" cho đúng 1,000×. Muốn hạ chi phí số học ở B-V3
            # thì phải hạ λ của chính lệnh requantize -> thêm biến thể này cho rõ.
            ("Hạ λ của lệnh lượng tử hoá lại (2 → 1 chu kỳ)", {"custom_req": 1}, "L3"),
            ("Cả hai: bộ nhớ hai cổng + mọi phép nhân 1 chu kỳ",
             {"load": 1, "store": 1, "mul": 1, "custom_req": 1}, "L3")):
        for base in ("B-V1", "B-V3"):
            e3 = est_lambda(base, dl)
            e3.update({"candidate": name, "level": lv, "base_config": base})
            out.append(e3)
    return out


# ------------------------------------------------- chặn trên cho MỌI ứng viên của S5
# Ánh xạ từ chữ trong trường `target`/`title` của ứng viên sang lớp công việc bị nhắm.
TARGET_CLASSES = [
    (r"requant|lượng tử", ["requant"]),
    (r"\bmac\b|nhân|multipl|dot|tích vô hướng", ["mac", "load_data"]),
    (r"load|nạp|bộ nhớ|memory|byte", ["load_data", "store_data"]),
    (r"pool|max", ["other", "loop_ctrl"]),
    (r"addr|địa chỉ|index|chỉ số", ["addr"]),
    (r"loop|vòng lặp", ["loop_ctrl"]),
    (r"issue|phát .*lệnh|dual", list(SEM)),
]


def ceiling_for_candidate(base: str, c: dict) -> dict:
    import re
    txt = f"{c.get('title','')} {c.get('target','')} {c.get('expected_mechanism','')}"
    for pat, classes in TARGET_CLASSES:
        if re.search(pat, txt, re.I):
            e = est_ceiling(base, classes)
            e["matched_pattern"] = pat
            return e
    e = est_ceiling(base, list(SEM))
    e["matched_pattern"] = "(không khớp mẫu nào — lấy toàn bộ)"
    return e


def main(args, run) -> int:
    base = getattr(args, "target", None) or "B-V1"
    files = sorted((paths.RESULTS_PIPE / "S5" / "candidates").glob("blind_*.json")) + \
        [paths.RESULTS_PIPE / "S5" / "candidates" / "rules.json"]
    files = [f for f in files if f.exists()]
    run.say(f"# cdp estimate · cơ sở {base} · {len(files)} tệp ứng viên")
    run.say("    SPEC 0.3: dự báo ghi vào sổ cái TRƯỚC khi hiện thực, không sửa lùi.")

    # ---------- 1. dự báo cấu trúc cho ứng viên ưu tiên ----------
    pri = priority_estimates()
    run.say("")
    run.say("## 1. Dự báo cấu trúc cho các ứng viên ưu tiên")
    run.say("")
    run.say("| ứng viên | tầng | cơ sở | phương pháp | dự báo | tăng tốc dự báo | đo thật | sai số |")
    run.say("|---|---|---|---|---:|---:|---:|---:|")
    for e in pri:
        mc = e.get("measured_cycles")
        sp = e.get("predicted_speedup")
        bc = e.get("base_cycles")
        msp = (bc / mc) if (mc and bc) else None
        err = (f"{100*(sp-msp)/msp:+.1f} %" if (sp and msp) else "—")
        run.say(f"| {e['candidate']} | {e['level']} | {e.get('base_config', base)} | "
                f"{e['method'].split('_')[0]} | "
                f"{fmt_int(e.get('predicted_cycles')) if e.get('predicted_cycles') else '—'} | "
                f"{sp if sp else ('≤ ' + str(e.get('max_speedup')))} | "
                f"{fmt_int(mc) if mc else '—'} | {err} |")

    # ---------- 2. chặn trên cho mọi ứng viên ----------
    rows, con = [], ledger.connect()
    for f in files:
        doc = json.loads(f.read_text())
        for c in doc["candidates"]:
            e = ceiling_for_candidate(base, c)
            rid = f"{doc['origin']}.{doc.get('mode', 'open')}.{c['id']}"[:120]
            rows.append({
                "file": f.name, "origin": doc["origin"], "mode": doc.get("mode"),
                "cand_id": c["id"], "level": c["level"], "title": c["title"][:90],
                "targeted_classes": ",".join(e["classes"]),
                "fraction": e["fraction"], "max_speedup": e["max_speedup"],
                "method": e["method"], "estimate_method_declared": c.get("estimate_method"),
                # Có đủ đặc tả để dự báo tự động không?
                "has_timing_changes": bool((c.get("spec") or {}).get("timing_changes")),
                "has_full_instr_spec": bool(
                    (c.get("spec") or {}).get("encoding")
                    and (c.get("spec") or {}).get("semantics_python")
                    and (c.get("spec") or {}).get("latency_cycles") is not None),
            })
            ledger.upsert_candidate(
                con, rid, origin=doc["origin"], round=1, level=c["level"],
                title=c["title"][:200],
                spec_json={"candidate": c, "estimate": e, "base_config": base},
                status="estimated",
                predicted_speedup=e["max_speedup"],
                predicted_cost_json={"note": "chặn trên Amdahl, chưa có chi phí phần cứng"},
                git_commit=run.git.get("commit"), run_id=run.id)
    # ghi cả dự báo ưu tiên vào sổ cái
    for e in pri:
        rid = "priority." + e["candidate"].split("(")[0].strip()[:60]
        ledger.upsert_candidate(
            con, rid, origin="pipeline", round=1, level=e["level"],
            title=e["candidate"][:200], spec_json=e, status="estimated",
            predicted_cycles=e.get("predicted_cycles"),
            predicted_speedup=e.get("predicted_speedup") or e.get("max_speedup"),
            measured_cycles_sim=e.get("measured_cycles"),
            git_commit=run.git.get("commit"), run_id=run.id)
    con.close()

    out = paths.RESULTS_PIPE / "S6"
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "estimates_all_candidates.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    (out / "estimates_priority.json").write_text(
        json.dumps(pri, indent=2, ensure_ascii=False))
    run.path("estimates.json").write_text(
        json.dumps({"priority": pri, "all": rows}, indent=2, ensure_ascii=False))

    run.say("")
    run.say(f"## 2. Dự báo được tới đâu? ({len(rows)} ứng viên)")
    run.say("")
    run.say("Chặn trên Amdahl tính được cho **mọi** ứng viên, nhưng nó **không phân biệt**")
    run.say("được chúng: hầu hết ứng viên đều nhắm `mac`+`load_data`, cộng lại 85 % chu kỳ,")
    run.say("nên chặn trên của chúng gần như bằng nhau. Vì vậy chọn top-K **không** dùng")
    run.say("chặn trên, mà dùng dự báo cấu trúc (phương pháp A hoặc B) — và chỉ một phần")
    run.say("ứng viên đủ đặc tả để làm được việc đó:")
    run.say("")
    run.say("| tầng | ứng viên | có `timing_changes` → dự báo A (chính xác) | "
            "có mã hoá + ngữ nghĩa + độ trễ → dự báo B | chỉ có chặn trên |")
    run.say("|---|---:|---:|---:|---:|")
    for lv in sorted({r["level"] for r in rows}):
        g = [r for r in rows if r["level"] == lv]
        a = sum(1 for r in g if r["has_timing_changes"])
        b = sum(1 for r in g if r["has_full_instr_spec"] and not r["has_timing_changes"])
        run.say(f"| {lv} | {len(g)} | {a} | {b} | {len(g)-a-b} |")
    na = sum(1 for r in rows if r["has_timing_changes"])
    nb = sum(1 for r in rows if r["has_full_instr_spec"] and not r["has_timing_changes"])
    run.say("")
    run.say(f"    Tổng: **{na}** ứng viên dự báo được CHÍNH XÁC (A), **{nb}** dự báo được")
    run.say(f"    dưới dạng chặn dưới (B), **{len(rows)-na-nb}** chỉ có chặn trên.")
    run.say("")
    run.say(f"    đã ghi {rel(out / 'estimates_all_candidates.csv')} và "
            f"{rel(out / 'estimates_priority.json')}")
    run.say(f"    sổ cái: {len(rows) + len(pri)} dòng candidates trạng thái `estimated`")
    run.say("")
    run.say("=> ĐẠT")
    run.finish("ok", {"n_priority": len(pri), "n_candidates": len(rows),
                      "files": [f.name for f in files]})
    return 0
