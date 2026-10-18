"""cdp synth — tổng hợp để lấy chi phí phần cứng và Fmax, qua Makefile có sẵn.

Luồng của dự án: yosys (synth_gowin -nodsp) → nextpnr-himbaechel → gowin_pack.
Số tài nguyên và Fmax đọc từ `report.json` của nextpnr; bản in cho người đọc do
`scripts/pnr_report.py` sinh (dùng lại, không viết lại).

Cảnh báo đã ghi trong docs/KET_QUA_TONG_HOP.md mục 5: hiệu hai lần tổng hợp KHÔNG
đo được chi phí phần cứng nhỏ (ABC chọn cách phủ khác, tổng LUT4 xê dịch tới 1.545),
và nextpnr KHÔNG ràng buộc đường tới BSRAM nên Fmax không nói gì về thiết kế tính
địa chỉ bộ nhớ bằng tổ hợp.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import build as build_mod
from . import paths, spec as spec_mod, wrap
from .util import fmt_int, rel, sh, tool_env

STEP = "S1"

WATCH = ("LUT4", "ALU", "DFF", "BSRAM", "MULT18X18", "MULT9X9", "MULT36X36", "IOB")


def read_report(p: Path) -> dict:
    rep = json.loads(p.read_text())
    util = {k: {"used": v.get("used", 0), "available": v.get("available", 0)}
            for k, v in rep.get("utilization", {}).items()}
    fmax = {k: {"achieved": v.get("achieved"), "constraint": v.get("constraint")}
            for k, v in rep.get("fmax", {}).items()}
    return {"utilization": util, "fmax": fmax}


def parse_resources_txt(p: Path) -> dict:
    """Đọc lại resources.txt đã ghi của giai đoạn trước (để đối chiếu)."""
    out = {"utilization": {}, "fmax": {}}
    if not p.exists():
        return out
    for ln in p.read_text().splitlines():
        a = ln.split()
        if len(a) >= 4 and a[2] == "/" and a[1].isdigit():
            out["utilization"][a[0]] = {"used": int(a[1]), "available": int(a[3])}
        elif ln.startswith("Fmax["):
            name = ln[ln.index("[") + 1:ln.index("]")]
            try:
                out["fmax"][name] = {"achieved": float(ln.split("=")[1].split()[0])}
            except (IndexError, ValueError):
                pass
    return out


def main(args, run) -> int:
    if not args.spec:
        run.say("cần --spec <đặc tả.yaml>")
        run.finish("fail")
        return 1
    s = spec_mod.load(args.spec)
    t = s.target
    run.target = t.name
    run.say(f"# cdp synth · đặc tả {s.path.name} → cấu hình {t.name} ({t.hw})")

    w = wrap.shadow_tree(args.work, fresh=args.fresh, say=run.say)
    res = {"target": t.name, "spec": rel(s.path), "work": rel(w)}

    res["firmware"] = build_mod.ensure_firmware(w, t, run)
    if "error" in res["firmware"]:
        run.finish("fail", res)
        return 1

    res["bitstream"] = build_mod.ensure_bitstream(w, t, run)
    rep_path = w / t.make_dir / t.var_dir / "report.json"
    if "error" in res["bitstream"] or not rep_path.exists():
        run.say("=> KHÔNG ĐẠT: không có report.json của nextpnr")
        run.finish("fail", res)
        return 1

    # bản in cho người đọc: dùng lại scripts/pnr_report.py
    c = sh([paths.VENV_PY, paths.SCRIPTS / "pnr_report.py", rep_path],
           cwd=paths.ROOT, env=tool_env(), log_path=run.path("resources.txt"),
           say=run.say, echo=False)
    got = read_report(rep_path)
    ref = parse_resources_txt(paths.ROOT / t.make_dir / t.var_dir / "resources.txt")

    run.say("")
    run.say("    | tài nguyên | lần này | đã ghi trước | lệch |")
    run.say("    |---|---:|---:|---:|")
    for k in WATCH:
        a = got["utilization"].get(k, {}).get("used")
        b = ref["utilization"].get(k, {}).get("used")
        d = (a - b) if (a is not None and b is not None) else None
        run.say(f"    | {k} | {fmt_int(a) if a is not None else '—'} | "
                f"{fmt_int(b) if b is not None else '—'} | "
                f"{('%+d' % d) if d is not None else '—'} |")
    for clk, v in got["fmax"].items():
        b = ref["fmax"].get(clk, {}).get("achieved")
        run.say(f"    Fmax[{clk}] = {v['achieved']:.2f} MHz "
                f"(ràng buộc {v['constraint']} MHz)"
                + (f" · đã ghi trước {b:.2f} MHz" if b else ""))

    res["report"] = got
    res["reference_resources_txt"] = rel(paths.ROOT / t.make_dir / t.var_dir
                                         / "resources.txt")
    res["reference"] = ref
    fmax_ok = all((v["achieved"] or 0) >= (v["constraint"] or 0)
                  for v in got["fmax"].values()) if got["fmax"] else False
    res["fmax_ok"] = fmax_ok
    run.path("synth.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    run.say("")
    run.say(f"=> {'ĐẠT' if fmax_ok and c.ok else 'KHÔNG ĐẠT'} "
            "(tiêu chí: Fmax >= ràng buộc 27 MHz)")
    run.finish("ok" if fmax_ok and c.ok else "fail", res)
    return 0 if fmax_ok and c.ok else 1
