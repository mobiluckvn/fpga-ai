"""Phép kiểm K1 của lý thuyết (docs/MO_HINH_CHI_PHI.md mục 1.3).

Khẳng định cần kiểm: chỉ từ **bốn con số đo** (chu kỳ của cặp FAST_ADDR=1/0 và số lệnh
trong cửa sổ đo) cộng bảng $\\lambda$ **đọc từ RTL**, giải hệ hai ẩn ra được thành phần
lệnh động $n_{mem}$, $n_{mul}$ — và kết quả phải khớp số ISS **đếm** được, từng ảnh.

    C(FA=1) =  N + n_mem + n_mul
    C(FA=0) = 2N + 2 n_mem + n_mul

Phải giải TỪNG ẢNH và trong CÙNG một phạm vi đo (xem cảnh báo ở mục 1.3: trộn phạm vi
hoặc lấy trung vị riêng từng đại lượng đều sinh sai hệ thống).
"""
from __future__ import annotations

import json

import yaml

from .. import build as build_mod
from .. import paths, targets
from ..util import fmt_int
from .core import CLASSES, Iss

PAIRS = (("v0", "B-V0", "B-V0r"), ("v1", "B-V1", "B-V1r"))


def _per_image(w, name, profile):
    t = targets.get(name)
    doc = yaml.safe_load((paths.CDP / "iss/timing/mycore.yaml").read_text())
    iss = Iss(build_mod.fw_paths(w, t)["hex"], doc["profiles"][profile]).run()
    out = []
    for g in iss.layer_windows(10):
        acc = dict.fromkeys(CLASSES, 0)
        for wd in g:
            for c, n in zip(CLASSES, wd.classes):
                acc[c] += n
        out.append({"N": sum(acc.values()),
                    "C": sum(wd.cycles for wd in g),
                    "n_mem": acc["load"] + acc["store"],
                    "n_mul": acc["mul"]})
    return out


def main(args, run, w) -> int:
    run.say("# Phép kiểm K1 — mô hình nghịch so với số ISS đếm được")
    run.say("  C(FA=1) = N + n_mem + n_mul ·  C(FA=0) = 2N + 2 n_mem + n_mul")
    rows, bad = [], 0
    for fw, n1, n0 in PAIRS:
        a = _per_image(w, n1, "fast_addr_1")
        b = _per_image(w, n0, "fast_addr_0")
        run.say("")
        run.say(f"  firmware {fw} ({n1} / {n0})")
        run.say(f"    {'ảnh':>4}{'N':>10}{'C(FA=1)':>11}{'C(FA=0)':>11}"
                f"{'n_mem suy ra':>14}{'n_mem ISS':>11}{'n_mul suy ra':>14}"
                f"{'n_mul ISS':>11}  ")
        for i in range(min(len(a), len(b))):
            N, C1, C0 = a[i]["N"], a[i]["C"], b[i]["C"]
            s1, s0 = C1 - N, C0 - 2 * N
            n_mem = s0 - s1
            n_mul = s1 - n_mem
            ok = (n_mem == a[i]["n_mem"] and n_mul == a[i]["n_mul"])
            bad += 0 if ok else 1
            rows.append({"firmware": fw, "img": i, "N": N, "C_fa1": C1, "C_fa0": C0,
                         "n_mem_derived": n_mem, "n_mem_iss": a[i]["n_mem"],
                         "n_mul_derived": n_mul, "n_mul_iss": a[i]["n_mul"],
                         "match": ok})
            if i < 2 or not ok:
                run.say(f"    {i:>4}{N:>10,}{C1:>11,}{C0:>11,}{n_mem:>14,}"
                        f"{a[i]['n_mem']:>11,}{n_mul:>14,}{a[i]['n_mul']:>11,}"
                        f"  {'KHỚP' if ok else 'LỆCH'}")
        if len(a) > 2:
            run.say(f"    … {len(a)-2} ảnh còn lại: "
                    + ("tất cả KHỚP" if bad == 0 else f"{bad} ảnh LỆCH"))
    n = len(rows)
    run.say("")
    run.say(f"=> {'ĐẠT' if bad == 0 else 'KHÔNG ĐẠT'}: {n-bad}/{n} ảnh khớp tuyệt đối")
    # đẳng thức cấu trúc: n_mul = MAC + 2 * số lần requantize (conv1 + conv2)
    nreq = 26 * 26 * 8 + 11 * 11 * 16
    pred = targets.MAC_TOTAL + 2 * nreq
    v1 = [r for r in rows if r["firmware"] == "v1"]
    run.say("")
    run.say(f"   kiểm chéo bằng cấu trúc: {fmt_int(targets.MAC_TOTAL)} MAC + 2×"
            f"{fmt_int(nreq)} lần requantize = {fmt_int(pred)}")
    if v1:
        run.say(f"   n_mul của v1 (ISS)      : {fmt_int(v1[0]['n_mul_iss'])} "
                f"({'KHỚP CHÍNH XÁC' if v1[0]['n_mul_iss'] == pred else 'lệch '
                   + str(v1[0]['n_mul_iss'] - pred)})")
    run.path("k1.json").write_text(json.dumps(
        {"rows": rows, "n": n, "n_bad": bad, "struct_pred_n_mul": pred},
        indent=2, ensure_ascii=False))
    run.finish("ok" if bad == 0 else "fail", {"n": n, "n_bad": bad})
    return 0 if bad == 0 else 1
