"""cdp propose — sinh gói đầu vào cho AI (mù), kiểm đầu ra, và bộ sinh theo luật.

Ba việc (SPEC mục 2 và 4.2, 4.4, 4.6):
  cdp propose --sandbox --target B-V1 --mode open|catalog
        dựng sandbox MÙ: chỉ các file được phép, ĐÃ LÀM SẠCH rò rỉ, kèm kiểm tự động
  cdp propose --validate <candidates.json>
        kiểm đầu ra theo pipeline/schemas/candidate.schema.json
  cdp propose --rules --target B-V1
        bộ sinh ứng viên KHÔNG dùng AI, theo trường `rule` của catalog — để trả lời
        PQ4: AI có đề xuất tốt hơn luật cố định không?

## Làm sạch rò rỉ — vì sao bắt buộc
Đáp án cần tái khám phá ở S5 là DOT4, REQ và bố cục 4 pha. Hai chỗ trong dữ liệu thật
nêu thẳng chúng ra:
  - `static.json.encoding_space` ghi "custom-0 đã dùng funct3 000 (DOT4) và 001 (REQ)".
    Với cấu hình B-V1 thì câu ĐÚNG là "toàn bộ không gian custom còn trống" — bản sạch
    vừa đúng hơn vừa không rò.
  - bảng λ của lõi có hai dòng `custom_dot4` và `custom_req`. Với B-V1 hai lệnh đó không
    tồn tại, nên bỏ hai dòng là đúng sự thật.
Lớp ngữ nghĩa `requant` thì GIỮ: đó là tên công việc trong phần mềm (đọc được từ mã C),
không phải tên giải pháp phần cứng.

Mọi file trước khi cấp đều chạy qua `audit()`; nếu còn một chuỗi trong danh sách cấm
thì DỪNG, không cấp. Thà không chạy còn hơn chạy một thí nghiệm đã mất giá trị.
"""
from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import jsonschema
import yaml

from . import paths, targets
from .util import fmt_int, rel

STEP = "S5"
# Chuỗi cấm xuất hiện trong bất kỳ file nào được cấp cho AI mù.
BANNED = [r"\bDOT4\b", r"\bdot4\b", r"custom_dot4", r"custom_req", r"\bREQ\b",
          r"conv1_prep", r"4 pha", r"bốn pha", r"four[- ]phase", r"pcpi"]
BANNED_RE = re.compile("|".join(BANNED), re.I)
# Nhưng `requant`/`requantize` là tên công việc, không phải đáp án -> cho phép.
ALLOW_RE = re.compile(r"requant\w*", re.I)

LAMBDA_DROP = ("custom_dot4", "custom_req")


def audit(text: str) -> list[str]:
    """Trả danh sách chuỗi cấm còn sót (đã trừ các chỗ thuộc từ `requant...`)."""
    masked = ALLOW_RE.sub(lambda m: "·" * len(m.group(0)), text)
    return sorted(set(m.group(0) for m in BANNED_RE.finditer(masked)))


# ------------------------------------------------------------------ làm sạch
def clean_analysis(an: dict) -> dict:
    out = json.loads(json.dumps(an))
    out.pop("lambda_load", None)
    out["note"] = ("Số liệu do bộ mô phỏng tập lệnh đếm trực tiếp khi chạy firmware "
                   "thật, 10 ảnh. Không có số nào là ước lượng.")
    return out


def clean_static(st: dict) -> dict:
    out = json.loads(json.dumps(st))
    # Không gian mã lệnh: với cấu hình này KHÔNG có lệnh tùy biến nào -> tất cả trống.
    out["encoding_space"] = {
        "note": ("Lõi hiện tại không hiện thực lệnh tùy biến nào. Bốn opcode dành cho "
                 "lệnh tùy biến của RISC-V đều còn trống hoàn toàn."),
        "free_custom_opcodes": {"0x0b": "custom-0", "0x2b": "custom-1",
                                "0x5b": "custom-2", "0x7b": "custom-3"},
        "funct3_per_opcode": 8, "funct7_per_funct3": 128,
    }
    return out


def core_md(t: targets.Target) -> str:
    doc = yaml.safe_load((paths.CDP / "iss/timing/mycore.yaml").read_text())
    lam = doc["profiles"][f"fast_addr_{int(t.rtl_params.get('FAST_ADDR', 1))}"]
    rows = [(k, v) for k, v in lam.items()
            if k not in LAMBDA_DROP and k != "reset_cycles"]
    L = ["# Lõi đích: vi kiến trúc và số chu kỳ mỗi lệnh\n",
         "Lõi RISC-V RV32IM tự viết, chạy trên FPGA ở **27 MHz cố định**.\n",
         "| lớp lệnh | chu kỳ |", "|---|---:|"]
    L += [f"| {k} | {v} |" for k, v in rows]
    L += ["",
          "Tính chất quan trọng:",
          "- **Phát một lệnh mỗi chu kỳ**, máy trạng thái tất định, không đoán nhánh:",
          "  nhánh nhảy hay không nhảy đều hết đúng 1 chu kỳ (không có hình phạt rẽ nhánh).",
          "- **Không có cache.** Bộ nhớ là BSRAM trên chip, **MỘT CỔNG**: mỗi truy cập dữ",
          "  liệu chiếm cổng nên lệnh kế phải nạp ở chu kỳ sau — đó là lý do load/store tốn",
          f"  {lam['load']} chu kỳ. Băng thông tối đa 4 byte / {lam['load']} chu kỳ ="
          f" {4/lam['load']:g} byte/chu kỳ.",
          "- Nhân 32×32 dùng khối nhân cứng của FPGA, hiện tốn "
          f"{lam['mul']} chu kỳ; chia {lam['div']} chu kỳ (dịch-trừ 32 bước).",
          "- Tệp thanh ghi: 31 thanh ghi dùng được (x1–x31), hai cổng đọc một cổng ghi.",
          "- Mô hình chi phí đã kiểm: **C = Σ n_c · λ_c** (n_c = số lệnh động theo lớp),",
          "  khớp **tuyệt đối** với mô phỏng RTL trên mọi cấu hình đã thử. Vì vậy mọi đề",
          "  xuất đổi λ hoặc đổi n_c đều dự báo được bằng chính phương trình này.",
          ""]
    return "\n".join(L)


def budget_json(t: targets.Target) -> dict:
    # Tài nguyên FPGA GW2AR-18C và phần cấu hình hiện tại đã dùng (đo ở bước tổng hợp).
    used = {"LUT4": 3255, "DFF": 573, "BSRAM": 32, "MULT18X18": 4, "ALU": 798}
    avail = {"LUT4": 20736, "DFF": 15552, "BSRAM": 46, "MULT18X18": 48, "ALU": 15552}
    return {
        "fpga": "GW2AR-LV18QN88C8/I7 (họ GW2A-18C)",
        "clock_mhz_fixed": 27.0,
        "fmax_min_mhz": 27.0,
        "fmax_current_mhz": 56.47,
        "available_total": avail,
        "used_by_current_design": used,
        "remaining": {k: avail[k] - used.get(k, 0) for k in avail},
        "note": ("Xung nhịp CỐ ĐỊNH 27 MHz: một đề xuất làm giảm Fmax xuống dưới 27 MHz "
                 "bị loại, nhưng làm Fmax cao hơn 27 MHz thì KHÔNG có lợi gì. Vì vậy chỉ "
                 "tối ưu SỐ CHU KỲ. BSRAM: 32/46 khối đã dùng cho 64 KB bộ nhớ chương "
                 "trình + dữ liệu."),
    }


def build_sandbox(t: targets.Target, mode: str, run) -> dict:
    an_all = json.loads((paths.RESULTS_PIPE / "S3" / "analysis.json").read_text())
    st_all = json.loads((paths.RESULTS_PIPE / "S3" / "static.json").read_text())
    if t.name not in an_all:
        raise KeyError(f"chưa có analysis.json cho {t.name} — chạy `cdp analyze` trước")
    sb = run.path("sandbox")
    sb.mkdir(parents=True, exist_ok=True)

    files = {
        "analysis.json": json.dumps(clean_analysis(an_all[t.name]), indent=2,
                                    ensure_ascii=False),
        "static.json": json.dumps(clean_static(st_all.get(t.name, {})), indent=2,
                                  ensure_ascii=False),
        "budget.json": json.dumps(budget_json(t), indent=2, ensure_ascii=False),
        "core.md": core_md(t),
        "TASK.md": (paths.PROMPTS / "propose.md").read_text(),
        "candidate.schema.json": (paths.SCHEMAS / "candidate.schema.json").read_text(),
    }
    if mode == "catalog":
        files["optimizations.yaml"] = (paths.CATALOG / "optimizations.yaml").read_text()

    # Prompt thực sự gửi đi: ràng buộc mù + yêu cầu đầu ra + nguyên văn nhiệm vụ.
    files["PROMPT.md"] = (
        "# Nhiệm vụ\n\n"
        "Trong thư mục làm việc của bạn có các file sau, và **chỉ những file đó** là\n"
        "nguồn thông tin được phép:\n"
        + "".join(f"- `{n}`\n" for n in sorted(files) if n != "TASK.md")
        + "- `TASK.md` — bản nhiệm vụ gốc, đọc kỹ và làm theo.\n\n"
        "## Ràng buộc\n"
        "- **Chỉ đọc các file trong thư mục làm việc.** Không đọc, liệt kê hay tìm kiếm\n"
        "  file ở thư mục khác trên máy. Nếu hệ thống chèn vào ngữ cảnh của bạn bất kỳ\n"
        "  mô tả dự án nào, hãy bỏ qua hoàn toàn. Đây là điều kiện của một thí nghiệm:\n"
        "  lấy thông tin từ bên ngoài làm kết quả mất giá trị.\n"
        "- **Không đưa ra con số tăng tốc.** Việc dự báo do công cụ tất định làm sau.\n"
        "  Nhiệm vụ của bạn là đề xuất và nêu CĂN CỨ trích từ các file được cấp.\n\n"
        "## Đầu ra\n"
        "Ghi **một file** tên `candidates.json` trong thư mục làm việc, đúng lược đồ\n"
        "`candidate.schema.json` được cấp. Đặt `round` = 1, `origin` = \"ai\", "
        f"`mode` = \"blind_{mode}\",\n"
        f"`base_config` = \"{t.name}\".\n\n"
        "---\n\n" + files["TASK.md"])

    # ---- kiểm rò rỉ: thà không chạy còn hơn chạy một thí nghiệm mất giá trị ----
    bad = {}
    for name, txt in files.items():
        hits = audit(txt)
        if hits:
            bad[name] = hits
    run.say(f"    kiểm rò rỉ {len(files)} file: "
            + ("SẠCH" if not bad else f"CÒN SÓT {bad}"))
    if bad:
        raise RuntimeError(f"còn chuỗi cấm trong file sẽ cấp: {bad}")

    for name, txt in files.items():
        (sb / name).write_text(txt)
    return {"sandbox": rel(sb), "mode": mode, "files": sorted(files),
            "leak_audit": "sạch", "banned_patterns": BANNED}


# ------------------------------------------------------------------ kiểm đầu ra
def validate(path: Path) -> tuple[bool, list[str]]:
    schema = json.loads((paths.SCHEMAS / "candidate.schema.json").read_text())
    try:
        doc = json.loads(Path(path).read_text())
    except Exception as exc:                                 # noqa: BLE001
        return False, [f"không đọc được JSON: {exc}"]
    errs = []
    v = jsonschema.Draft202012Validator(schema)
    for e in sorted(v.iter_errors(doc), key=lambda e: list(e.path)):
        errs.append("/" + "/".join(str(x) for x in e.path) + ": " + e.message)
    return (not errs), errs


def main(args, run) -> int:
    t = targets.get(getattr(args, "target", None) or "B-V1")
    run.target = t.name
    if getattr(args, "validate", None):
        ok, errs = validate(Path(args.validate))
        run.say(f"# kiểm {args.validate}: {'HỢP LỆ' if ok else 'KHÔNG HỢP LỆ'}")
        for e in errs[:20]:
            run.say("    " + e)
        if ok:
            doc = json.loads(Path(args.validate).read_text())
            lv = {}
            for c in doc["candidates"]:
                lv[c["level"]] = lv.get(c["level"], 0) + 1
            run.say(f"    {len(doc['candidates'])} ứng viên · theo tầng: {lv} · "
                    f"origin={doc['origin']} · mode={doc.get('mode')}")
        run.finish("ok" if ok else "fail", {"valid": ok, "errors": errs[:20]})
        return 0 if ok else 1

    if getattr(args, "sandbox", False):
        run.say(f"# cdp propose --sandbox · cấu hình {t.name} · chế độ {args.mode}")
        info = build_sandbox(t, args.mode, run)
        run.say(f"    sandbox: {info['sandbox']}")
        run.say(f"    file: {', '.join(info['files'])}")
        run.say("")
        run.say("    Gọi AI mù bằng:")
        run.say(f"      ./cdp blind --sandbox {info['sandbox']} "
                f"--prompt-file {info['sandbox']}/TASK.md --collect 'candidates*.json'")
        run.finish("ok", info)
        return 0

    if getattr(args, "rules", False):
        run.say(f"# cdp propose --rules · cấu hình {t.name} · KHÔNG dùng AI")
        res = eval_rules(t, run)
        run.say(f"    đại lượng dựng từ analysis/static: {res['facts']}")
        run.say("")
        run.say("    | mẫu catalog | tầng | luật | kết quả |")
        run.say("    |---|---|---|---|")
        for f in res["fired"]:
            run.say(f"    | {f['id']} | {f['level']} | `{f['rule']}` | "
                    f"**THOẢ** ở {', '.join(f.get('layers', []))} |")
        for s_ in res["skipped"]:
            run.say(f"    | {s_['id']} | — | `{s_['rule']}` | {s_.get('why')} |")
        doc = rules_candidates(t, res)
        out = run.path("candidates_rules.json")
        out.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
        ok, errs = validate(out)
        run.say("")
        run.say(f"    sinh {len(doc['candidates'])} ứng viên · lược đồ: "
                + ("HỢP LỆ" if ok else "KHÔNG HỢP LỆ"))
        for e in errs[:8]:
            run.say("        " + e)
        run.path("rules_eval.json").write_text(
            json.dumps(res, indent=2, ensure_ascii=False, default=str))
        run.say(f"    => {rel(out)}")
        run.finish("ok" if ok else "fail",
                   {"n_fired": len(res["fired"]), "n_candidates": len(doc["candidates"]),
                    "schema_valid": ok})
        return 0 if ok else 1

    run.say("dùng: cdp propose --sandbox --target B-V1 --mode open|catalog"
            " | --validate <file> | --rules")
    run.finish("fail")
    return 1


# ------------------------------------------------------------------ bộ sinh theo luật
"""Bộ sinh ứng viên KHÔNG dùng AI (SPEC 4.4), để trả lời PQ4.

Mỗi mẫu trong `pipeline/catalog/optimizations.yaml` có một trường `rule` là biểu thức
trên các đại lượng của `analysis.json`/`static.json`. Bộ sinh dựng đúng không gian tên
đó rồi đánh giá. Đại lượng nào KHÔNG có trong dữ liệu thì luật được ghi là **không
đánh giá được** — không im lặng coi là sai, vì như vậy sẽ thổi phồng ưu thế của AI.
"""


class _NS(dict):
    """Không gian tên cho biểu thức luật; truy cập dạng `class.mac` qua đối tượng con."""

    class _Sub:
        def __init__(self, d):
            self._d = d

        def __getattr__(self, k):
            if k not in self._d:
                raise KeyError(f"thiếu đại lượng: {k}")
            return self._d[k]

    def __init__(self, groups, scalars):
        super().__init__()
        for g, d in groups.items():
            self[g] = _NS._Sub(d)
        self.update(scalars)


def _mnemonics(pr: dict, lay: str) -> set:
    """Tập mã lệnh (dạng tên gợi nhớ thô) xuất hiện trong lớp mạng nóng nhất."""
    out = set()
    for pcs, d in pr["layers"][lay].get("tier3", {}).get("per_pc", {}).items():
        out.add(d["class"])
    # ánh xạ thô sang tên trong catalog
    m = set()
    if "branch_taken" in out or "branch_nt" in out:
        m |= {"blt", "bge", "bne", "beq", "branch"}
    if "load" in out:
        m.add("lb")
    if "mul" in out:
        m.add("mul")
    if "custom_dot4" in out or "mac_like" in out:
        m.add("mac_like")
    return m


def rule_namespace(t: targets.Target, an: dict, st: dict, pr: dict,
                   layer: str | None = None) -> tuple[_NS, dict]:
    """Không gian tên cho luật. `layer=None` -> lớp mạng nóng nhất.

    Luật được đánh giá TRÊN TỪNG LỚP MẠNG, không chỉ lớp nóng nhất: nếu chỉ xét lớp
    nóng nhất thì bộ sinh theo luật bị đánh giá thấp một cách không công bằng (ví dụ
    cơ hội gói 4 làn nằm ở conv1 chứ không ở conv2).
    """
    lay = layer or max(targets.LAYERS, key=lambda l: an["layers"][l]["cycles"])
    hot = an["layers"][lay]
    tot = an["total_cycles"]
    instret = sum(an["layers"][l]["instret"] for l in targets.LAYERS)
    doc = yaml.safe_load((paths.CDP / "iss/timing/mycore.yaml").read_text())
    lamb = doc["profiles"][f"fast_addr_{int(t.rtl_params.get('FAST_ADDR', 1))}"]
    nc = {}
    for k, v in pr["layers"][lay].get("classes_per_image", {}).items():
        nc[k] = nc.get(k, 0) + v
    loops = [x for l in targets.LAYERS for x in st.get("layers", {}).get(l, {}).get("loops", [])]
    hot_loops = sorted(loops, key=lambda d: -(d.get("cycles_in_body") or 0))
    lanes = [d.get("lanes_possible_8bit") for d in loops if d.get("lanes_possible_8bit")]
    facts = {
        "cycles": tot, "cycles_hot": hot["cycles"], "instret": hot["instret"],
        "ipc": round(hot["instret"] / hot["cycles"], 4),
        "layer": lay,
        "fmax_margin": round(56.47 / 27.0, 3),
    }
    hl = sorted(st.get("layers", {}).get(lay, {}).get("loops", []),
                key=lambda d: -(d.get("cycles_in_body") or 0))
    s1 = hl[0].get("stride1_share_pct") if hl else None
    groups = {
        # `class.<x>`: tên lớp NGỮ NGHĨA -> số CHU KỲ; tên lớp LỆNH -> số LỆNH động.
        # (`class` là từ khoá Python nên biểu thức được đổi `class.` -> `cls.` trước khi
        #  đánh giá; xem eval_rules.)
        "cls": {**{k: v / 10.0 for k, v in hot["cycles_by_sem"].items()}, **nc},
        "timing": {"load_cycles": lamb["load"], "mul_cycles": lamb["mul"],
                   "store_cycles": lamb["store"], "div_cycles": lamb["div"]},
        "ilp": {"ideal_ipc": hot.get("ipc_ideal")},
        "roofline": {"bound": hot.get("bound")},
        # `aligned`: truy cập liên tục theo BYTE thì gói 4 làn cần chỉnh thẳng hàng,
        # nên coi là chưa thẳng hàng. Định nghĩa này ghi rõ ở đây, không ngầm hiểu.
        "dlp": {"elem_bits": 8, "lanes_possible": max(lanes) if lanes else 1,
                "aligned": (s1 is not None and s1 < 50.0)},
        "pattern": {"mnem": _mnemonics(pr, lay)},
        "loop": {"body_len": hot_loops[0]["static_instr"] if hot_loops else None},
    }
    return _NS(groups, facts), facts


# Đại lượng catalog dùng mà profile HIỆN TẠI không đo: ghi rõ, không coi là "luật sai".
NOT_MEASURED = ("pattern.len", "pattern.count", "pattern.sources", "region")


def eval_rules(t: targets.Target, run) -> dict:
    an = json.loads((paths.RESULTS_PIPE / "S3" / "analysis.json").read_text())[t.name]
    st = json.loads((paths.RESULTS_PIPE / "S3" / "static.json").read_text()).get(t.name, {})
    pr = json.loads((paths.RESULTS_PIPE / "S3" / "profile.json").read_text())[t.name]
    cat = yaml.safe_load((paths.CATALOG / "optimizations.yaml").read_text())
    nss = {l: rule_namespace(t, an, st, pr, l) for l in targets.LAYERS}
    ns, facts = rule_namespace(t, an, st, pr)
    fired, skipped = [], []
    for tpl in cat["templates"]:
        rule = tpl.get("rule")
        if any(x in rule for x in NOT_MEASURED):
            skipped.append({"id": tpl["id"], "rule": rule,
                            "why": "profile hiện tại KHÔNG đo đại lượng này "
                                   "(cần khai thác n-gram mẫu lệnh — chưa hiện thực)"})
            continue
        expr = rule.replace("class.", "cls.")
        expr = re.sub(r"pattern\.contains\(\[([^\]]*)\]\)",
                      r"any(x in pattern.mnem for x in [\1])", expr)
        expr = expr.replace("false", "False").replace("true", "True")
        hits, errs = [], []
        for l, (nl, _f) in nss.items():
            try:
                if bool(eval(expr, {"__builtins__": {"any": any}, **dict(nl)}, {})):  # noqa: S307
                    hits.append(l)
            except Exception as exc:                                  # noqa: BLE001
                errs.append(f"{l}: {exc}")
        if errs and not hits:
            skipped.append({"id": tpl["id"], "rule": rule,
                            "why": f"không đánh giá được: {errs[0]}"})
            continue
        if hits:
            fired.append({"id": tpl["id"], "level": tpl["level"], "name": tpl["name"],
                          "rule": rule, "fired": True, "layers": hits,
                          "estimate": tpl["estimate"], "risk": tpl.get("risk"),
                          "signal": tpl.get("signal")})
        else:
            skipped.append({"id": tpl["id"], "rule": rule,
                            "why": "luật không thoả ở lớp mạng nào"})
        continue
        try:
            # Không gian tên phải nằm trong GLOBALS: biểu thức generator tạo phạm vi
            # riêng chỉ thấy globals, không thấy locals truyền cho eval().
            ok = bool(eval(expr, {"__builtins__": {"any": any}, **dict(ns)}, {}))  # noqa: S307
        except Exception as exc:                                    # noqa: BLE001
            skipped.append({"id": tpl["id"], "rule": rule,
                            "why": f"không đánh giá được: {exc}"})
            continue
        (fired if ok else skipped).append(
            {"id": tpl["id"], "level": tpl["level"], "name": tpl["name"],
             "rule": rule, "fired": ok, "estimate": tpl["estimate"],
             "risk": tpl.get("risk"), "signal": tpl.get("signal")}
            if ok else {"id": tpl["id"], "rule": rule, "why": "luật không thoả"})
    return {"fired": fired, "skipped": skipped, "facts": facts,
            "namespace": {g: (v._d if hasattr(v, "_d") else v) for g, v in ns.items()}}


def rules_candidates(t: targets.Target, res: dict) -> dict:
    lamb_note = ("Đổi λ của lớp lệnh tương ứng; dự báo bằng ΔC = Σ n_c·Δλ_c "
                 "(không cần RTL).")
    out = []
    for f in res["fired"]:
        cid = f["id"].replace(".", "_")
        ev = [f"luật catalog `{f['rule']}` thoả trên analysis.json của {t.name}"]
        for k, v in res["facts"].items():
            ev.append(f"analysis: {k} = {v}")
        out.append({
            "id": f"rules.{cid}", "level": f["level"], "template": f["id"],
            "title": f["name"],
            "target": ", ".join(f.get("layers", [])) or res["facts"]["layer"],
            "evidence": ev[:6],
            "spec": {"firmware_changes": "(theo mẫu catalog)",
                     "timing_changes": {} if f["estimate"] == "iss_timing" else None,
                     "hw_resources_guess": {"note": "mẫu catalog không nêu"}},
            "estimate_method": {"iss_plugin": "iss_plugin", "iss_timing": "iss_timing",
                                "iss_firmware": "iss_firmware",
                                "analytic": "analytic"}[f["estimate"]],
            "expected_mechanism": (f["signal"] or "") + " — " + lamb_note,
            "risks": [f["risk"]] if f.get("risk") else [],
        })
    for c in out:
        c["spec"] = {k: v for k, v in c["spec"].items() if v is not None}
    return {"round": 1, "origin": "rules", "mode": "open",
            "base_config": t.name, "candidates": out}
