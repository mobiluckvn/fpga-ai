#!/usr/bin/env python3
"""In bảng so sánh nhánh A (PicoRV32) ↔ nhánh B (lõi tự viết) từ hai file CSV."""
import csv, statistics as st
from pathlib import Path
R = Path(__file__).resolve().parent.parent
MACS, F = 192064, 27e6

def load(p):
    d = {}
    for r in csv.DictReader(open(p)):
        d.setdefault(r['bien_the'], []).append(r)
    return d

A = load(R / 'results/experiment/m1s/m1s.csv')
B = load(R / 'results/branch_b/m1s_b.csv')
med = lambda rs, k: int(st.median([int(x[k]) for x in rs]))
PAIRS = [("A-V0","bv0","C thẳng"), ("A-V1","bv1","+tối ưu phần mềm"),
         ("A-V2","bv2","C thẳng + DOT4"), ("A-V1+DOT4","bv1d","+tối ưu PM + DOT4"),
         ("A-V1+DOT4+C1","bv1dc","+bố cục 4 pha")]
base = med(A['A-V0'], 'total') if 'A-V0' in A else None

print(f"{'biến thể':<20}{'A chu kỳ':>12}{'A ms':>8}{'B chu kỳ':>12}{'B ms':>8}"
      f"{'B/A':>7}{'instret':>9}{'B so A-V0':>11}")
for av, bv, name in PAIRS:
    if av not in A or bv not in B:
        print(f"{name:<20}{'(chưa đo)':>58}")
        continue
    ta, tb = med(A[av],'total'), med(B[bv],'total')
    ia, ib = med(A[av],'instret'), med(B[bv],'instret')
    print(f"{name:<20}{ta:>12,}{ta/F*1000:>8.1f}{tb:>12,}{tb/F*1000:>8.1f}"
          f"{ta/tb:>6.2f}x{('KHỚP' if ia==ib else 'LỆCH'):>9}"
          f"{(base/tb if base else 0):>10.2f}x")

if 'bv1' in B and 'bv1d' in B:
    print(f"\nDOT4 trên lõi tự viết : {med(B['bv1'],'total')/med(B['bv1d'],'total'):.2f}x")
if 'A-V1' in A and 'A-V1+DOT4' in A:
    print(f"DOT4 trên PicoRV32    : {med(A['A-V1'],'total')/med(A['A-V1+DOT4'],'total'):.2f}x")
if 'bv1dc' in B:
    t = med(B['bv1dc'],'total')
    print(f"\nNhanh nhất (B-V1+DOT4+C1): {t:,} chu kỳ · {t/F*1000:.1f} ms · "
          f"{t/MACS:.2f} chu kỳ/MAC · {F/t:.1f} ảnh/giây")
    if base: print(f"  so A-V0: {base/t:.1f}x")
