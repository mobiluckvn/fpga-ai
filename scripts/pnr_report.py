#!/usr/bin/env python3
"""Đọc report.json của nextpnr-himbaechel, in tài nguyên đã dùng và Fmax.

Dùng: python3 scripts/pnr_report.py <report.json> [--all]
Mặc định chỉ in các loại tài nguyên có used > 0, cộng BSRAM và các khối nhân
(luôn in, kể cả 0, vì đó là số liệu theo dõi của dự án).
"""
import json
import sys

ALWAYS = ("BSRAM", "MULT9X9", "MULT18X18", "MULT36X36",
          "MULTALU18X18", "MULTALU36X18", "MULTADDALU18X18", "ALU54D")


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    path = sys.argv[1]
    show_all = "--all" in sys.argv
    with open(path) as fh:
        rep = json.load(fh)

    util = rep.get("utilization", {})
    rows = []
    for name in sorted(util):
        used = util[name].get("used", 0)
        avail = util[name].get("available", 0)
        if show_all or used > 0 or name in ALWAYS:
            pct = (100.0 * used / avail) if avail else 0.0
            rows.append((name, used, avail, pct))

    w = max((len(r[0]) for r in rows), default=10)
    print(f"{'Tài nguyên'.ljust(w)}  {'dùng':>7} {'/':^1} {'có':>7}   %")
    for name, used, avail, pct in rows:
        print(f"{name.ljust(w)}  {used:>7} / {avail:>7}  {pct:5.1f}%")

    print()
    fmax = rep.get("fmax", {})
    if not fmax:
        print("Fmax: (không có trong report)")
    for clk, d in fmax.items():
        ach = d.get("achieved")
        con = d.get("constraint")
        verdict = ""
        if isinstance(ach, (int, float)) and isinstance(con, (int, float)):
            verdict = "ĐẠT" if ach >= con else "KHÔNG ĐẠT"
        print(f"Fmax[{clk}] = {ach:.2f} MHz (ràng buộc {con} MHz) -> {verdict}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
