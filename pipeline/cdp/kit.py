"""cdp kit — nạp bitstream và đo trên kit thật, qua khoá kit và có đối chứng.

Bọc: `make load-<biến thể>` (openFPGALoader, CHỈ SRAM) và `make check-<biến thể>`
(scripts/m1s_check.py: đọc UART, so CRC với golden, so chu kỳ với Verilator).

Đối chứng đường đo — bài học quan trọng nhất của giai đoạn trước (LOG.md, nhánh B
cổng B3): khi phép đo trả về "không có gì", việc ĐẦU TIÊN là nạp một cấu hình ĐÃ
BIẾT CHẠY (`rtl/mycore/min/top.fs`, phát chuỗi "MIN" qua UART). Không làm vậy thì
dễ đi sửa thiết kế trên một đường đo đã chết. Quy tắc này nằm trong
`scripts/branch_b_measure.sh`; ở đây giữ nguyên tiêu chí: thấy "MIN" >= 2 lần.

An toàn: chỉ nạp SRAM (`openFPGALoader -b tangnano20k file.fs`), KHÔNG ghi flash.
"""
from __future__ import annotations

import csv
import glob
import json
import statistics as st
import time
from pathlib import Path

from . import build as build_mod
from . import kitlock, ledger, paths, spec as spec_mod, wrap
from .util import fmt_int, rel, sh, tool_env

STEP = "S1"
CONTROL_FS = "min/top.fs"


def find_ports(given=None) -> list[str]:
    if given:
        return list(given)
    return sorted(glob.glob("/dev/cu.usbserial*"))


def detect_kit(run) -> dict:
    c = sh(["openFPGALoader", "--detect", "-b", "tangnano20k"], cwd=paths.ROOT,
           env=tool_env(), log_path=run.path("logs", "detect.log"), say=run.say,
           echo=False)
    return {"rc": c.rc, "out": c.out.strip().splitlines()[-4:], "ok": c.ok}


def read_serial(port: str, seconds: float, needle: bytes) -> int:
    """Đếm số lần thấy `needle` trên cổng UART trong `seconds` giây."""
    try:
        import serial
    except ImportError:
        return -1
    try:
        with serial.Serial(port, 115200, timeout=0.5) as s:
            time.sleep(0.4)
            s.reset_input_buffer()
            end = time.time() + seconds
            buf = b""
            while time.time() < end:
                buf += s.read(8192)
        return buf.count(needle)
    except Exception:                                       # noqa: BLE001
        return 0


def control(w: Path, ports: list[str], run) -> dict:
    """Nạp thiết kế tối giản đã biết chạy và kiểm nó có phát byte không."""
    run.say("    [đối chứng] dựng + nạp min/top.fs (thiết kế đã biết chạy)")
    cb = wrap.make(w, "rtl/mycore", "build-min", run=run, log_name="make-build-min.log")
    if not cb.ok:
        return {"ok": False, "reason": "không dựng được min/top.fs"}
    fs = w / "rtl/mycore" / CONTROL_FS
    c = sh(["openFPGALoader", "-b", "tangnano20k", str(fs)], cwd=w / "rtl/mycore",
           env=tool_env(), log_path=run.path("logs", "load-min.log"), say=run.say,
           echo=False)
    counts = {p: read_serial(p, 2.5, b"MIN") for p in ports}
    best = max(counts.values()) if counts else 0
    ok = best >= 2
    # Cổng nào thật sự phát byte thì dùng chính cổng đó để đo. FT2232 hiện ra HAI cổng
    # (một cho JTAG, một cho UART) và thứ tự không bảo đảm, nên ĐOÁN là sai cách —
    # phép đối chứng đã biết câu trả lời, cứ dùng nó.
    port = max(counts, key=lambda k: counts[k]) if counts else None
    run.say(f"    [đối chứng] số lần thấy 'MIN': {counts} → "
            + ("ĐẠT, cổng phát byte: " + str(port) if ok
               else "KHÔNG ĐẠT — đường UART của kit đã chết; cần rút/cắm lại cáp USB"))
    return {"ok": ok, "load_rc": c.rc, "counts": counts, "port": port}


def csv_drop(path: Path, label: str, run) -> int:
    """Xoá các dòng của biến thể `label` trước khi đo lại.

    `scripts/branch_b_measure.sh` có đúng cơ chế này và có lý do: nếu không xoá thì
    đo lại sẽ GHI NỐI, CSV thành 20 dòng cho một biến thể và trung vị mất nghĩa.
    (Đã xảy ra thật ở phiên S6 khi đo lại cấu hình PMAX4.)
    """
    if not path.exists():
        return 0
    rows = list(csv.DictReader(open(path)))
    if not rows:
        return 0
    keep = [r for r in rows if r["bien_the"] != label]
    n = len(rows) - len(keep)
    if n:
        with open(path, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader()
            w.writerows(keep)
        run.say(f"    xoá {n} dòng cũ của `{label}` trong CSV trước khi đo lại")
    return n


def csv_rows(path: Path, label: str) -> list[dict]:
    if not path.exists():
        return []
    return [r for r in csv.DictReader(open(path)) if r["bien_the"] == label]


def main(args, run) -> int:
    if not args.spec:
        run.say("cần --spec <đặc tả.yaml>")
        run.finish("fail")
        return 1
    s = spec_mod.load(args.spec)
    t = s.target
    run.target = t.name
    run.say(f"# cdp kit · đặc tả {s.path.name} → cấu hình {t.name} ({t.hw})")

    ports = find_ports(args.port)
    if not ports:
        run.say("")
        run.say("DỪNG: không thấy cổng UART nào của kit (/dev/cu.usbserial*).")
        run.say("Cần người dùng: cắm Sipeed Tang Nano 20K vào máy bằng cáp USB,")
        run.say("rồi chạy lại. (Chỉ nạp SRAM, không ghi flash.)")
        run.finish("fail", {"reason": "kit chưa cắm", "ports": []})
        return 1
    run.say(f"    cổng UART thấy được: {ports}")

    w = wrap.shadow_tree(args.work, fresh=args.fresh, say=run.say)
    res = {"target": t.name, "spec": rel(s.path), "work": rel(w), "ports": ports,
           "src_hash": run.src_hash}

    res["firmware"] = build_mod.ensure_firmware(w, t, run)
    if "error" in res["firmware"]:
        run.finish("fail", res)
        return 1
    fs = w / t.make_dir / t.var_dir / "top.fs"
    if not fs.exists():
        res["bitstream"] = build_mod.ensure_bitstream(w, t, run)
        if "error" in res["bitstream"]:
            run.finish("fail", res)
            return 1
    sim_log = w / t.make_dir / t.var_dir / "sim.log"
    if not sim_log.exists():
        run.say("    chưa có sim.log trong cây bóng — chạy Verilator trước "
                "(check cần so kit với Verilator)")
        wrap.make(w, t.make_dir, t.t_sim, mvars=t.make_vars, run=run,
                  log_name=f"make-{t.t_sim}.log", timeout=7200)

    # ---------------- vào khoá kit: một kit, tuần tự ----------------
    with kitlock.kit_lock(owner=f"cdp kit {t.name}", timeout=args.lock_timeout,
                          say=run.say):
        res["detect"] = detect_kit(run)
        if not args.no_control:
            res["control_before"] = control(w, ports, run)
            if not res["control_before"]["ok"]:
                run.say("=> DỪNG: đường đo không sống. Rút/cắm lại cáp USB rồi chạy lại.")
                run.finish("fail", res)
                return 1

        csv_drop(w / t.kit_csv, t.kit_csv_label, run)
        run.say(f"    nạp {t.var_dir}/top.fs (SRAM)")
        cl = wrap.make(w, t.make_dir, t.t_load, mvars=t.make_vars, run=run,
                       log_name=f"make-{t.t_load}.log")
        res["load"] = {"rc": cl.rc}

        mvars = dict(t.make_vars)
        # Dùng cổng mà phép đối chứng đã chứng minh là có phát byte.
        mvars["UART_PORT"] = (res.get("control_before", {}) or {}).get("port") or ports[-1]
        if t.branch == "B":
            mvars["CSV_APPEND"] = "--append"
        cc = wrap.make(w, t.make_dir, t.t_check, mvars=mvars, run=run,
                       log_name=f"make-{t.t_check}.log", timeout=1800)
        res["check"] = {"rc": cc.rc, "passed": "M1S_PASS" in cc.out}

        if not res["check"]["passed"] and not args.no_control:
            run.say("    phép đo KHÔNG ĐẠT — phân loại nguyên nhân bằng đối chứng")
            res["control_after"] = control(w, ports, run)

    # ---------------- đọc lại số đo ----------------
    kit_csv = w / t.kit_csv
    rows = csv_rows(kit_csv, t.kit_csv_label)
    res["kit_csv"] = rel(kit_csv) if kit_csv.exists() else None
    res["n_csv_rows"] = len(rows)
    tot = [int(r["total"]) for r in rows]
    sim = [int(r["total_sim"]) for r in rows]
    med = int(st.median(tot)) if tot else None
    res["median_total"] = med
    res["kit_eq_sim_per_image"] = bool(tot) and tot == sim
    res["expect_total"] = t.expect_total_median
    res["median_ok"] = med == t.expect_total_median

    con = ledger.connect()
    if rows:
        res["measurements_written"] = ledger.insert_measurements(
            con, wrap.measurement_rows_from_csv(rows, run.id, t.name, run.src_hash))
    ledger.upsert_candidate(
        con, f"replay.{t.name}", origin="human_replay", round=0,
        title=f"tái tạo {t.name} ({t.hw})",
        status="measured" if res["check"]["passed"] else "rejected",
        measured_cycles_kit=med, src_hash=run.src_hash,
        git_commit=run.git.get("commit"), run_id=run.id)
    con.close()

    chk_log = w / t.make_dir / t.var_dir / "check.log"
    if chk_log.exists():
        run.path("check.log").write_text(chk_log.read_text())
    if kit_csv.exists():
        run.path("kit.csv").write_text(kit_csv.read_text())

    run.say("")
    run.say(f"    số dòng CSV          : {len(rows)} (mong đợi 10)")
    run.say(f"    trung vị chu kỳ/ảnh  : {fmt_int(med)} · bảng "
            f"{fmt_int(t.expect_total_median)} "
            f"{'✓' if res['median_ok'] else '✗'}")
    run.say(f"    kit = Verilator từng ảnh: "
            + ("BẰNG TUYỆT ĐỐI" if res["kit_eq_sim_per_image"] else "LỆCH"))
    run.say(f"    m1s_check.py         : "
            + ("M1S_PASS" if res["check"]["passed"] else "KHÔNG ĐẠT"))

    ok = bool(res["check"]["passed"] and res["median_ok"]
              and res["kit_eq_sim_per_image"] and len(rows) == 10)
    run.path("kit.json").write_text(json.dumps(res, indent=2, ensure_ascii=False))
    run.say("")
    run.say(f"=> {'ĐẠT' if ok else 'KHÔNG ĐẠT'}")
    run.finish("ok" if ok else "fail", res)
    return 0 if ok else 1
