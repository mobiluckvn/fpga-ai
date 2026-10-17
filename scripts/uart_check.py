#!/usr/bin/env python3
"""F2 — kiểm tra UART hai chiều với kit Tang Nano 20K.

Ba pha:
  Pha 1  đồng bộ tới ranh giới dòng, đọc một dòng
         "F2 OK dddd rx=.... tx=.... dr=.... er=.. ov=. hw=.."  (timeout mặc định 5 s).
  Pha 2  gửi N byte ngẫu nhiên (hạt giống cố định) theo khối, so sánh echo từng byte.
  Pha 3  đọc lại dòng chẩn đoán, đối chiếu bộ đếm BÊN TRONG FPGA (mốc lấy ngay trước pha 2):
         rx phải tăng đúng N, dr (byte bị bỏ vì FIFO đầy) = 0, er (lỗi bit stop) = 0,
         ov (FIFO từng tràn) = 0. hw = mức FIFO cao nhất, chỉ để tham khảo.

Nhờ pha 3, phép kiểm phân biệt được lỗi của FPGA và lỗi của cầu USB/driver trên máy chủ.

KÍCH THƯỚC KHỐI: mặc định 64 byte = đúng một gói USB. Đo trên máy này cho thấy nếu host
ghi hơn ~66 byte trong một lần write() thì chiều FPGA->PC bị mất byte, dù bộ đếm trong FPGA
chứng minh FPGA nhận đủ và phát đủ. Đó là giới hạn của cầu FT2232/driver macOS, không phải
của thiết kế. Dùng --sweep để đo lại ngưỡng này.

Tự tìm cổng: thử mọi /dev/cu.usbserial* (cầu FT2232 của kit hiện ra hai cổng — quy tắc 9
trong CLAUDE.md). Mọi lần mở cổng đều có timeout và đóng cổng sau khi dùng.

Mã thoát 0 = ĐẠT.
"""
from __future__ import annotations

import argparse
import glob
import random
import re
import sys
import time

import serial

MSG_PREFIX = b"F2 OK "
DIAG_KEYS = ("rx", "tx", "dr", "er", "ov", "hw")


class Tee:
    def __init__(self, fh):
        self.fh = fh

    def __call__(self, *parts):
        line = " ".join(str(p) for p in parts)
        print(line, flush=True)
        if self.fh:
            self.fh.write(line + "\n")
            self.fh.flush()


def parse_diag(line: str) -> dict:
    return {k: int(v, 16) for k, v in re.findall(r"(\w+)=([0-9A-Fa-f]+)", line)}


def sync_line(ser, timeout):
    """Đọc tới khi vừa kết thúc trọn một dòng và bộ đệm không còn byte dư.

    Trả về (dòng, chẩn đoán) hoặc (None, {}). Sau khi trả về, đường truyền im tới
    dòng kế tiếp (~1 s) nên pha 2 bắt đầu trên nền sạch, không lẫn byte cũ.
    """
    buf = b""
    last = None
    t0 = time.time()
    while time.time() - t0 < timeout:
        chunk = ser.read(512)
        if not chunk:
            continue
        buf += chunk
        while b"\r\n" in buf:
            last, _, buf = buf.partition(b"\r\n")
        if buf == b"" and last is not None and last.startswith(MSG_PREFIX):
            text = last.decode("ascii", "replace")
            diag = parse_diag(text)
            if all(k in diag for k in DIAG_KEYS):
                return text, diag
            return text, diag
    return None, {}


def echo_test(ser, say, nbytes, block, seed):
    rng = random.Random(seed)
    payload = bytes(rng.randrange(256) for _ in range(nbytes))
    got = bytearray()
    t0 = time.time()
    for off in range(0, nbytes, block):
        piece = payload[off:off + block]
        ser.write(piece)
        ser.flush()
        deadline = time.time() + 5.0
        back = bytearray()
        while len(back) < len(piece) and time.time() < deadline:
            r = ser.read(len(piece) - len(back))
            if r:
                back += r
        got += back
        if len(back) != len(piece):
            say(f"    LỖI: khối tại offset {off}: chờ {len(piece)} byte, chỉ nhận {len(back)}")
            return False, payload, bytes(got), time.time() - t0
    return True, payload, bytes(got), time.time() - t0


def compare(payload, got, say):
    nbad = 0
    first = None
    for i, (a, b) in enumerate(zip(payload, got)):
        if a != b:
            nbad += 1
            if first is None:
                first = i
    if len(payload) != len(got):
        say(f"    LỖI: số byte echo {len(got)} != đã gửi {len(payload)}")
    if nbad:
        lo = max(0, first - 8)
        hi = min(len(payload), first + 8)
        say(f"    LỖI: {nbad} byte sai, byte sai đầu tiên ở offset {first}")
        say(f"      đã gửi [{lo}:{hi}] = {payload[lo:hi].hex(' ')}")
        say(f"      nhận   [{lo}:{hi}] = {got[lo:hi].hex(' ')}")
    return nbad


def sweep(ser, say, seed):
    """Đo kích thước khối lớn nhất mà chiều FPGA->PC còn nguyên vẹn."""
    say("    --- quét kích thước khối (512 byte mỗi lần) ---")
    best = 0
    for blk in (16, 32, 64, 65, 66, 67, 68, 96, 128, 256):
        sync_line(ser, 6.0)
        ok, payload, got, _ = echo_test(ser, say, 512, blk, seed)
        nbad = sum(1 for a, b in zip(payload, got) if a != b)
        good = ok and nbad == 0 and len(got) == 512
        say(f"      khối {blk:4d}: {'nguyên vẹn' if good else f'MẤT/SAI {nbad} byte'}")
        if good:
            best = max(best, blk)
    say(f"    => khối lớn nhất còn nguyên vẹn: {best} byte")
    return best


def try_port(port, args, say):
    say(f"--- Thử cổng {port} @ {args.baud} 8N1 ---")
    try:
        ser = serial.Serial(port, args.baud, timeout=0.2, write_timeout=5.0)
    except Exception as exc:  # noqa: BLE001
        say(f"    không mở được: {type(exc).__name__}: {exc}")
        return False, None
    try:
        time.sleep(0.1)
        ser.reset_input_buffer()

        # ---- Pha 1 ----
        t0 = time.time()
        line, d0 = sync_line(ser, args.msg_timeout)
        waited = time.time() - t0
        if line is None:
            say(f"    Pha 1 KHÔNG ĐẠT: sau {waited:.2f}s không thấy dòng 'F2 OK'")
            return False, None
        say(f"    Pha 1 ĐẠT sau {waited:.2f}s: {line!r}")
        if not all(k in d0 for k in DIAG_KEYS):
            say(f"    CẢNH BÁO: dòng thiếu trường chẩn đoán ({sorted(d0)})")

        if args.sweep:
            sweep(ser, say, args.seed)

        # Lấy lại mốc bộ đếm NGAY TRƯỚC pha 2: nếu đã quét thì bộ đếm rx của FPGA
        # đã cộng thêm phần byte của bài quét, mốc cũ không còn dùng được.
        line0, d0 = sync_line(ser, 8.0)
        if line0 is None or not all(k in d0 for k in DIAG_KEYS):
            say("    KHÔNG ĐẠT: không lấy được mốc bộ đếm trước pha 2")
            return False, None
        say(f"    Mốc trước pha 2: {line0!r}")

        # ---- Pha 2 ----
        ok, payload, got, dt = echo_test(ser, say, args.bytes, args.block, args.seed)
        nbad = compare(payload, got, say)
        if not ok or nbad or len(got) != args.bytes:
            say("    Pha 2 KHÔNG ĐẠT")
            return False, None
        rate = len(got) / dt if dt > 0 else 0.0
        say(f"    Pha 2 ĐẠT: {len(got)} byte echo khớp 100% (khối {args.block} byte), "
            f"{dt:.3f}s => {rate:.0f} byte/s ≈ {rate*10:.0f} bit/s "
            f"(trần lý thuyết một chiều {args.baud} bit/s)")

        # ---- Pha 3 ----
        line1, d1 = sync_line(ser, 8.0)
        if line1 is None or not all(k in d1 for k in DIAG_KEYS):
            say("    Pha 3 KHÔNG ĐẠT: không đọc lại được dòng chẩn đoán")
            return False, None
        say(f"    Pha 3 dòng chẩn đoán sau bài kiểm: {line1!r}")
        drx = (d1["rx"] - d0["rx"]) % 65536
        probs = []
        if drx != args.bytes:
            probs.append(f"rx tăng {drx}, kỳ vọng {args.bytes}")
        if d1["dr"] != 0:
            probs.append(f"dr={d1['dr']} (FPGA phải bỏ byte vì FIFO đầy)")
        if d1["er"] != 0:
            probs.append(f"er={d1['er']} (lỗi bit stop ở phía FPGA)")
        if d1["ov"] != 0:
            probs.append(f"ov={d1['ov']} (FIFO từng tràn)")
        if probs:
            say("    Pha 3 KHÔNG ĐẠT: " + "; ".join(probs))
            return False, None
        say(f"    Pha 3 ĐẠT: FPGA rx tăng đúng {drx}; dr=0 er=0 ov=0; "
            f"mức FIFO cao nhất hw={d1['hw']}/63")

        return True, {"port": port, "line": line, "line_after": line1,
                      "bytes": len(got), "seconds": dt, "rate": rate,
                      "block": args.block, "hw": d1["hw"], "wait_msg": waited}
    finally:
        ser.close()
        say(f"    (đã đóng {port})")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--port", action="append", default=None,
                    help="cổng cụ thể; lặp lại được. Mặc định: mọi /dev/cu.usbserial*")
    ap.add_argument("--baud", type=int, default=115200)
    ap.add_argument("--bytes", type=int, default=10240)
    ap.add_argument("--block", type=int, default=64,
                    help="byte mỗi lần write() (mặc định 64 = một gói USB)")
    ap.add_argument("--seed", type=int, default=20261017)
    ap.add_argument("--msg-timeout", type=float, default=5.0)
    ap.add_argument("--sweep", action="store_true",
                    help="đo luôn kích thước khối lớn nhất còn nguyên vẹn")
    ap.add_argument("--log", default=None, help="ghi log ra file")
    args = ap.parse_args()

    fh = open(args.log, "w") if args.log else None
    say = Tee(fh)
    try:
        ports = args.port or sorted(glob.glob("/dev/cu.usbserial*"))
        say("# F2 uart_check")
        say(f"Thời điểm: {time.strftime('%Y-%m-%d %H:%M:%S %z')}")
        say(f"Cổng sẽ thử: {ports}")
        say(f"Tham số: baud={args.baud} bytes={args.bytes} block={args.block} "
            f"seed={args.seed} sweep={args.sweep}")
        if not ports:
            say("LỖI: không tìm thấy cổng /dev/cu.usbserial*")
            return 1

        results = []
        for p in ports:
            ok, info = try_port(p, args, say)
            results.append((p, ok, info))
            if ok:
                break

        say("")
        say("## Kết quả")
        for p, ok, _ in results:
            say(f"  {p}: {'ĐẠT' if ok else 'không phải cổng UART của FPGA / không đạt'}")
        good = [i for _, ok, i in results if ok]
        if good:
            g = good[0]
            say("")
            say(f"F2_UART_PASS cổng={g['port']} byte_echo={g['bytes']} byte_sai=0 "
                f"khối={g['block']} thời_gian={g['seconds']:.3f}s "
                f"tốc_độ={g['rate']:.0f}B/s fifo_hwm={g['hw']}")
            return 0
        say("")
        say("F2_UART_FAIL: không cổng nào đạt")
        return 1
    finally:
        if fh:
            fh.close()


if __name__ == "__main__":
    sys.exit(main())
