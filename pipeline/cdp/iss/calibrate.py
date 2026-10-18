"""cdp iss --calibrate picorv32 — hiệu chuẩn mô hình chu kỳ cho PicoRV32.

Với mycore, $\\lambda$ đọc được từ RTL vì mỗi lệnh chiếm một số chu kỳ cố định. PicoRV32
thì không: bus của SoC tốn 2 chu kỳ mỗi truy cập (kể cả nạp lệnh) và lệnh tùy biến đi
qua PCPI, nên số chu kỳ mỗi lệnh phụ thuộc trạng thái. Vì vậy $\\lambda$ của PicoRV32 là
**tham số hiệu chuẩn**, và phải báo sai số (docs/MO_HINH_CHI_PHI.md mục 4, 6.4).

Cách hiệu chuẩn — bình phương tối thiểu trên dữ liệu ĐÃ ĐO, không dùng số nào khác:
    với mỗi (cấu hình, ảnh, lớp mạng): sum_c n_c * lambda_c  =  C đo bởi Verilator
  6 cấu hình nhánh A x 10 ảnh x 5 lớp = 300 phương trình, <= 13 ẩn.
$n_c$ do ISS đếm (chính xác, vì ISS chạy đúng chuỗi lệnh đó); $C$ do Verilator đo.
Cột nào có tổng đếm bằng 0 thì không xác định được -> ghi rõ và đặt bằng 0.
"""
from __future__ import annotations

import json
import time

import numpy as np
import yaml

from .. import build as build_mod
from .. import paths, targets, wrap
from ..util import rel
from .core import CLASSES, Iss

TIMING = paths.CDP / "iss" / "timing" / "picorv32.yaml"
# Hồ sơ tạm chỉ để chạy ISS lấy n_c: lambda không ảnh hưởng số lệnh hay luồng điều khiển.
PLACEHOLDER = {c: 1 for c in CLASSES} | {"reset_cycles": 1}


def collect(w, run, names) -> tuple[np.ndarray, np.ndarray, list]:
    rows, b, meta = [], [], []
    for name in names:
        t = targets.get(name)
        run.say(f"    {t.name}: đếm n_c bằng ISS…")
        fw = build_mod.ensure_firmware(w, t, run)
        if "error" in fw:
            raise RuntimeError(f"không dựng được firmware cho {t.name}")
        iss = Iss(build_mod.fw_paths(w, t)["hex"], PLACEHOLDER,
                  with_dot4=bool(t.rtl_params.get("WITH_DOT4", 0)),
                  with_req=bool(t.rtl_params.get("WITH_REQ", 0))).run()
        ref = wrap.parse_m1s(wrap.recorded_sim_log(t))
        if not ref:
            raise RuntimeError(f"không đọc được sim.log đối chứng của {t.name}")
        groups = iss.layer_windows(n_img=len(ref["cyc"]))
        for img, g in enumerate(groups):
            for li, lay in enumerate(targets.LAYERS):
                rows.append(list(g[li].classes))
                b.append(ref["cyc"][img][lay])
                meta.append({"target": t.name, "img": img, "layer": lay})
        run.say(f"      {len(groups)} ảnh × {len(targets.LAYERS)} lớp · "
                f"{iss.instret:,} lệnh · {iss.seconds:.1f} s")
    return np.array(rows, dtype=float), np.array(b, dtype=float), meta


def solve(A: np.ndarray, b: np.ndarray, run):
    """Bình phương tối thiểu, bỏ các cột không xác định được, ép lambda >= 0."""
    totals = A.sum(axis=0)
    keep = [i for i in range(A.shape[1]) if totals[i] > 0]
    drop = [CLASSES[i] for i in range(A.shape[1]) if totals[i] == 0]
    Ak = A[:, keep]
    lam = np.zeros(A.shape[1])
    x, *_ = np.linalg.lstsq(Ak, b, rcond=None)
    # Nếu nghiệm có thành phần âm (vô nghĩa về vật lý), ghim nó về 0 rồi giải lại.
    for _ in range(len(keep)):
        neg = [j for j, v in enumerate(x) if v < 0]
        if not neg:
            break
        keep2 = [k for j, k in enumerate(keep) if j not in neg]
        pinned = [CLASSES[keep[j]] for j in neg]
        run.say(f"    ghim về 0 (nghiệm âm, vô nghĩa vật lý): {pinned}")
        keep = keep2
        x, *_ = np.linalg.lstsq(A[:, keep], b, rcond=None)
    for j, k in enumerate(keep):
        lam[k] = x[j]
    return lam, drop, keep


def integerize(A, b, lam, keep, run):
    """Ép lambda về SỐ NGUYÊN — lambda là số chu kỳ, không thể là phân số.

    Nghiệm bình phương tối thiểu có thể ra phân số khi ma trận **suy biến**: ở đây
    mọi cửa sổ đo chỉ có hai mẫu (jal=0,jalr=2,csr=1) và (jal=3,jalr=4,csr=1), nên
    ba ẩn lambda[csr], lambda[jal], lambda[jalr] chỉ bị ràng buộc bởi hai phương
    trình -> còn một chiều tự do. Trên chiều đó ta tìm nghiệm NGUYÊN, không âm, phần
    dư bằng 0, và có chuẩn nhỏ nhất.

    Cách làm: lam = lam0 + t * n với n là cơ sở của không gian null (ở đây 1 chiều);
    quét giá trị nguyên của một cột trụ để suy ra t, rồi kiểm tính nguyên của mọi cột.
    """
    Ak = A[:, keep]
    # không gian null của Ak
    _, sv, Vt = np.linalg.svd(Ak, full_matrices=True)
    tol = max(Ak.shape) * (sv[0] if len(sv) else 0) * 1e-12
    null = [Vt[i] for i in range(len(Vt)) if i >= len(sv) or sv[i] <= tol]
    lam0 = np.array([lam[k] for k in keep], dtype=float)

    def ok_int(v):
        return np.all(np.abs(v - np.rint(v)) < 1e-6) and np.all(np.rint(v) >= 0)

    best = None
    if not null:
        if ok_int(lam0):
            best = np.rint(lam0)
    elif len(null) == 1:
        n = null[0]
        piv = int(np.argmax(np.abs(n)))
        run.say(f"    không gian null 1 chiều -> lambda[{CLASSES[keep[piv]]}] "
                f"không xác định riêng; quét nghiệm nguyên")
        for v in range(0, 65):
            t = (v - lam0[piv]) / n[piv]
            cand = lam0 + t * n
            if not ok_int(cand):
                continue
            ci = np.rint(cand)
            if not np.allclose(Ak @ ci, b):
                continue
            if best is None or (ci ** 2).sum() < (best ** 2).sum():
                best = ci
    else:
        run.say(f"    không gian null {len(null)} chiều — chưa hiện thực tìm nghiệm "
                f"nguyên nhiều chiều, giữ nghiệm thập phân")

    if best is None:
        run.say("    KHÔNG tìm được nghiệm nguyên khớp tuyệt đối -> giữ nghiệm thập phân")
        return lam
    out = np.zeros_like(lam)
    for j, k in enumerate(keep):
        out[k] = best[j]
    run.say("    nghiệm NGUYÊN, phần dư 0, chuẩn nhỏ nhất: "
            + ", ".join(f"{CLASSES[keep[j]]}={best[j]:.0f}" for j in range(len(keep))))
    return out


def main(args, run, w) -> int:
    core = args.calibrate
    if core != "picorv32":
        run.say(f"chỉ hiệu chuẩn được 'picorv32' (mycore đọc lambda từ RTL), "
                f"không phải {core!r}")
        run.finish("fail")
        return 1
    names = [t.name for t in targets.table() if t.core == "picorv32"]
    run.say(f"# hiệu chuẩn mô hình chu kỳ PicoRV32 trên {len(names)} cấu hình: "
            + ", ".join(names))

    A, b, meta = collect(w, run, names)
    run.say(f"    hệ: {A.shape[0]} phương trình × {A.shape[1]} ẩn")
    lam, drop, keep = solve(A, b, run)
    lam = integerize(A, b, lam, keep, run)

    pred = A @ lam
    err = np.abs(pred - b) / b * 100.0
    run.say("")
    run.say("    | lớp lệnh | lambda hiệu chuẩn | tổng số lệnh (300 dòng) |")
    run.say("    |---|---:|---:|")
    for i, c in enumerate(CLASSES):
        if A[:, i].sum() == 0:
            run.say(f"    | {c} | — (không xuất hiện) | 0 |")
        else:
            run.say(f"    | {c} | {lam[i]:.3f} | {A[:, i].sum():,.0f} |")
    run.say("")
    run.say(f"    sai số của chính phép khớp: lớn nhất {err.max():.3f} % · "
            f"trung bình {err.mean():.3f} % · trung vị {np.median(err):.3f} %")
    worst = np.argsort(err)[-5:][::-1]
    for i in worst:
        m = meta[i]
        run.say(f"      tệ nhất: {m['target']} ảnh {m['img']} {m['layer']}: "
                f"mô hình {pred[i]:,.0f} so với đo {b[i]:,.0f} ({err[i]:.2f} %)")

    doc = {
        "core": "picorv32",
        "derived_from": "hiệu chuẩn bình phương tối thiểu trên số đo Verilator",
        "deterministic": False,
        "note": ("PicoRV32 + bus 2 chu kỳ của feasibility/F5_soc/soc.v. lambda là giá trị "
                 "HIỆU DỤNG, không phải số chu kỳ cố định của một lệnh: bus và PCPI làm "
                 "số chu kỳ phụ thuộc trạng thái. Xem docs/MO_HINH_CHI_PHI.md mục 6.4."),
        "calibration": {
            "fitted_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
            "configs": names,
            "equations": int(A.shape[0]),
            "unknowns_fitted": [CLASSES[i] for i in keep],
            "unidentifiable_set_to_zero": drop,
            "fit_err_max_pct": round(float(err.max()), 4),
            "fit_err_mean_pct": round(float(err.mean()), 4),
            "fit_err_median_pct": round(float(np.median(err)), 4),
            "reference_logs": [rel(wrap.recorded_sim_log(targets.get(n))) for n in names],
        },
        "degeneracy": (
            "Mọi cửa sổ đo chỉ có hai mẫu (jal=0, jalr=2, csr=1) và (jal=3, jalr=4, "
            "csr=1), nên ba ẩn lambda[csr], lambda[jal], lambda[jalr] chỉ bị ràng buộc "
            "bởi hai phương trình: lambda[csr] + 2*lambda[jalr] = 21 và "
            "3*lambda[jal] + 2*lambda[jalr] = 31. Còn một chiều tự do; nghiệm ghi ở "
            "đây là nghiệm NGUYÊN, không âm, phần dư 0, chuẩn nhỏ nhất. "
            "Xem docs/MO_HINH_CHI_PHI.md mục 1.4."),
        "profiles": {"default": {"reset_cycles": 0,
                                 **{c: int(lam[i]) if float(lam[i]).is_integer()
                                    else round(float(lam[i]), 4)
                                    for i, c in enumerate(CLASSES)}}},
    }
    TIMING.write_text(yaml.safe_dump(doc, allow_unicode=True, sort_keys=False))
    run.say("")
    run.say(f"    đã ghi {rel(TIMING)}")
    run.path("calibration.json").write_text(json.dumps(
        {"lambda": {c: float(lam[i]) for i, c in enumerate(CLASSES)},
         "err_max_pct": float(err.max()), "err_mean_pct": float(err.mean()),
         "rows": [{**meta[i], "measured": float(b[i]), "model": float(pred[i]),
                   "err_pct": float(err[i])} for i in range(len(b))]},
        indent=2, ensure_ascii=False))
    ok = bool(err.max() <= 2.0)
    run.say(f"=> {'ĐẠT' if ok else 'KHÔNG ĐẠT'} (tiêu chí S2: sai số từng lớp ≤ 2 %)")
    run.finish("ok" if ok else "fail", doc["calibration"])
    return 0 if ok else 1
