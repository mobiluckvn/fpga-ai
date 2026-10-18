"""cdp selftest — tự kiểm hạ tầng S0.

Bốn phép kiểm, đúng theo tiêu chí ĐẠT của S0 trong docs/PIPELINE_PLAN.md:
  1. spec      — mọi đặc tả trong pipeline/specs/ hợp lệ và phân giải được
  2. ledger    — sổ cái ghi / đọc / xuất CSV được
  3. kitlock   — hai tiến trình cùng xin khoá kit: tiến trình thứ hai CHỜ
  4. targets   — 14 số chu kỳ trong bảng cấu hình = trung vị tính lại từ CSV số đo
                 thật, và chu kỳ kit = chu kỳ Verilator từng ảnh
"""
from __future__ import annotations

import csv
import json
import re
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

from . import paths, provenance, spec as spec_mod, targets
from .ledger import connect, counts, export_csv, upsert

LINE_RE = re.compile(r"^M1S,([a-z]+),?(.*)$")


# --------------------------------------------------------------- kiểm 1
def t_spec(say) -> dict:
    files = sorted(paths.SPECS.glob("*.yaml"))
    ok, bad = spec_mod.check_many(files)
    for s in ok:
        say(f"    {s.path.name} → {s.target.name}")
    for p, e in bad:
        say(f"    {p.name}: {str(e).splitlines()[0]}")
    return {"pass": bool(files) and not bad, "n_files": len(files),
            "n_ok": len(ok), "n_bad": len(bad),
            "resolved": {s.path.name: s.target.name for s in ok},
            "errors": {p.name: str(e) for p, e in bad}}


# --------------------------------------------------------------- kiểm 2
def t_ledger(say) -> dict:
    con = connect()
    probe = "selftest-probe"
    upsert(con, "runs", {"run_id": probe, "cmd": "selftest", "step": "S0",
                         "status": "probe", "params_json": {"probe": True},
                         "note": "dòng thử của cdp selftest, sẽ bị xoá"})
    got = con.execute("SELECT params_json FROM runs WHERE run_id=?", (probe,)).fetchone()
    read_ok = got is not None and json.loads(got[0]) == {"probe": True}
    files = export_csv(con)
    csv_ok = all(f.exists() and f.stat().st_size > 0 for f in files)
    con.execute("DELETE FROM runs WHERE run_id=?", (probe,))
    con.commit()
    gone = con.execute("SELECT 1 FROM runs WHERE run_id=?", (probe,)).fetchone() is None
    c = counts(con)
    con.close()
    for f in files:
        say(f"    xuất {f.relative_to(paths.ROOT)}")
    say(f"    ghi={read_ok} đọc={read_ok} xoá={gone} CSV={csv_ok} · {c}")
    return {"pass": bool(read_ok and csv_ok and gone), "write_read": read_ok,
            "csv": csv_ok, "delete": gone, "counts": c,
            "csv_files": [str(f.relative_to(paths.ROOT)) for f in files]}


# --------------------------------------------------------------- kiểm 3
def t_kitlock(say, hold_a: float = 2.0) -> dict:
    """A giữ khoá hold_a giây; B xin khoá 0,5 s sau → B phải CHỜ rồi mới lấy được."""
    env_py = [sys.executable, "-m", "cdp"]
    kw = dict(cwd=str(paths.ROOT), capture_output=True, text=True,
              env={**__import__("os").environ, "PYTHONPATH": str(paths.PIPELINE)})
    t0 = time.time()
    a = subprocess.Popen(env_py + ["lock", "--hold", str(hold_a), "--owner", "selftest-A"],
                         cwd=str(paths.ROOT), stdout=subprocess.PIPE,
                         stderr=subprocess.STDOUT, text=True,
                         env=kw["env"])
    time.sleep(0.5)
    b = subprocess.run(env_py + ["lock", "--hold", "0.1", "--owner", "selftest-B"], **kw)
    t_b_done = time.time() - t0
    a_out = a.communicate()[0] or ""
    b_out = (b.stdout or "") + (b.stderr or "")
    m = re.search(r"đã lấy được khoá sau khi chờ ([\d.]+) s", b_out)
    waited = float(m.group(1)) if m else 0.0
    b_waited = "CHỜ" in b_out and waited > 0.5
    say(f"    A giữ {hold_a:g} s · B xin sau 0,5 s → B chờ {waited:.2f} s "
        f"(xong ở {t_b_done:.2f} s)")
    if not b_waited:
        say("    đầu ra của B:")
        for ln in b_out.splitlines():
            say("      " + ln)
    return {"pass": bool(b_waited and b.returncode == 0),
            "b_waited_s": waited, "b_total_s": round(t_b_done, 3),
            "hold_a_s": hold_a, "rc_a": a.returncode, "rc_b": b.returncode,
            "b_out": b_out.strip().splitlines()}


# --------------------------------------------------------------- kiểm 4
def _csv_rows(path: Path, label: str) -> list[dict]:
    if not path.exists():
        return []
    return [r for r in csv.DictReader(open(path)) if r["bien_the"] == label]


def _simlog_cyc(path: Path) -> dict[int, dict]:
    out: dict[int, dict] = {}
    if not path.exists():
        return out
    for ln in path.read_text().splitlines():
        m = LINE_RE.match(ln.strip())
        if not m or m.group(1) != "cyc":
            continue
        a = m.group(2).split(",")
        out[int(a[0])] = dict(zip(("conv1", "pool1", "conv2", "pool2", "dense",
                                   "total", "instret"), (int(x) for x in a[1:8])))
    return out


def t_targets(say) -> dict:
    rows = []
    allok = True
    for t in targets.table():
        kit = _csv_rows(paths.ROOT / t.kit_csv, t.kit_csv_label)
        tot = [int(r["total"]) for r in kit]
        sim = [int(r["total_sim"]) for r in kit]
        med = int(st.median(tot)) if tot else None
        sl = _simlog_cyc(paths.ROOT / t.sim_log)
        med_sl = int(st.median([v["total"] for v in sl.values()])) if sl else None
        ok_med = med == t.expect_total_median
        ok_kitsim = bool(tot) and tot == sim
        ok_sl = med_sl == t.expect_total_median
        allok &= bool(ok_med and ok_kitsim and ok_sl and len(kit) == 10)
        rows.append({"target": t.name, "n_csv": len(kit), "median_csv": med,
                     "median_simlog": med_sl, "expect": t.expect_total_median,
                     "ok_median": ok_med, "ok_kit_eq_sim": ok_kitsim,
                     "ok_simlog": ok_sl, "sim_log": t.sim_log})
        say(f"    {t.name:<16} n={len(kit):<3} CSV={med if med else '—':>9} "
            f"simlog={med_sl if med_sl else '—':>9} bảng={t.expect_total_median:>9}  "
            f"{'ĐẠT' if ok_med and ok_kitsim and ok_sl else 'LỆCH'}")
    return {"pass": allok, "rows": rows}


# --------------------------------------------------------------- chạy hết
def main(args, run) -> int:
    out_dir = Path(args.out) if getattr(args, "out", None) else paths.RESULTS_PIPE / "S0"
    out_dir.mkdir(parents=True, exist_ok=True)

    run.say("# cdp selftest — hạ tầng S0")
    run.say(f"git {run.git.get('short')} · SRC_HASH {run.src_hash}")
    run.say("")

    res = {}
    for name, fn, title in (
        ("spec", t_spec, "1. đặc tả YAML hợp lệ và phân giải được"),
        ("ledger", t_ledger, "2. sổ cái ghi/đọc/xuất CSV"),
        ("kitlock", t_kitlock, "3. khoá kit: tiến trình thứ hai phải CHỜ"),
        ("targets", t_targets, "4. bảng 14 cấu hình = trung vị tính lại từ CSV số đo"),
    ):
        run.say(title)
        res[name] = fn(run.say)
        run.say(f"    => {'ĐẠT' if res[name]['pass'] else 'KHÔNG ĐẠT'}")
        run.say("")

    allpass = all(v["pass"] for v in res.values())
    run.say(f"KẾT LUẬN S0: {'ĐẠT' if allpass else 'KHÔNG ĐẠT'}  "
            + " · ".join(f"{k}={'ĐẠT' if v['pass'] else 'KHÔNG'}" for k, v in res.items()))

    tv = provenance.tool_versions()
    (out_dir / "tool_versions.txt").write_text(
        "\n".join(f"{k}: {v}" for k, v in tv.items()) + "\n")
    payload = {"run_id": run.id, "git": run.git, "src_hash": run.src_hash,
               "tools": tv, "pass": allpass, "checks": res}
    (out_dir / "selftest.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    (out_dir / "selftest.log").write_text(Path(run.log_path).read_text())

    run.say(f"đã ghi {out_dir.relative_to(paths.ROOT)}/"
            "{selftest.json,selftest.log,tool_versions.txt}")
    run.finish("ok" if allpass else "fail",
               {"pass": allpass, "checks": {k: v["pass"] for k, v in res.items()},
                "out_dir": str(out_dir.relative_to(paths.ROOT))})
    return 0 if allpass else 1
