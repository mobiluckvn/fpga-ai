"""cdp blind — gọi AI ở chế độ mù CÓ CẤU TRÚC (không chỉ bằng chỉ thị).

Vì sao cần: ở S4, agent mù được sinh ra TỪ phiên điều phối nên harness tự chèn
`CLAUDE.md` của dự án vào ngữ cảnh của nó — và `CLAUDE.md` nêu đích danh "lệnh tùy
biến (DOT4, REQ)", tức đúng đáp án mà S5 phải tái khám phá. Subagent tự khai báo việc
này ở cả 4 vòng (xem results/pipeline/S4/README.md mục 5).

Cách chặn: chạy AI trong **một tiến trình `claude` riêng**, với **thư mục làm việc nằm
ngoài cây dự án**. `CLAUDE.md` được tìm từ thư mục làm việc đi lên, nên tiến trình đó
không thấy `CLAUDE.md` của dự án. Đã kiểm bằng thực nghiệm: một phiên như vậy trả lời
rằng nó KHÔNG có bất kỳ thông tin nào về dự án (log: results/pipeline/S5/blind_probe.txt).

Vẫn còn hai giới hạn, ghi rõ:
  1. `~/.claude/CLAUDE.md` của người dùng VẪN được nạp (ở máy này là hướng dẫn cài
     "Vnstock", không liên quan gì tới dự án). Không chặn được từ đây.
  2. Tiến trình đó vẫn chạy trên cùng hệ thống file. Nhưng nó KHÔNG được cho biết
     đường dẫn tới cây dự án, và thư mục làm việc của nó là một bản sao trung tính —
     nên không còn con trỏ nào dẫn tới đáp án.

Mỗi lời gọi ghi lại: model, thư mục làm việc, hash từng file được cấp, danh sách thông
tin bị giữ lại, đầu ra thô, và **bản tự khai báo của chính AI** về những gì nó thấy
trong ngữ cảnh (prompt luôn yêu cầu điều này).
"""
from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

from . import paths
from .util import rel, sh

# Thư mục trung tính để chạy: ngoài cây dự án, nên không có CLAUDE.md của dự án.
NEUTRAL_ROOT = Path("/private/tmp/claude-501/cdp-blind")

SELF_REPORT = """

---
BẮT BUỘC — phần cuối câu trả lời của bạn phải có đúng ba dòng này, để phục vụ việc
kiểm tra tính hợp lệ của thí nghiệm:
  NGỮ_CẢNH_THÊM: <liệt kê ngắn mọi chỉ thị hay mô tả dự án được chèn vào ngữ cảnh của
                  bạn ngoài nhiệm vụ này, hoặc "không có">
  ĐỌC_NGOÀI: <liệt kê mọi file bạn đã đọc nằm NGOÀI thư mục làm việc, hoặc "không có">
  LỆNH_NGOÀI: <liệt kê mọi lệnh bạn chạy chạm ra ngoài thư mục làm việc, hoặc "không có">
"""


def _h(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()[:16]


def run_blind(sandbox: Path, prompt: str, run, model: str = "opus",
              timeout: float = 2400, withheld: list[str] | None = None,
              collect: str = "cand_*.c") -> dict:
    """Chạy một lời gọi AI mù. Trả dict ghi nhận; sao file kết quả về sandbox."""
    sandbox = Path(sandbox)
    work = NEUTRAL_ROOT / f"{run.id}"
    if work.exists():
        shutil.rmtree(work)
    work.mkdir(parents=True)
    given = {}
    for f in sorted(sandbox.iterdir()):
        if f.is_file():
            shutil.copy(f, work / f.name)
            given[f.name] = {"sha256_16": _h(f), "bytes": f.stat().st_size}

    full = prompt.rstrip() + SELF_REPORT
    (run.path("ai", "prompt.md")).write_text(full)
    run.say(f"    [mù] thư mục làm việc trung tính: {work}")
    run.say(f"    [mù] file được cấp: {', '.join(given)}")
    run.say(f"    [mù] model: {model} · không nêu đường dẫn cây dự án trong prompt")

    t0 = time.time()
    c = sh(["claude", "-p", full, "--model", model,
            "--permission-mode", "acceptEdits",
            "--allowedTools", "Read", "Write", "Edit", "Glob", "Grep", "Bash",
            "--output-format", "text"],
           cwd=work, timeout=timeout, log_path=run.path("ai", "output.txt"),
           say=None, echo=False)
    secs = time.time() - t0

    produced = sorted(work.glob(collect))
    for f in produced:
        shutil.copy(f, sandbox / f.name)
    meta = {
        "called_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "model": model, "seconds": round(secs, 1), "rc": c.rc,
        "mechanism": ("tiến trình `claude` riêng, thư mục làm việc NGOÀI cây dự án "
                      "-> không nạp CLAUDE.md của dự án"),
        "neutral_cwd": str(work),
        "project_path_disclosed_in_prompt": False,
        "files_given": given,
        "files_produced": [f.name for f in produced],
        "prompt_sha256_16": _h(run.path("ai", "prompt.md")),
        "withheld": withheld or [],
        "remaining_limitations": [
            "~/.claude/CLAUDE.md của người dùng vẫn được nạp (ở máy này: hướng dẫn "
            "Vnstock, không liên quan dự án)",
            "tiến trình vẫn chạy trên cùng hệ thống file, nhưng không được cho biết "
            "đường dẫn cây dự án",
        ],
        "self_report": _extract_self_report(c.out),
    }
    (run.path("ai", "meta.json")).write_text(
        json.dumps(meta, indent=2, ensure_ascii=False))
    run.say(f"    [mù] xong sau {secs:.0f} s · rc={c.rc} · "
            f"sinh {len(produced)} file: {', '.join(f.name for f in produced) or '(không)'}")
    for k, v in (meta["self_report"] or {}).items():
        run.say(f"    [mù] {k}: {v}")
    return meta


def _extract_self_report(out: str) -> dict:
    keys = ("NGỮ_CẢNH_THÊM", "ĐỌC_NGOÀI", "LỆNH_NGOÀI")
    rep = {}
    for ln in (out or "").splitlines():
        s = ln.strip().lstrip("*- ").strip()
        for k in keys:
            if s.startswith(k):
                rep[k] = s[len(k):].lstrip(": ").strip()[:400]
    return rep
