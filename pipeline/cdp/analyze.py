"""cdp analyze — ILP, DLP, byte/MAC, roofline, Amdahl (SPEC 2.2, bước S3).

Biến `profile.json` thành `analysis.json`: các **chặn trên** và **tỷ trọng** mà một
ứng viên phần cứng phải trích dẫn làm căn cứ (SPEC 4.2 + `candidate.schema.json`).
Mọi công thức ở docs/MO_HINH_CHI_PHI.md mục 3.

- **ILP**: $C \\ge L_{crit}$ (đường găng RAW qua thanh ghi) ⟹ IPC lý tưởng = $N/L_{crit}$.
  ISS đo $L_{crit}$ trực tiếp bằng chiều cao đồ thị phụ thuộc.
- **DLP**: với mỗi lệnh nạp, ISS ghi biểu đồ khoảng cách địa chỉ giữa hai lần chạy
  liên tiếp. Khoảng cách 1 byte ⟹ truy cập liên tục ⟹ gói được 4 làn 8 bit trong 32 bit.
- **Bộ nhớ / roofline**: $\\text{MAC/chu kỳ} \\le B/b$ với $b$ = byte trên mỗi MAC (đo),
  $B$ = byte/chu kỳ mà bộ nhớ cấp được = 4 byte mỗi lần truy cập / $\\lambda_{load}$.
- **Amdahl theo lớp ngữ nghĩa**: nếu xoá sạch một lớp thì tăng tốc tối đa $1/(1-f)$.
"""
from __future__ import annotations

import json

from . import paths, spec as spec_mod, targets, wrap
from .iss import load_timing
from .profile import SEM, profile_target
from .util import fmt_int, rel

STEP = "S3"
BYTES_PER_ACCESS = 4          # bus 32 bit: một lần truy cập chuyển tối đa 4 byte


def analyze_one(pr: dict) -> dict:
    t = targets.get(pr["target"])
    lam, _ = load_timing(t)
    B = BYTES_PER_ACCESS / lam["load"]        # byte/chu kỳ bộ nhớ cấp được
    tot = pr["total_cycles_median"]
    agg = dict.fromkeys(SEM, 0)
    out_layers = {}
    for lay in targets.LAYERS:
        d = pr["layers"][lay]
        c = d["tier3"].get("cycles_by_sem", {})
        for k in SEM:
            agg[k] += c.get(k, 0)
        nimg = d.get("n_img", 1)
        mac = d["mac"]
        byt = ((d.get("ld_bytes") or 0) + (d.get("st_bytes") or 0)) / nimg
        b = (byt / mac) if mac else None
        mpc = (mac / d["cycles_median"]) if mac else None
        roof = (B / b) if b else None
        out_layers[lay] = {
            "cycles": d["cycles_median"], "instret": d["instret_median"],
            "mac": mac, "cycles_per_mac": round(d["cycles_median"] / mac, 3) if mac else None,
            "mac_per_cycle": round(mpc, 4) if mpc else None,
            "bytes_per_image": round(byt, 1), "byte_per_mac": round(b, 3) if b else None,
            "cycles_sum10": d.get("cycles_sum"),
            "cycles_by_sem_sum10": c,
            "sum_check_ok": sum(c.values()) == d.get("cycles_sum"),
            "roof_mac_per_cycle": round(roof, 4) if roof else None,
            "dist_to_roof_x": round(roof / mpc, 2) if (roof and mpc) else None,
            "bound": (None if not roof else
                      ("memory" if mpc >= 0.95 * roof else "compute/issue")),
            "crit_path": d.get("crit_path"), "ipc_ideal": d.get("ipc_ideal"),
            "ipc_real": round(d["instret_median"] / d["cycles_median"], 3),
            # c cộng dồn trên CẢ 10 ảnh -> mẫu số cũng phải là tổng 10 ảnh,
            # không được lấy trung vị của một ảnh (cùng loại bẫy ở mục 1.3).
            "cycles_by_sem": c,
            "share_by_sem": {k: round(100 * c.get(k, 0) / max(d.get("cycles_sum", 1), 1), 2)
                             for k in SEM},
            "amdahl_max_speedup": {
                k: round(1 / (1 - min(c.get(k, 0) / max(d.get("cycles_sum", 1), 1), 0.999)), 2)
                for k in SEM},
            "loops": d.get("tier2_loops", [])[:3],
            "dlp": d.get("dlp"),
        }
    return {
        "target": pr["target"], "core": pr["core"],
        "total_cycles": tot,
        "ms_27mhz": round(tot / 27e6 * 1000, 1),
        "cycles_per_mac_total": round(tot / targets.MAC_TOTAL, 3),
        "mem_bytes_per_cycle_available": round(B, 3),
        "lambda_load": lam["load"],
        "share_by_sem_total": {k: round(100 * agg[k] / max(sum(agg.values()), 1), 2)
                               for k in SEM},
        "cycles_by_sem_total": {k: agg[k] / 10.0 for k in SEM},
        "cycles_by_sem_sum10": agg,
        "cycles_sum10": sum(pr["layers"][l].get("cycles_sum", 0)
                            for l in targets.LAYERS),
        "sum_check_ok": sum(agg.values()) == sum(
            pr["layers"][l].get("cycles_sum", 0) for l in targets.LAYERS),
        "amdahl_max_speedup_total": {
            k: round(1 / (1 - min(agg[k] / max(sum(agg.values()), 1), 0.999)), 2)
            for k in SEM},
        "layers": out_layers,
    }


def dlp_from_profile(pr: dict) -> dict:
    """Tỷ lệ lệnh nạp có khoảng cách địa chỉ 1 byte (liên tục) theo từng lớp."""
    out = {}
    for lay in targets.LAYERS:
        st = pr["layers"][lay].get("stride") or {}
        n1 = n4 = nall = 0
        for _pc, hist in st.items():
            for k, v in hist.items():
                nall += v
                if abs(int(k)) == 1:
                    n1 += v
                elif abs(int(k)) == 4:
                    n4 += v
        out[lay] = {"n_strided": nall,
                    "share_stride_1_pct": round(100 * n1 / nall, 1) if nall else None,
                    "share_stride_4_pct": round(100 * n4 / nall, 1) if nall else None,
                    "lanes_possible_8bit": 4 if (nall and n1 / nall > 0.5) else None}
    return out


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

    res = {}
    for name in names:
        t = targets.get(name)
        run.say("")
        run.say(f"## {t.name} ({t.hw})")
        pr = profile_target(t, w, run)
        dlp = dlp_from_profile(pr)
        for lay in targets.LAYERS:
            pr["layers"][lay]["dlp"] = dlp[lay]
        an = analyze_one(pr)
        res[name] = {"analysis": an, "profile": pr}
        s = an["share_by_sem_total"]
        run.say(f"    tổng {fmt_int(an['total_cycles'])} chu kỳ · {an['ms_27mhz']} ms · "
                f"{an['cycles_per_mac_total']} chu kỳ/MAC")
        run.say(f"    đẳng thức phân loại = ISS: "
                f"{'KHỚP' if an['sum_check_ok'] else 'LỆCH ' + str(sum(an['cycles_by_sem_sum10'].values()) - an['cycles_sum10'])}"
                f"  (tổng 10 ảnh: {fmt_int(an['cycles_sum10'])} chu kỳ)")
        run.say("    tỷ trọng chu kỳ: "
                + " · ".join(f"{k} {s[k]:.1f} %" for k in SEM if s[k] > 0.05))
        run.say("")
        run.say("    DLP — tỷ lệ lệnh nạp có khoảng cách địa chỉ 1 byte (liên tục): "
                + " · ".join(f"{lay} {dlp[lay]['share_stride_1_pct']} %"
                             for lay in targets.LAYERS
                             if dlp[lay]['share_stride_1_pct'] is not None))
        run.say("")
        run.say("    | lớp | chu kỳ | MAC/ck | byte/MAC | trần bộ nhớ | cách trần | giới hạn bởi | IPC thật | IPC lý tưởng |")
        run.say("    |---|---:|---:|---:|---:|---:|---|---:|---:|")
        for lay in targets.LAYERS:
            d = an["layers"][lay]
            run.say(f"    | {lay} | {fmt_int(d['cycles'])} | "
                    f"{d['mac_per_cycle'] if d['mac_per_cycle'] else '—'} | "
                    f"{d['byte_per_mac'] if d['byte_per_mac'] else '—'} | "
                    f"{d['roof_mac_per_cycle'] if d['roof_mac_per_cycle'] else '—'} | "
                    f"{str(d['dist_to_roof_x'])+'x' if d['dist_to_roof_x'] else '—'} | "
                    f"{d['bound'] or '—'} | {d['ipc_real']} | {d['ipc_ideal']} |")

    run.path("analysis.json").write_text(json.dumps(
        {k: v["analysis"] for k, v in res.items()}, indent=2, ensure_ascii=False))
    run.path("profile.json").write_text(json.dumps(
        {k: v["profile"] for k, v in res.items()}, indent=2, ensure_ascii=False))
    run.say("")
    run.say(f"=> ĐẠT · {len(res)} cấu hình · analysis.json + profile.json")
    run.finish("ok", {"targets": list(res)})
    return 0
