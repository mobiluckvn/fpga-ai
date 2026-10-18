"""Khoá kit: một kit, tuần tự (SPEC mục 0.6).

Mọi truy cập kit (nạp bitstream, đọc UART) PHẢI đi qua khoá này. Khoá là
fcntl.flock trên pipeline/runs/kit.lock — tiến trình thứ hai CHỜ, không bao giờ
hai tiến trình cùng nạp.
"""
from __future__ import annotations

import errno
import fcntl
import json
import os
import time
from contextlib import contextmanager

from . import paths
from .util import ts_now


def holder_info() -> dict | None:
    """Ai đang giữ khoá (đọc nội dung file khoá, không cần khoá)."""
    try:
        txt = paths.KIT_LOCK.read_text().strip()
        return json.loads(txt) if txt else None
    except (OSError, ValueError):
        return None


@contextmanager
def kit_lock(owner: str = "cdp", timeout: float | None = None, say=print,
             poll: float = 0.25):
    """Giữ khoá kit trong khối `with`.

    timeout=None: chờ vô hạn (đúng tinh thần "tiến trình thứ hai chờ").
    Trả về dict thông tin khoá: {acquired_at, waited_s, path}.
    """
    paths.KIT_LOCK.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(paths.KIT_LOCK), os.O_RDWR | os.O_CREAT, 0o644)
    t0 = time.time()
    waited = 0.0
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            if exc.errno not in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
                raise
            who = holder_info()
            say(f"[kit.lock] khoá đang bị giữ{' bởi ' + str(who) if who else ''} — CHỜ…")
            while True:
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError as exc2:
                    if exc2.errno not in (errno.EAGAIN, errno.EACCES, errno.EWOULDBLOCK):
                        raise
                    if timeout is not None and (time.time() - t0) > timeout:
                        raise TimeoutError(
                            f"không lấy được khoá kit sau {timeout} s") from exc2
                    time.sleep(poll)
            waited = time.time() - t0
            say(f"[kit.lock] đã lấy được khoá sau khi chờ {waited:.2f} s")
        info = {"owner": owner, "pid": os.getpid(), "acquired_at": ts_now(),
                "waited_s": round(waited, 3), "path": str(paths.KIT_LOCK)}
        os.lseek(fd, 0, os.SEEK_SET)
        os.truncate(fd, 0)
        os.write(fd, (json.dumps(info, ensure_ascii=False) + "\n").encode())
        os.fsync(fd)
        yield info
    finally:
        try:
            os.lseek(fd, 0, os.SEEK_SET)
            os.truncate(fd, 0)
        except OSError:
            pass
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)
