"""Bọc hai Makefile có sẵn mà KHÔNG sửa cây cũ (SPEC 0.7, quy tắc 2 của phiên).

Vấn đề: `experiment/m1s/v*/` và `rtl/mycore/bv*/` đã nằm trong git (130 + 839 file)
và là bằng chứng của giai đoạn trước. Chạy make tại chỗ sẽ ghi đè chúng.

Cách làm: **thư mục bóng**. Tạo một cây chỉ gồm symlink tới mã nguồn, sắp đúng độ
sâu để mọi đường dẫn tương đối trong hai Makefile (`../../fw`, `../../scripts`,
`../../hw`, `../uart`, `../../feasibility/...`, `../../experiment/m1s`) vẫn trỏ đúng.
Riêng `results/` trong cây bóng là thư mục THẬT và rỗng, nên `make check-*` không
bao giờ ghi lên CSV số đo cũ.

    pipeline/work/<tên>/
        .git -> ROOT/.git            (chỉ để Makefile lấy GIT_HASH)
        fw hw scripts feasibility model .venv -> ROOT/...
        results/                     THẬT, rỗng
        experiment/m1s/              THẬT; symlink Makefile, main.c, *.cpp
        rtl/{uart,picorv32,ext} -> ROOT/rtl/...
        rtl/mycore/                  THẬT; symlink Makefile, *.v, *.cpp
"""
from __future__ import annotations

import importlib.util
import os
import re
import shutil
import statistics as st
from pathlib import Path

from . import paths, targets
from .util import sh, tool_env

WORK = paths.PIPELINE / "work"

# Thư mục dùng chung: chỉ ĐỌC, nối bằng symlink.
LINK_DIRS = ("fw", "hw", "scripts", "feasibility", "model", ".venv")
LINK_RTL = ("uart", "picorv32", "ext")
# Mã nguồn của hai thư mục build: symlink theo mẫu tên, KHÔNG lấy thư mục con
# (v*/ bv*/ obj_dir*/ tests/) và KHÔNG lấy nhị phân Verilator đã commit (Vsoc_b*).
SRC_GLOBS = {
    "experiment/m1s": ("Makefile", "*.c", "*.cpp", "*.h"),
    "rtl/mycore": ("Makefile", "*.v", "*.cpp"),
}


def _link(src: Path, dst: Path) -> None:
    if dst.is_symlink() or dst.exists():
        if dst.is_symlink() and os.readlink(dst) == str(src):
            return
        dst.unlink()
    dst.symlink_to(src)


def shadow_tree(name: str = "cdp", fresh: bool = False, say=print) -> Path:
    """Tạo (hoặc làm mới) cây bóng, trả về đường dẫn gốc của nó."""
    w = WORK / name
    if fresh and w.exists():
        shutil.rmtree(w)
    w.mkdir(parents=True, exist_ok=True)
    _link(paths.ROOT / ".git", w / ".git")
    for d in LINK_DIRS:
        if (paths.ROOT / d).exists():
            _link(paths.ROOT / d, w / d)
    (w / "results").mkdir(exist_ok=True)
    (w / "rtl").mkdir(exist_ok=True)
    for d in LINK_RTL:
        if (paths.ROOT / "rtl" / d).exists():
            _link(paths.ROOT / "rtl" / d, w / "rtl" / d)
    for rel, globs in SRC_GLOBS.items():
        real = w / rel
        real.mkdir(parents=True, exist_ok=True)
        for g in globs:
            for f in sorted((paths.ROOT / rel).glob(g)):
                if f.is_file():
                    _link(f, real / f.name)
    (w / ".cdp-shadow").write_text(
        "Cây bóng của cdp. Chỉ chứa symlink tới mã nguồn + thư mục build mới.\n"
        f"Gốc dự án: {paths.ROOT}\n")
    say(f"[cây bóng] {w.relative_to(paths.ROOT)}"
        + (" (dựng mới)" if fresh else " (dùng lại)"))
    return w


# --------------------------------------------------------------- make
def make(w: Path, subdir: str, target: str, mvars: dict | None = None,
         run=None, log_name: str | None = None, timeout: float = 3600) -> "object":
    argv = ["make", "-C", str(w / subdir), target]
    for k, v in (mvars or {}).items():
        argv.append(f"{k}={v}")
    log = run.path("logs", log_name or f"make-{target}.log") if run else None
    say = run.say if run else None
    c = sh(argv, cwd=w / subdir, log_path=log, timeout=timeout, env=tool_env(), say=say)
    if run:
        run.say(f"    make {target} → rc={c.rc} · {c.seconds:.1f} s"
                + (f" · log {Path(log).relative_to(run.dir)}" if log else ""))
        if not c.ok:
            for ln in c.out.strip().splitlines()[-25:]:
                run.say("      " + ln)
    return c


# --------------------------------------------------------------- đọc log M1S
_m1s = None


def m1s_check_mod():
    """Nạp scripts/m1s_check.py làm module để DÙNG LẠI read_golden/parse_block."""
    global _m1s
    if _m1s is None:
        spec = importlib.util.spec_from_file_location(
            "m1s_check", paths.SCRIPTS / "m1s_check.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _m1s = mod
    return _m1s


def parse_m1s(path: Path) -> dict | None:
    """Khối M1S trong một log (sim.log của Verilator, hoặc log kit)."""
    p = Path(path)
    if not p.exists():
        return None
    return m1s_check_mod().parse_block(p.read_text().splitlines())


def golden() -> dict:
    return m1s_check_mod().read_golden(paths.FW / "weights.h")


SIM_CYCLES_RE = re.compile(r"SIM_OK: xong sau (\d+) chu ky")


def sim_total_cycles(path: Path) -> int | None:
    m = SIM_CYCLES_RE.search(Path(path).read_text()) if Path(path).exists() else None
    return int(m.group(1)) if m else None


# --------------------------------------------------------------- so sánh
def median_total(blk: dict) -> int | None:
    """Trung vị chu kỳ/ảnh — ĐÚNG định nghĩa của scripts/branch_b_table.py."""
    if not blk or not blk.get("cyc"):
        return None
    return int(st.median([blk["cyc"][i]["total"] for i in sorted(blk["cyc"])]))


COLS = ("conv1", "pool1", "conv2", "pool2", "dense", "total", "instret")


def compare_cycles(got: dict, ref: dict) -> dict:
    """So chu kỳ từng lớp từng ảnh giữa hai khối M1S. Yêu cầu BẰNG TUYỆT ĐỐI."""
    diffs = []
    imgs = sorted(set(got.get("cyc", {})) | set(ref.get("cyc", {})))
    for i in imgs:
        a, b = got.get("cyc", {}).get(i), ref.get("cyc", {}).get(i)
        if a is None or b is None:
            diffs.append({"img": i, "col": "*", "got": a and "có" or "thiếu",
                          "ref": b and "có" or "thiếu"})
            continue
        for col in COLS:
            if a[col] != b[col]:
                diffs.append({"img": i, "col": col, "got": a[col], "ref": b[col],
                              "delta": a[col] - b[col]})
    return {"equal": not diffs, "n_img": len(imgs), "n_diff": len(diffs),
            "diffs": diffs[:40]}


def check_golden(blk: dict, g: dict | None = None) -> dict:
    """CRC 5 tensor × N ảnh và dự đoán, so với golden Python trong fw/weights.h."""
    g = g or golden()
    probs = []
    n = len(g["m1s_labels"])
    for i in range(n):
        if i not in blk.get("crc", {}):
            probs.append(f"ảnh {i}: thiếu dòng crc")
            continue
        exp = [g["m1s_crc_a1"][i], g["m1s_crc_p1"][i], g["m1s_crc_a2"][i],
               g["m1s_crc_p2"][i], g["m1s_crc_logit"][i]]
        for nm, got_v, e in zip(("a1", "p1", "a2", "p2", "logit"), blk["crc"][i], exp):
            if got_v != e:
                probs.append(f"ảnh {i}: CRC {nm} {got_v:08X} != golden {e:08X}")
        if blk["img"][i]["pred"] != g["m1s_pred_golden"][i]:
            probs.append(f"ảnh {i}: dự đoán {blk['img'][i]['pred']} "
                         f"!= golden {g['m1s_pred_golden'][i]}")
    return {"ok": not probs, "n_img": n, "problems": probs[:20]}


def measurement_rows(blk: dict, run_id: str, target: str, source: str,
                     src_hash: str | None, g: dict | None = None) -> list[dict]:
    g = g or golden()
    rows = []
    for i in sorted(blk.get("cyc", {})):
        c = blk["cyc"][i]
        crc = blk.get("crc", {}).get(i) or [None] * 5
        img = blk.get("img", {}).get(i, {})
        rows.append({
            "run_id": run_id, "target": target, "variant": blk.get("variant"),
            "source": source, "img": i,
            **{k: c[k] for k in COLS},
            "crc_a1": f"{crc[0]:08X}" if crc[0] is not None else None,
            "crc_p1": f"{crc[1]:08X}" if crc[1] is not None else None,
            "crc_a2": f"{crc[2]:08X}" if crc[2] is not None else None,
            "crc_p2": f"{crc[3]:08X}" if crc[3] is not None else None,
            "crc_logit": f"{crc[4]:08X}" if crc[4] is not None else None,
            "pred": img.get("pred"),
            "pred_golden": g["m1s_pred_golden"][i] if i < len(g["m1s_pred_golden"]) else None,
            "crc_ok": 1 if img.get("okmask") == 31 else 0,
            "src_hash": src_hash,
        })
    return rows


def recorded_sim_log(t: targets.Target) -> Path:
    """sim.log ĐÃ GHI của giai đoạn trước (chỉ đọc) — mốc đối chứng của S1."""
    return paths.ROOT / t.sim_log


def measurement_rows_from_csv(rows: list[dict], run_id: str, target: str,
                              src_hash: str | None) -> list[dict]:
    """Dòng `measurements` cho số đo KIT: lấy từ CSV mà scripts/m1s_check.py ghi.

    `m1s_check.py` không in lại các dòng M1S thô, nên nguồn duy nhất đủ số là CSV của
    nó. CSV có chu kỳ từng lớp + instret + cờ CRC (không có giá trị CRC từng tensor —
    chính m1s_check.py đã so chúng với golden và chỉ ghi lại kết quả so).
    """
    out = []
    for r in rows:
        out.append({
            "run_id": run_id, "target": target, "variant": r.get("bien_the"),
            "source": "kit", "img": int(r["img"]),
            "conv1": int(r["conv1"]), "pool1": int(r["pool1"]),
            "conv2": int(r["conv2"]), "pool2": int(r["pool2"]),
            "dense": int(r["dense"]), "total": int(r["total"]),
            "instret": int(r["instret"]),
            "pred": int(r["pred"]), "pred_golden": int(r["pred_golden"]),
            "crc_ok": int(r["crc_ok_5lop"]), "src_hash": src_hash,
        })
    return out
