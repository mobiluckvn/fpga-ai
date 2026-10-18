"""Tiện ích dùng chung: chạy lệnh ngoài, thời gian, môi trường công cụ."""
from __future__ import annotations

import os
import subprocess
import time
from pathlib import Path

from . import paths


def ts_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S%z")


def run_id(cmd: str, when: float | None = None) -> str:
    return time.strftime("%Y%m%d-%H%M%S", time.localtime(when or time.time())) + "-" + cmd


_ENV_CACHE: dict | None = None


def tool_env() -> dict:
    """PATH + biến của công cụ, lấy bằng cách SOURCE chính env/setup_env.sh.

    Không nhân bản logic của script đó (quy tắc SPEC 0.7: bọc, không viết lại).
    Phải dùng bash: script dựa vào BASH_SOURCE để tìm gốc dự án.
    """
    global _ENV_CACHE
    if _ENV_CACHE is not None:
        return dict(_ENV_CACHE)
    if not paths.ENV_SH.exists():
        _ENV_CACHE = dict(os.environ)
        return dict(_ENV_CACHE)
    out = subprocess.run(
        ["bash", "-c", f'source "{paths.ENV_SH}" >/dev/null 2>&1; env -0'],
        cwd=paths.ROOT, capture_output=True, text=False, check=False,
    )
    env = dict(os.environ)
    for item in out.stdout.split(b"\0"):
        if not item:
            continue
        k, _, v = item.decode("utf-8", "replace").partition("=")
        if k:
            env[k] = v
    _ENV_CACHE = env
    return dict(env)


class Cmd:
    """Kết quả một lần chạy lệnh ngoài."""

    def __init__(self, argv, rc, out, seconds, cwd, log_path=None):
        self.argv = argv
        self.rc = rc
        self.out = out
        self.seconds = seconds
        self.cwd = str(cwd)
        self.log_path = str(log_path) if log_path else None

    @property
    def ok(self) -> bool:
        return self.rc == 0

    def as_dict(self) -> dict:
        return {"argv": self.argv, "rc": self.rc, "seconds": round(self.seconds, 3),
                "cwd": self.cwd, "log": self.log_path}


def sh(argv, cwd: Path | None = None, log_path: Path | None = None,
       timeout: float | None = None, env: dict | None = None,
       say=None, echo: bool = True) -> Cmd:
    """Chạy một lệnh ngoài với môi trường công cụ của dự án, ghi log thô."""
    cwd = Path(cwd or paths.ROOT)
    env = env or tool_env()
    if echo and say:
        say("$ " + " ".join(str(a) for a in argv) + f"   (cwd={cwd})")
    t0 = time.time()
    try:
        p = subprocess.run([str(a) for a in argv], cwd=str(cwd), env=env,
                           capture_output=True, text=True, timeout=timeout, check=False)
        out = (p.stdout or "") + (p.stderr or "")
        rc = p.returncode
    except FileNotFoundError as exc:
        out, rc = f"KHONG TIM THAY LENH: {exc}\n", 127
    except subprocess.TimeoutExpired as exc:
        out = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        out += f"\nHET THOI GIAN sau {timeout} s\n"
        rc = 124
    dt = time.time() - t0
    if log_path:
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        Path(log_path).write_text(
            "$ " + " ".join(str(a) for a in argv) + f"\n# cwd={cwd}\n# rc={rc}"
            f" · {dt:.1f} s · {ts_now()}\n\n" + out)
    return Cmd([str(a) for a in argv], rc, out, dt, cwd, log_path)


def rel(p) -> str:
    """Đường dẫn tương đối gốc dự án nếu được, không thì giữ nguyên."""
    try:
        return str(Path(p).resolve().relative_to(paths.ROOT))
    except ValueError:
        return str(p)


def fmt_int(n) -> str:
    """Số nguyên kiểu Việt Nam: 1.459.993."""
    try:
        return f"{int(n):,}".replace(",", ".")
    except (TypeError, ValueError):
        return str(n)
