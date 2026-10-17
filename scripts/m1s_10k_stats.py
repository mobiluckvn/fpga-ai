#!/usr/bin/env python3
"""Thống kê lần chạy 10.000 ảnh trên kit (từ results/experiment/m1s/m1s_10k.csv).

In: độ chính xác, số CRC khớp, ma trận nhầm lẫn, và phân bố chu kỳ từng lớp —
để trả lời "lớp nào tất định, lớp nào phụ thuộc dữ liệu".
"""
import argparse
import csv
import statistics as st
from collections import Counter

LAYERS = ["conv1", "pool1", "conv2", "pool2", "dense", "tot"]
F = 27e6
MACS = 192064


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv", nargs="?", default="results/experiment/m1s/m1s_10k.csv")
    a = ap.parse_args()
    rows = list(csv.DictReader(open(a.csv)))
    n = len(rows)
    if n == 0:
        print("CSV rỗng")
        return 1

    lab_ok = sum(1 for r in rows if int(r["pred"]) == int(r["label"]))
    gold_ok = sum(1 for r in rows if int(r["pred"]) == int(r["pred_golden"]))
    crc_ok = sum(int(r["crc_logit_ok"]) for r in rows)

    print(f"số ảnh                     : {n}")
    print(f"CRC32 logit khớp golden    : {crc_ok}/{n} ({crc_ok/n*100:.2f}%)")
    print(f"dự đoán khớp golden        : {gold_ok}/{n} ({gold_ok/n*100:.2f}%)")
    print(f"ĐỘ CHÍNH XÁC ĐO TRÊN KIT   : {lab_ok}/{n} = {lab_ok/n*100:.2f}%")
    print()
    print(f"{'lớp':<8} {'trung vị':>12} {'nhỏ nhất':>12} {'lớn nhất':>12} {'biên độ':>9} {'độ lệch ch.':>12}")
    for L in LAYERS:
        v = [int(r[L]) for r in rows]
        print(f"{L:<8} {st.median(v):>12,.0f} {min(v):>12,} {max(v):>12,} "
              f"{max(v)-min(v):>9,} {st.pstdev(v):>12,.1f}")
    tot = [int(r["tot"]) for r in rows]
    ins = [int(r["instret"]) for r in rows]
    med = st.median(tot)
    print()
    print(f"thời gian/ảnh @27 MHz      : trung vị {med/F*1000:.2f} ms  "
          f"(nhanh nhất {min(tot)/F*1000:.2f} · chậm nhất {max(tot)/F*1000:.2f})")
    print(f"chu kỳ/MAC                 : {med/MACS:.3f}")
    print(f"ảnh/giây                   : {F/med:.2f}")
    print(f"số lệnh/ảnh                : trung vị {st.median(ins):,.0f}  "
          f"IPC = {st.median(ins)/med:.3f}")

    # ảnh sai: để biết kit sai ở đâu (phải GIỐNG chỗ golden sai)
    bad = [r for r in rows if int(r["pred"]) != int(r["label"])]
    print(f"\nsố ảnh dự đoán sai nhãn    : {len(bad)}")
    c = Counter((int(r["label"]), int(r["pred"])) for r in bad)
    print("10 cặp nhầm nhiều nhất (nhãn -> dự đoán):")
    for (lb, pr), k in c.most_common(10):
        print(f"  {lb} -> {pr} : {k} lần")
    mism = [r for r in rows if int(r["pred"]) != int(r["pred_golden"])]
    if mism:
        print(f"\nCẢNH BÁO: {len(mism)} ảnh kit khác golden: "
              f"{[int(r['idx']) for r in mism][:20]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
