"""Khoá tái lập: git commit, SRC_HASH, phiên bản công cụ.

Quy tắc 3 của phiên: MỖI lệnh cdp phải ghi được những thứ này vào meta.json.
"""
from __future__ import annotations

import hashlib
import platform
import sys

from . import paths
from .util import sh, tool_env

# SRC_HASH phải GIỐNG HỆT cách Makefile tính:
#   cat main.c ../../fw/weights.h | shasum -a 256 | cut -c1-12
SRC_FILES = (paths.M1S / "main.c", paths.FW / "weights.h")


def src_hash(files=SRC_FILES) -> str | None:
    h = hashlib.sha256()
    for f in files:
        if not f.exists():
            return None
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def git_info() -> dict:
    out = {}
    c = sh(["git", "rev-parse", "HEAD"], cwd=paths.ROOT, echo=False)
    out["commit"] = c.out.strip() if c.ok else None
    c = sh(["git", "rev-parse", "--short", "HEAD"], cwd=paths.ROOT, echo=False)
    out["short"] = c.out.strip() if c.ok else None
    c = sh(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=paths.ROOT, echo=False)
    out["branch"] = c.out.strip() if c.ok else None
    c = sh(["git", "status", "--porcelain"], cwd=paths.ROOT, echo=False)
    lines = [l for l in (c.out or "").splitlines() if l.strip()] if c.ok else []
    out["dirty"] = bool(lines)
    out["dirty_files"] = len(lines)
    return out


# Lệnh lấy phiên bản, đã KIỂM trên máy này (xem results/pipeline/S0/tool_versions.txt).
_TOOLS = {
    "yosys":            (["yosys", "-V"], 0),
    "nextpnr":          (["nextpnr-himbaechel", "--version"], 0),
    "verilator":        (["verilator", "--version"], 0),
    "openFPGALoader":   (["openFPGALoader", "--Version"], 0),
    "riscv-gcc":        (["riscv-none-elf-gcc", "-dumpversion"], 0),
    "make":             (["make", "-v"], 0),
    "git":              (["git", "--version"], 0),
}


def _first_line(txt: str) -> str:
    for ln in (txt or "").splitlines():
        if ln.strip():
            return ln.strip()
    return ""


def tool_versions(names=None) -> dict:
    """Phiên bản các công cụ. `names` = None nghĩa là lấy hết.

    gowin_pack KHÔNG có cờ phiên bản (đã kiểm), nên ghi phiên bản gói
    OSS CAD Suite (file VERSION) thay cho nó — cả hai cùng đến từ gói đó.
    """
    want = set(names) if names else set(_TOOLS) | {"gowin_pack", "python"}
    env = tool_env()
    out: dict[str, str | None] = {}
    if "python" in want:
        out["python"] = sys.version.split()[0]
        try:
            import numpy
            out["numpy"] = numpy.__version__
        except Exception:                                    # noqa: BLE001
            out["numpy"] = None
    for name, (argv, _ln) in _TOOLS.items():
        if name not in want:
            continue
        c = sh(argv, cwd=paths.ROOT, env=env, echo=False)
        out[name] = _first_line(c.out) if c.ok else None
    if "gowin_pack" in want:
        c = sh(["bash", "-c", "command -v gowin_pack"], cwd=paths.ROOT, env=env, echo=False)
        out["gowin_pack_path"] = _first_line(c.out) if c.ok else None
        vf = None
        p = _first_line(c.out) if c.ok else ""
        if p:
            cand = [x for x in (p, ) if x]
            from pathlib import Path as _P
            root = _P(p).resolve().parent.parent
            if (root / "VERSION").exists():
                vf = (root / "VERSION").read_text().strip()
            del cand
        out["oss_cad_suite"] = vf
    return out


def host_info() -> dict:
    return {"platform": platform.platform(), "machine": platform.machine(),
            "python": sys.version.split()[0]}
