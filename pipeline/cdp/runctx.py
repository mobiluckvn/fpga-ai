"""Ngữ cảnh một lần chạy lệnh cdp.

Quy tắc 3 của phiên: MỖI lệnh cdp ghi pipeline/runs/<id>/meta.json với git commit,
phiên bản công cụ, tham số và SRC_HASH. Lớp này làm việc đó, kèm một dòng sổ cái.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

from . import ledger, paths, provenance
from .util import run_id, ts_now


class Run:
    def __init__(self, cmd: str, params: dict | None = None, step: str | None = None,
                 spec: str | None = None, target: str | None = None,
                 tools: list[str] | None = None, note: str | None = None,
                 quiet: bool = False):
        self.cmd = cmd
        self.params = params or {}
        self.step = step
        self.spec = spec
        self.target = target
        self.note = note
        self.quiet = quiet
        self.t0 = time.time()
        self.id = run_id(cmd, self.t0)
        # Tạo thư mục bằng mkdir KHÔNG exist_ok và bắt lỗi: hai tiến trình cdp khởi
        # động trong cùng một giây tính ra cùng run_id, nên kiểm-rồi-tạo bị đua
        # (đã xảy ra thật khi chạy 2 lời gọi song song ở S5).
        base = self.id
        n = 1
        while True:
            self.id = base if n == 1 else f"{base}-{n}"
            self.dir = paths.RUNS / self.id
            try:
                self.dir.mkdir(parents=True)
                break
            except FileExistsError:
                n += 1
                if n > 50:
                    raise
        self.log_path = self.dir / "run.log"
        self._log = open(self.log_path, "w")
        self.git = provenance.git_info()
        self.src_hash = provenance.src_hash()
        self.tools = provenance.tool_versions(tools)
        self.result: dict = {}
        self.status = "running"
        self._write_meta()
        self.con = ledger.connect()
        self._ledger_row()

    # ---------- ghi ----------
    def say(self, *parts) -> None:
        line = " ".join(str(p) for p in parts)
        if not self.quiet:
            print(line, flush=True)
        self._log.write(line + "\n")
        self._log.flush()

    def path(self, *name) -> Path:
        p = self.dir.joinpath(*name)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def meta(self) -> dict:
        return {
            "run_id": self.id,
            "cmd": self.cmd,
            "step": self.step,
            "argv": sys.argv[1:],
            "spec": self.spec,
            "target": self.target,
            "params": self.params,
            "started_at": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(self.t0)),
            "finished_at": None if self.status == "running" else ts_now(),
            "duration_s": None if self.status == "running" else round(time.time() - self.t0, 3),
            "status": self.status,
            "git": self.git,
            "src_hash": self.src_hash,
            "tools": self.tools,
            "host": provenance.host_info(),
            "cwd": str(Path.cwd()),
            "run_dir": str(self.dir.relative_to(paths.ROOT)),
            "note": self.note,
            "result": self.result,
        }

    def _write_meta(self) -> None:
        (self.dir / "meta.json").write_text(
            json.dumps(self.meta(), indent=2, ensure_ascii=False) + "\n")

    def _ledger_row(self) -> None:
        ledger.upsert(self.con, "runs", {
            "run_id": self.id, "cmd": self.cmd, "step": self.step, "spec": self.spec,
            "target": self.target, "status": self.status,
            "started_at": self.meta()["started_at"],
            "finished_at": self.meta()["finished_at"],
            "duration_s": self.meta()["duration_s"],
            "git_commit": self.git.get("commit"),
            "git_dirty": 1 if self.git.get("dirty") else 0,
            "src_hash": self.src_hash,
            "params_json": self.params, "tools_json": self.tools,
            "result_json": self.result,
            "run_dir": str(self.dir.relative_to(paths.ROOT)), "note": self.note,
        })

    def finish(self, status: str, result: dict | None = None) -> None:
        self.status = status
        if result:
            self.result.update(result)
        self._write_meta()
        self._ledger_row()
        self.say(f"[run {self.id}] {status} · {time.time()-self.t0:.1f} s · {self.dir}")
        self._log.close()
        self.con.close()

    # ---------- dùng như context manager ----------
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type is not None:
            self.result["error"] = f"{exc_type.__name__}: {exc}"
            self.finish("fail")
        elif self.status == "running":
            self.finish("ok")
        return False
