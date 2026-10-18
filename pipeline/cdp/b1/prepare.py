"""Dựng hạ tầng cho S4 (vòng B1): tách 5 kernel C ra một file riêng.

Vì sao phải tách: `experiment/m1s/main.c` chứa **cả** bản C thẳng **và** bản đã tối
ưu bằng tay trong cùng một file, phân biệt bằng `#ifdef OPT_KERNELS`. Nếu đưa file
đó cho subagent thì nó thấy luôn đáp án — thí nghiệm "tái khám phá mù" mất ý nghĩa.

Cách làm: giải các chỉ thị tiền xử lý của SÁU macro tính năng (OPT_KERNELS, USE_DOT4,
CONV1_DOT4, USE_REQ, REQ_BENCH, STREAM_10K) ở trạng thái **không định nghĩa**, rồi
cắt vùng kernel ra `kernels_v0.c`. Phần còn lại thành `main.c` với một dòng
`#include "kernels.c"` đúng chỗ đã cắt.

Không sửa `experiment/m1s/` — mọi thứ sinh vào thư mục MỚI `experiment/m1s_b1/`.

Cổng kiểm bắt buộc trước khi dùng: firmware dựng từ `kernels_v0.c` phải cho **đúng
từng chu kỳ từng lớp từng ảnh** như B-V0 đã đo. Nếu lệch thì hạ tầng sai, không phải
đề xuất của AI sai — và ta sẽ không biết điều đó nếu không kiểm trước.
"""
from __future__ import annotations

import re
from pathlib import Path

from .. import paths

FEATURES = ("OPT_KERNELS", "USE_DOT4", "CONV1_DOT4", "USE_REQ", "REQ_BENCH",
            "STREAM_10K")
# Vùng kernel trong main.c: từ chú thích "requantize" tới hết hàm dense.
REGION_START = re.compile(r"^/\* -+ requantize")
REGION_END = re.compile(r"^#ifdef REQ_BENCH")

OUT_DIR = paths.ROOT / "experiment" / "m1s_b1"
SRC = paths.M1S / "main.c"

_COND = re.compile(r"^#\s*(ifdef|ifndef|if|elif|else|endif)\b(.*)$")


def _eval(expr: str) -> bool | None:
    """Trả True/False nếu biểu thức CHỈ dùng các macro tính năng, None nếu không."""
    e = expr.strip()
    names = set(re.findall(r"[A-Za-z_][A-Za-z_0-9]*", e)) - {"defined"}
    if not names or not names.issubset(set(FEATURES)):
        return None
    py = re.sub(r"defined\s*\(\s*([A-Za-z_0-9]+)\s*\)", r"False", e)
    py = py.replace("&&", " and ").replace("||", " or ").replace("!", " not ")
    try:
        return bool(eval(py, {"__builtins__": {}}, {}))      # noqa: S307
    except Exception:                                        # noqa: BLE001
        return None


def resolve(lines: list[str]) -> list[str]:
    """Giải chỉ thị của sáu macro tính năng ở trạng thái KHÔNG định nghĩa.

    Khối nào dùng macro khác (GIT_HASH, SRC_HASH, RUN_IMGS) thì giữ nguyên văn.
    """
    out: list[str] = []
    # mỗi phần tử: (đang xử lý bởi ta?, nhánh nào đang được chọn, đã có nhánh đúng?)
    stack: list[tuple[bool, bool, bool]] = []

    def emitting() -> bool:
        return all(ours is False or take for ours, take, _ in stack)

    for ln in lines:
        m = _COND.match(ln)
        if not m:
            if emitting():
                out.append(ln)
            continue
        kind, rest = m.group(1), m.group(2)
        if kind in ("ifdef", "ifndef", "if"):
            if kind == "ifdef":
                v = False if rest.strip() in FEATURES else None
            elif kind == "ifndef":
                v = True if rest.strip() in FEATURES else None
            else:
                v = _eval(rest)
            if v is None:
                stack.append((False, True, True))
                if emitting():
                    out.append(ln)
            else:
                stack.append((True, v, v))
        elif kind == "elif":
            ours, _take, done = stack[-1]
            if ours:
                v = _eval(rest)
                v = False if v is None else v
                stack[-1] = (True, (not done) and v, done or v)
            else:
                stack[-1] = (ours, True, True)
                if emitting():
                    out.append(ln)
        elif kind == "else":
            ours, _take, done = stack[-1]
            if ours:
                stack[-1] = (True, not done, True)
            else:
                if emitting():
                    out.append(ln)
        elif kind == "endif":
            ours, _t, _d = stack.pop()
            if not ours and emitting():
                out.append(ln)
    return out


def split(lines: list[str]) -> tuple[list[str], list[str]]:
    """Cắt vùng kernel ra; trả (phần còn lại có #include, phần kernel).

    Tìm ranh giới trên file GỐC, vì mốc cuối (`#ifdef REQ_BENCH`) chính là một chỉ
    thị của macro tính năng — nếu giải trước thì mốc đó biến mất.
    """
    a = b = None
    for i, ln in enumerate(lines):
        if a is None and REGION_START.match(ln):
            a = i
        elif a is not None and b is None and REGION_END.match(ln):
            b = i
            break
    if a is None or b is None:
        raise RuntimeError("không tìm được ranh giới vùng kernel trong main.c")
    rest = lines[:a] + [
        "/* ---------- 5 kernel nằm ở file riêng (hạ tầng S4/B1) ----------\n",
        " * Mọi biến đổi của vòng B1 chỉ được sửa file này; phần còn lại của main.c\n",
        " * giữ nguyên để số đo so sánh được. Xem pipeline/cdp/b1/prepare.py.\n",
        " */\n",
        '#include "kernels.c"\n',
        "\n",
    ] + lines[b:]
    return rest, lines[a:b]


def main_prepare(say=print) -> dict:
    lines = SRC.read_text().splitlines(keepends=True)
    rest, kern_raw = split(lines)            # ranh giới trên file gốc
    kern = resolve(kern_raw)                 # chỉ GIẢI vùng kernel
    resolved = kern
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "main.c").write_text("".join(rest))
    (OUT_DIR / "kernels_v0.c").write_text("".join(kern))
    say(f"    {SRC.name}: {len(lines)} dòng · vùng kernel {len(kern_raw)} dòng "
        f"→ giải chỉ thị còn {len(kern)} dòng")
    say(f"    experiment/m1s_b1/main.c      : {len(rest)} dòng")
    say(f"    experiment/m1s_b1/kernels_v0.c: {len(kern)} dòng (5 kernel + requantize + đệm)")
    leaked = [f for f in FEATURES if f in "".join(kern)]
    say(f"    kiểm lọt đáp án: macro tính năng còn sót trong kernels_v0.c = "
        + (", ".join(leaked) if leaked else "KHÔNG"))
    return {"main_lines": len(rest), "kernel_lines": len(kern), "leaked": leaked}
