"""cdp build — dựng firmware (cờ) và bitstream (tham số RTL) bằng Makefile có sẵn.

Dựng trong cây bóng (xem cdp/wrap.py): không một file nào trong
`experiment/m1s/`, `rtl/mycore/`, `results/` cũ bị ghi.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

from . import paths, provenance, spec as spec_mod, wrap
from .util import rel

STEP = "S1"


def fw_paths(w: Path, t) -> dict:
    d = w / t.fw_dir / t.fw_id
    return {"dir": d, "hex": d / "firmware.hex", "elf": d / "firmware.elf",
            "bin": d / "firmware.bin", "dis": d / "firmware.dis",
            "size": d / "firmware.size.txt", "map": d / "firmware.map"}


def _sha256(p: Path) -> str | None:
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def ram_bytes(t) -> int:
    """Dung lượng RAM thật của cấu hình, theo RAMKB của chính nó (mặc định 64 KB).

    Cấu hình bộ nhớ hai cổng (S7) liên kết với RAMKB=32. Trước đây hàm dưới chia
    cứng cho 65.536 nên nó báo 48,2 % trong khi chỗ thật đã dùng 96,4 % — đúng con
    số cần biết, vì phần còn lại là ngăn xếp.
    """
    return int(getattr(t, "fw_make_vars", {}).get("RAMKB", 64)) * 1024


def read_size(p: Path, ram: int = 65536) -> dict:
    out = {}
    if not p.exists():
        return out
    for ln in p.read_text().splitlines():
        a = ln.split()
        if len(a) >= 2 and a[0].startswith("."):
            try:
                out[a[0]] = int(a[1])
            except ValueError:
                pass
    used = sum(v for k, v in out.items() if k in (".text", ".data", ".bss"))
    out["_used"] = used
    out["_ram"] = ram
    out["_ram_pct"] = round(100.0 * used / ram, 1)
    out["_headroom"] = ram - used
    return out


def ensure_firmware(w: Path, t, run) -> dict:
    """make -C experiment/m1s fw-<id>. Nhánh B dùng lại ĐÚNG file hex này."""
    c = wrap.make(w, t.fw_dir, t.t_fw, mvars=t.fw_make_vars, run=run,
                  log_name=f"make-{t.t_fw}-{t.fw_id}.log")
    fp = fw_paths(w, t)
    info = {"target": t.t_fw, "rc": c.rc, "seconds": round(c.seconds, 1),
            "hex": rel(fp["hex"]) if fp["hex"].exists() else None,
            "hex_sha256": _sha256(fp["hex"]),
            "size": read_size(fp["size"], ram_bytes(t))}
    if not c.ok or not fp["hex"].exists():
        info["error"] = "không dựng được firmware"
        return info
    sz = info["size"]
    run.say(f"    firmware {t.fw_id}: .text {sz.get('.text', 0):,} + "
            f".data {sz.get('.data', 0):,} + .bss {sz.get('.bss', 0):,} = "
            f"{sz.get('_used', 0):,}/{sz.get('_ram', 65536):,} byte "
            f"({sz.get('_ram_pct')} %, còn {sz.get('_headroom', 0):,} byte cho ngăn xếp)")
    run.say(f"    sha256(firmware.hex) = {info['hex_sha256'][:16]}…")
    return info


def ensure_bitstream(w: Path, t, run) -> dict:
    """make build-<biến thể>: yosys → nextpnr → gowin_pack. Vài phút."""
    c = wrap.make(w, t.make_dir, t.t_build, mvars=t.make_vars, run=run,
                  log_name=f"make-{t.t_build}.log", timeout=7200)
    fs = w / t.make_dir / t.var_dir / "top.fs"
    rep = w / t.make_dir / t.var_dir / "report.json"
    info = {"target": t.t_build, "rc": c.rc, "seconds": round(c.seconds, 1),
            "fs": rel(fs) if fs.exists() else None,
            "fs_sha256": _sha256(fs),
            "report_json": rel(rep) if rep.exists() else None}
    if not c.ok or not fs.exists():
        info["error"] = "không dựng được bitstream"
    else:
        run.say(f"    bitstream {t.var_dir}/top.fs = {fs.stat().st_size:,} byte")
    return info


def main(args, run) -> int:
    if not args.spec:
        run.say("cần --spec <đặc tả.yaml>")
        run.finish("fail")
        return 1
    s = spec_mod.load(args.spec)
    t = s.target
    run.target = t.name
    run.say(f"# cdp build · đặc tả {s.path.name} → cấu hình {t.name} ({t.hw})")
    run.say(f"SRC_HASH hiện tại = {run.src_hash} · git {run.git.get('short')}"
            + (" (cây làm việc BẨN)" if run.git.get("dirty") else ""))

    w = wrap.shadow_tree(args.work, fresh=args.fresh, say=run.say)
    res = {"target": t.name, "spec": rel(s.path),
           "work": rel(w), "src_hash": run.src_hash}

    res["firmware"] = ensure_firmware(w, t, run)
    ok = "error" not in res["firmware"]

    if args.bitstream and ok:
        res["bitstream"] = ensure_bitstream(w, t, run)
        ok = "error" not in res["bitstream"]
    elif args.bitstream:
        run.say("    bỏ qua bitstream vì firmware chưa dựng được")

    run.path("build.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    run.say("")
    run.say(f"=> {'ĐẠT' if ok else 'KHÔNG ĐẠT'}")
    run.finish("ok" if ok else "fail", res)
    return 0 if ok else 1
