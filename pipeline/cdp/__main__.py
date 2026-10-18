"""CLI của pipeline đồng thiết kế: `python -m cdp <lệnh>` (hoặc `./cdp`).

Mọi lệnh tạo pipeline/runs/<id>/meta.json (git commit, phiên bản công cụ, tham số,
SRC_HASH) và một dòng trong sổ cái pipeline/db/ledger.sqlite.

Mã thoát: 0 = ĐẠT · 1 = KHÔNG ĐẠT · 2 = chưa hiện thực.
"""
from __future__ import annotations

import argparse
import json
import sys
import time

from . import (analyze, build, estimate, kit, kitlock, ledger, paths, profile,
               propose, report, selftest, sim, spec, synth, targets, verify)
from .iss import main as iss_main
from .runctx import Run
from .util import fmt_int

# Lệnh → (hàm, bước, mô tả ngắn, công cụ cần ghi phiên bản)
STEP_OF = {
    "spec": "S0", "db": "S0", "targets": "S0", "lock": "S0", "selftest": "S0",
    "build": "S1", "sim": "S1", "kit": "S1", "synth": "S1",
    "iss": "S2", "profile": "S3", "analyze": "S3",
    "propose": "S5", "estimate": "S6", "verify": "S6", "report": "S8",
}
TOOLS_OF = {
    "build": ["python", "git", "make", "riscv-gcc", "yosys", "nextpnr", "gowin_pack"],
    "sim": ["python", "git", "make", "verilator"],
    "kit": ["python", "git", "make", "openFPGALoader"],
    "synth": ["python", "git", "yosys", "nextpnr", "gowin_pack"],
}


# ---------------------------------------------------------------- lệnh S0
def cmd_db(args, run) -> int:
    con = ledger.connect()
    if args.action == "init":
        run.say(f"sổ cái: {paths.LEDGER.relative_to(paths.ROOT)}")
        run.say("bảng: " + ", ".join(f"{k}={v}" for k, v in ledger.counts(con).items()))
    elif args.action == "export":
        files = ledger.export_csv(con)
        for f in files:
            n = sum(1 for _ in open(f)) - 1
            run.say(f"đã xuất {f.relative_to(paths.ROOT)} ({n} dòng)")
    elif args.action == "show":
        rows = con.execute(
            "SELECT run_id, cmd, step, status, target, duration_s FROM runs "
            "ORDER BY started_at DESC LIMIT ?", (args.limit,)).fetchall()
        run.say(f"{'run_id':<30}{'cmd':<10}{'bước':<6}{'trạng thái':<18}{'cấu hình':<16}{'giây':>7}")
        for r in rows:
            run.say(f"{r['run_id']:<30}{r['cmd']:<10}{str(r['step'] or ''):<6}"
                    f"{r['status']:<18}{str(r['target'] or ''):<16}"
                    f"{(r['duration_s'] or 0):>7.1f}")
        run.say("")
        run.say("bảng: " + ", ".join(f"{k}={v}" for k, v in ledger.counts(con).items()))
    counts = ledger.counts(con)
    con.close()
    run.finish("ok", {"action": args.action, "counts": counts})
    return 0


def cmd_targets(args, run) -> int:
    rows = targets.table()
    if args.json:
        run.say(json.dumps([t.as_dict() for t in rows], indent=2, ensure_ascii=False))
    else:
        run.say(f"{'#':>2}  {'cấu hình':<16}{'lõi':<10}{'fw':<7}{'thư mục':<8}"
                f"{'chu kỳ/ảnh':>13}{'ms':>7}  cờ")
        for t in rows:
            run.say(f"{t.row:>2}  {t.name:<16}{t.core:<10}{t.fw_id:<7}{t.var_dir:<8}"
                    f"{fmt_int(t.expect_total_median):>13}{t.ms:>7.1f}  "
                    + (",".join(sorted(t.fw_flags)) or "—"))
        run.say("")
        run.say("Nguồn số: results/experiment/m1s/m1s.csv · results/branch_b/m1s_b.csv "
                "(trung vị 10 ảnh) — bảng docs/KET_QUA_TONG_HOP.md mục 1")
    run.finish("ok", {"n_targets": len(rows)})
    return 0


def cmd_lock(args, run) -> int:
    """Giữ khoá kit một lúc. Dùng để kiểm cơ chế tuần tự, và để người dùng giữ kit."""
    t0 = time.time()
    try:
        with kitlock.kit_lock(owner=args.owner or f"cdp lock pid={run.id}",
                              timeout=args.timeout, say=run.say) as info:
            waited = info["waited_s"]
            run.say(f"[{time.strftime('%H:%M:%S')}] GIỮ khoá kit "
                    f"(chờ {waited:.2f} s) trong {args.hold:g} s")
            time.sleep(args.hold)
            run.say(f"[{time.strftime('%H:%M:%S')}] NHẢ khoá kit")
    except TimeoutError as exc:
        run.say(f"KHÔNG lấy được khoá: {exc}")
        run.finish("fail", {"waited_s": round(time.time() - t0, 3)})
        return 1
    run.finish("ok", {"waited_s": waited, "held_s": args.hold})
    return 0


# ---------------------------------------------------------------- bảng điều phối
HANDLERS = {
    "spec": spec.main, "db": cmd_db, "targets": cmd_targets, "lock": cmd_lock,
    "selftest": selftest.main,
    "build": build.main, "sim": sim.main, "kit": kit.main, "synth": synth.main,
    "iss": iss_main, "profile": profile.main, "analyze": analyze.main,
    "propose": propose.main, "estimate": estimate.main, "verify": verify.main,
    "report": report.main,
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        prog="cdp", description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quiet", action="store_true", help="chỉ ghi log, không in")
    sub = ap.add_subparsers(dest="cmd", required=True, metavar="<lệnh>")

    p = sub.add_parser("spec", help="kiểm và chuẩn hoá đặc tả YAML")
    p.add_argument("files", nargs="*", help="mặc định: mọi file pipeline/specs/*.yaml")

    p = sub.add_parser("db", help="sổ cái: init | export | show")
    p.add_argument("action", choices=["init", "export", "show"], nargs="?", default="show")
    p.add_argument("--limit", type=int, default=20)

    p = sub.add_parser("targets", help="bảng 14 cấu hình đã đo")
    p.add_argument("--json", action="store_true")

    p = sub.add_parser("lock", help="giữ khoá kit (kiểm cơ chế tuần tự)")
    p.add_argument("--hold", type=float, default=1.0, help="giữ bao nhiêu giây")
    p.add_argument("--timeout", type=float, default=None, help="chờ tối đa bao lâu")
    p.add_argument("--owner", default=None)

    p = sub.add_parser("selftest", help="tự kiểm hạ tầng S0")
    p.add_argument("--out", default=None, help="thư mục ghi kết quả "
                                              "(mặc định results/pipeline/S0)")

    # ---- S1: bọc Makefile có sẵn, dựng trong cây bóng ----
    p = sub.add_parser("build", help="dựng firmware (+ bitstream) ngoài cây")
    p.add_argument("--spec", required=False, help="đặc tả YAML")
    p.add_argument("--work", default="s1", help="tên cây bóng trong pipeline/work/")
    p.add_argument("--fresh", action="store_true", help="dựng lại cây bóng từ đầu")
    p.add_argument("--bitstream", action="store_true", help="dựng cả bitstream (chậm)")

    p = sub.add_parser("sim", help="chạy Verilator và đối chứng từng con số")
    p.add_argument("--spec", required=False)
    p.add_argument("--work", default="s1")
    p.add_argument("--fresh", action="store_true")

    p = sub.add_parser("kit", help="nạp + đo trên kit (qua khoá kit, có đối chứng)")
    p.add_argument("--spec", required=False)
    p.add_argument("--work", default="s1")
    p.add_argument("--fresh", action="store_true")
    p.add_argument("--port", action="append", default=None, help="cổng UART của kit")
    p.add_argument("--repeat", type=int, default=2, help="số lần đọc độc lập")
    p.add_argument("--no-control", action="store_true",
                   help="bỏ đối chứng đường đo (KHÔNG khuyến nghị)")
    p.add_argument("--lock-timeout", type=float, default=None)

    p = sub.add_parser("synth", help="tổng hợp: LUT/DFF/MULT/BSRAM + Fmax")
    p.add_argument("--spec", required=False)
    p.add_argument("--work", default="s1")
    p.add_argument("--fresh", action="store_true")

    for name, mod in (("profile", profile), ("analyze", analyze), ("propose", propose),
                      ("estimate", estimate), ("verify", verify), ("report", report)):
        p = sub.add_parser(name, help=(mod.__doc__ or "").splitlines()[0])
        p.add_argument("--spec", default=None, help="đặc tả YAML")
        p.add_argument("rest", nargs="*")
    p = sub.add_parser("iss", help="ISS RV32IM + mô hình chu kỳ, đối chứng Verilator")
    p.add_argument("--spec", default=None, help="đặc tả YAML")
    p.add_argument("--target", default=None, help="tên cấu hình, vd B-V3")
    p.add_argument("--all", action="store_true", help="chạy cả 14 cấu hình")
    p.add_argument("--calibrate", default=None, metavar="LÕI",
                   help="hiệu chuẩn mô hình chu kỳ (chỉ 'picorv32')")
    p.add_argument("--pc-hist", action="store_true",
                   help="đếm số lần thực thi theo từng địa chỉ lệnh (cho S3)")
    p.add_argument("--check-k1", action="store_true",
                   help="kiểm phép K1 của lý thuyết: mô hình nghịch vs số ISS đếm")
    p.add_argument("--work", default="s1")
    return ap


def main(argv=None) -> int:
    ap = build_parser()
    args = ap.parse_args(argv)
    cmd = args.cmd
    params = {k: v for k, v in vars(args).items() if k not in ("cmd", "quiet")}
    run = Run(cmd, params=params, step=STEP_OF.get(cmd),
              spec=getattr(args, "spec", None), tools=TOOLS_OF.get(cmd),
              quiet=args.quiet)
    try:
        rc = HANDLERS[cmd](args, run)
    except Exception as exc:                                # noqa: BLE001
        run.say(f"LỖI {type(exc).__name__}: {exc}")
        import traceback
        run.say(traceback.format_exc())
        run.finish("fail", {"error": f"{type(exc).__name__}: {exc}"})
        return 1
    if run.status == "running":
        run.finish("ok" if rc == 0 else "fail")
    return rc


if __name__ == "__main__":
    sys.exit(main())
