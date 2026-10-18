"""cdp score — chấm TÁI KHÁM PHÁ: ứng viên nào tương đương tối ưu người đã làm?

Nguyên tắc: chấm bằng **tiêu chí máy đọc được**, không bằng phán xét của người điều
phối. Mỗi đáp án được định nghĩa bằng một bộ dấu hiệu BẮT BUỘC phải cùng xuất hiện
trong một ứng viên; công cụ in ra **đoạn chữ đã khớp** để người đọc tự kiểm từng quyết
định. Không có "gần đúng thì tính".

Bốn đáp án cần tái khám phá (ba cái đầu là tối ưu người đã làm và đã đo; cái thứ tư là
lý do lõi tự viết nhanh hơn PicoRV32):
  DOT4      lệnh nhân-cộng SIMD trên 4 làn 8 bit gói trong 32 bit
  REQ       gộp cả chuỗi lượng tử hoá lại thành MỘT lệnh
  LAYOUT    biến đổi bố cục/đệm dữ liệu để dùng được truy cập gói
  FASTMEM   bộ nhớ hai cổng / tách lệnh-dữ liệu để load/store hết 1 chu kỳ
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from .util import rel

STEP = "S5"

# Mỗi đáp án: danh sách các NHÓM dấu hiệu; phải khớp ÍT NHẤT MỘT mẫu trong MỖI nhóm.
ANSWERS = {
    "DOT4": [
        [r"\bSIMD\b", r"packed", r"\bgói\b", r"\blàn\b", r"\blane", r"\bvector"],
        [r"nhân", r"multipl", r"\bMAC\b", r"dot[- ]?product", r"tích vô hướng"],
        [r"\b8[- ]bit", r"\bbyte", r"int8", r"4 làn", r"4 lane", r"\bquad"],
    ],
    "REQ": [
        [r"requant", r"lượng tử hoá lại", r"rescale", r"quantiz"],
        [r"một lệnh", r"single instruction", r"gộp", r"fuse", r"hợp nhất", r"\bmacro-?op"],
    ],
    "LAYOUT": [
        [r"bố cục", r"layout", r"\bđệm\b", r"\bpad", r"thẳng hàng", r"align",
         r"chuyển vị", r"transpos", r"sắp xếp lại", r"reorder", r"interleav"],
        [r"\bSIMD\b", r"packed", r"\bgói\b", r"\blàn\b", r"\blane", r"\bvector",
         r"\blw\b", r"32[- ]bit"],
    ],
    "FASTMEM": [
        [r"hai cổng", r"dual[- ]?port", r"Harvard", r"hai khối", r"tách lệnh",
         r"split.*(instruction|data)", r"second (memory )?port"],
        [r"1 chu kỳ", r"một chu kỳ", r"single[- ]cycle", r"load_cycles", r"λ", r"lambda",
         r"timing_changes"],
    ],
}
# Chỉ quét các trường DIỄN ĐẠT ĐỀ XUẤT. Cố ý BỎ:
#  - `risks`: nhắc tới một thứ như rủi ro không phải là đề xuất thứ đó (đã gây một
#    dương tính giả: ứng viên SIMD ghi rủi ro "cần đổi bố cục dữ liệu" và bị tính là
#    đã đề xuất biến đổi bố cục);
#  - `evidence`: trường này trích số từ analysis.json, nên chứa sẵn các từ như
#    "requant" của phân loại chu kỳ — trích dẫn một tỷ trọng không phải là đề xuất.
FIELDS = ("id", "title", "target", "expected_mechanism", "template", "level", "spec")


def _text(c: dict) -> str:
    return json.dumps({k: c.get(k) for k in FIELDS}, ensure_ascii=False)


def score_candidate(c: dict) -> dict:
    txt = _text(c)
    out = {}
    for ans, groups in ANSWERS.items():
        matched, ok = [], True
        for g in groups:
            hit = None
            for pat in g:
                m = re.search(pat, txt, re.I)
                if m:
                    lo = max(0, m.start() - 40)
                    hit = {"pattern": pat, "quote": txt[lo:m.end() + 40]}
                    break
            if hit is None:
                ok = False
                break
            matched.append(hit)
        if ok:
            out[ans] = matched
    return out


def score_file(path: Path) -> dict:
    doc = json.loads(Path(path).read_text())
    per = []
    found: dict[str, list] = {}
    for c in doc["candidates"]:
        hits = score_candidate(c)
        per.append({"id": c.get("id"), "level": c.get("level"),
                    "title": c.get("title"), "answers": sorted(hits)})
        for a, m in hits.items():
            found.setdefault(a, []).append({"id": c.get("id"), "evidence": m})
    lv = {}
    for c in doc["candidates"]:
        lv[c["level"]] = lv.get(c["level"], 0) + 1
    return {"file": rel(path), "origin": doc.get("origin"), "mode": doc.get("mode"),
            "base_config": doc.get("base_config"), "n_candidates": len(doc["candidates"]),
            "levels": lv, "n_levels": len(lv),
            "rediscovered": sorted(found), "detail": found, "per_candidate": per}


def main(args, run) -> int:
    files = [Path(f) for f in (args.files or [])]
    if not files:
        run.say("cần danh sách file candidates.json")
        run.finish("fail")
        return 1
    res = [score_file(f) for f in files]
    run.say("# Chấm tái khám phá\n")
    run.say("| file | origin | chế độ | số ứng viên | tầng | DOT4 | REQ | LAYOUT | FASTMEM |")
    run.say("|---|---|---|---:|---|---|---|---|---|")
    for r in res:
        m = {a: ("**có**" if a in r["rediscovered"] else "không")
             for a in ANSWERS}
        run.say(f"| `{Path(r['file']).parent.parent.name}` | {r['origin']} | "
                f"{r.get('mode')} | {r['n_candidates']} | "
                f"{','.join(sorted(r['levels']))} | "
                f"{m['DOT4']} | {m['REQ']} | {m['LAYOUT']} | {m['FASTMEM']} |")
    run.say("")
    for a in ANSWERS:
        n = sum(1 for r in res if a in r["rediscovered"])
        run.say(f"    {a}: tái khám phá ở {n}/{len(res)} lần chạy")
    run.path("score.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    run.say("")
    run.say(f"=> ĐẠT · chi tiết kèm đoạn chữ đã khớp: {rel(run.path('score.json'))}")
    run.finish("ok", {"n_files": len(res),
                      "rediscovered_counts": {a: sum(1 for r in res if a in r["rediscovered"])
                                              for a in ANSWERS}})
    return 0
