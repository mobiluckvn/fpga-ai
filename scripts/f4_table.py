#!/usr/bin/env python3
"""F4 — lập bảng so sánh tài nguyên/Fmax của các biến thể từ report.json của nextpnr.

Dùng: python3 scripts/f4_table.py <thư mục F4_dsp>
"""
import json
import sys
from pathlib import Path

NAMES = {
    "dsp":   ("DSP",  "yosys tự suy luận (mul2dsp -> MULT9X9)"),
    "dsp18": ("D18",  "toán hạng mở rộng dấu 18 bit (yosys vẫn chọn MULT9X9)"),
    "prm":   ("PRM",  "gọi trực tiếp MULT18X18, chế độ không dấu"),
    "lut":   ("LUT",  "synth_gowin -nodsp, nhân bằng logic"),
}
KEYS = ("LUT4", "DFF", "ALU", "MULT9X9", "MULT18X18", "DUMMY_CELL")


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".")
    print("| Biến thể | Cách dựng phép nhân | LUT4 | DFF | ALU | MULT9X9 | MULT18X18 | DUMMY | Fmax (MHz) | Kết quả trên kit |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---|")
    for v, (label, how) in NAMES.items():
        rep = root / f"build_{v}" / "report.json"
        chk = root / f"build_{v}" / "f4_check.log"
        if not rep.exists():
            continue
        d = json.load(open(rep))
        u = d["utilization"]
        fm = list(d["fmax"].values())[0]["achieved"]
        vals = [u.get(k, {}).get("used", 0) for k in KEYS]
        verdict = "chưa kiểm"
        if chk.exists():
            txt = chk.read_text()
            if "F4_PASS" in txt:
                verdict = "**ĐÚNG** (3/3 lần đọc)"
            elif "F4_FAIL" in txt:
                verdict = "**SAI**"
        print(f"| {label} | {how} | " + " | ".join(str(x) for x in vals) +
              f" | {fm:.2f} | {verdict} |")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
