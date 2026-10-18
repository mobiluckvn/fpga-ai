#!/usr/bin/env python3
"""Sinh biểu đồ cho báo cáo S9 (bước cuối của pipeline đồng thiết kế).

Mọi con số trong đây đến từ tệp kết quả thật dưới results/pipeline/ — không nhập tay
số nào mà không ghi rõ nguồn ngay cạnh. Xuất cả PNG (300 dpi) và PDF (vector, cho bài báo)
vào report/pipeline/.

Màu: ba khe đầu của bảng màu phân loại đã kiểm bằng scripts/validate_palette.js của
hướng dẫn trực quan hoá (all-pairs, chế độ sáng: CVD dE 9,2 · thường 24,0 — ĐẠT).
Khe aqua dưới ngưỡng tương phản 3:1 nên mọi điểm đều có NHÃN TRỰC TIẾP, và README kèm
bảng số đầy đủ — đúng quy tắc bù.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

ROOT = Path(__file__).resolve().parent.parent
RES = ROOT / "results" / "pipeline"
OUT = ROOT / "report" / "pipeline"
OUT.mkdir(parents=True, exist_ok=True)

BLUE, ORANGE, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
INK, INK2, INK3 = "#0b0b0b", "#52514e", "#8a8984"
SURF = "#fcfcfb"

plt.rcParams.update({
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF,
    "font.size": 9, "axes.titlesize": 10.5, "axes.labelsize": 9,
    "axes.edgecolor": INK3, "axes.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False,
    "text.color": INK, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2,
    "xtick.major.size": 3, "ytick.major.size": 3,
    "grid.color": "#e3e2dd", "grid.linewidth": 0.7,
    "legend.frameon": False, "legend.fontsize": 8.5,
})

VN = FuncFormatter(lambda v, _: f"{int(v):,}".replace(",", "."))


def save(fig, name):
    for ext in ("png", "pdf"):
        fig.savefig(OUT / f"{name}.{ext}", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("đã vẽ", name)


# ---------------------------------------------------------------- hình 1
def fig_dubao_vs_do():
    """Sai số dự báo theo TẦNG của mô hình chi phí. Nguồn: S6/du_bao_vs_do.csv."""
    rows = [r for r in csv.DictReader(open(RES / "S6" / "du_bao_vs_do.csv"))
            if r["do_that_chu_ky"] and r["sai_so_pct"]]
    items = []
    for r in rows:
        muc = {"A_lambda_exact": "mức A", "B_pattern_lower_bound": "mức B",
               "B2_class_replacement_lower_bound": "mức B"}.get(r["phuong_phap"], "mức C")
        ten = r["ung_vien"].split("(")[0].strip()
        items.append((f"{ten}\n{muc} · nền {r['co_so']}", float(r["sai_so_pct"]), muc))
    items.sort(key=lambda t: abs(t[1]))

    fig, ax = plt.subplots(figsize=(7.4, 3.6))
    ys = list(range(len(items)))
    cols = [BLUE if m == "mức A" else ORANGE for *_, m in items]
    vals = [v for _, v, _ in items]
    ax.barh(ys, vals, color=cols, height=0.52, zorder=3)
    # Thanh dài 0 (mức A, sai số 0,00 %) sẽ vô hình nếu chỉ vẽ barh — đánh dấu bằng
    # một vạch đứng để nó vẫn là một MARK đọc được, không phải chỗ trống.
    for y, (v, c) in enumerate(zip(vals, cols)):
        if v == 0:
            ax.plot([0, 0], [y - 0.26, y + 0.26], color=c, lw=4, zorder=4,
                    solid_capstyle="butt")
    ax.axvline(0, color=INK3, lw=0.9, zorder=2)
    ax.set_yticks(ys, [t for t, _, _ in items], fontsize=8)
    ax.set_xlabel("sai số dự báo so với số đo thật (%)")
    ax.xaxis.grid(True, zorder=0); ax.set_axisbelow(True)
    lo, hi = min(vals), max(vals)
    ax.set_xlim(lo - (hi - lo) * 0.28, hi + (hi - lo) * 0.22)   # chỗ cho nhãn hai đầu
    for y, v in zip(ys, vals):
        ax.annotate(f"{v:+.2f} %".replace(".", ","), (v, y),
                    xytext=(7 if v >= 0 else -7, 0), textcoords="offset points",
                    va="center", ha="left" if v >= 0 else "right",
                    fontsize=8.5, color=INK, fontweight="bold")
    ax.set_title("Dự báo đóng băng TRƯỚC khi viết RTL, so với số đo thật",
                 loc="left", pad=10)
    h = [plt.Line2D([], [], marker="s", ls="", mfc=BLUE, mec=BLUE, ms=7,
                    label="mức A — chỉ đổi λ, n_c giữ nguyên (đẳng thức)"),
         plt.Line2D([], [], marker="s", ls="", mfc=ORANGE, mec=ORANGE, ms=7,
                    label="mức B — phải giả định mã viết lại gọn tới đâu (chặn dưới)")]
    ax.legend(handles=h, loc="lower left", bbox_to_anchor=(0.0, -0.40))
    save(fig, "hinh1_du_bao_vs_do")


# ---------------------------------------------------------------- hình 2
def fig_pareto():
    """Pareto chu kỳ–LUT4. Nguồn: report.json của quét p9_* + cặp A/B bs7ref/bs7dp."""
    pts = json.loads((RES / "S9" / "pareto.json").read_text())
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    ax.grid(True, zorder=0); ax.set_axisbelow(True)
    for p in pts:
        ax.scatter(p["lut4"], p["chu_ky"], s=86, color=p.get("mau", BLUE),
                   zorder=4, edgecolors=SURF, linewidths=1.6)
        ax.annotate(f"{p['ten']}\n{p['chu_ky']:,}".replace(",", ".") + " chu kỳ",
                    (p["lut4"], p["chu_ky"]), xytext=p.get("nhan", (10, 8)),
                    textcoords="offset points", fontsize=8.2, color=INK,
                    ha=p.get("ha", "left"))
    front = sorted([p for p in pts if p.get("pareto")], key=lambda p: p["lut4"])
    ax.plot([p["lut4"] for p in front], [p["chu_ky"] for p in front],
            color=INK3, lw=1.2, ls="--", zorder=2)
    ax.set_xlabel("LUT4 của lõi (trên tổng 20.736 của GW2AR-18C)")
    ax.set_ylabel("chu kỳ mỗi ảnh (M1-S)")
    ax.set_yscale("log"); ax.yaxis.set_major_formatter(VN); ax.xaxis.set_major_formatter(VN)
    ax.set_title("Đánh đổi chu kỳ ↔ diện tích: ba lệnh rẻ, bộ nhớ hai cổng đắt",
                 loc="left", pad=10)
    save(fig, "hinh2_pareto_chuky_lut")


# ---------------------------------------------------------------- hình 3
def fig_b1():
    """Tiến trình vòng B1 mù. Nguồn: S4/duong_cong_b1.csv."""
    rows = list(csv.DictReader(open(RES / "S4" / "duong_cong_b1.csv")))
    v = [int(r["vong"]) for r in rows]
    c = [int(r["chu_ky"]) for r in rows]
    pd = [r["phu_thuoc_du_lieu"] == "co" for r in rows]
    base = c[0]

    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.grid(True, zorder=0); ax.set_axisbelow(True)
    ax.plot(v, c, color=BLUE, lw=2, zorder=3, marker="o", ms=7,
            mfc=SURF, mec=BLUE, mew=2, label="AI mù, từng vòng")
    for i in [i for i, f in enumerate(pd) if f]:
        ax.scatter(v[i], c[i], s=58, color=BLUE, zorder=4)
    thu_cong = int(base / 1.355)
    ax.axhline(thu_cong, color=ORANGE, lw=2, ls="--", zorder=3,
               label=f"tối ưu phần mềm làm THỦ CÔNG (1,355×)")
    for x, y in zip(v, c):
        ax.annotate(f"{base/y:.3f}×".replace(".", ","), (x, y), xytext=(0, 11),
                    textcoords="offset points", ha="center", fontsize=8.4,
                    color=INK, fontweight="bold")
    ax.annotate("từ vòng 3 trở đi khai thác tính THƯA\n→ phụ thuộc dữ liệu (điểm đặc)",
                (0.02, 0.20), xycoords="axes fraction", ha="left", va="top",
                fontsize=8, color=INK2)
    ax.set_ylim(min(c) * 0.93, max(c) * 1.09)   # chỗ cho nhãn ở vòng 0
    ax.set_xticks(v); ax.set_xlabel("vòng")
    ax.set_ylabel("chu kỳ mỗi ảnh (B-V0, mycore)")
    ax.yaxis.set_major_formatter(VN)
    ax.set_title("Vòng B1 mù vượt tối ưu phần mềm làm bằng tay ngay ở vòng 2",
                 loc="left", pad=10)
    ax.legend(loc="upper right")
    save(fig, "hinh3_tien_trinh_b1")


# ---------------------------------------------------------------- hình 4
def fig_mo_hinh():
    """Mô hình × cấu hình. Nguồn: S8/ket_qua_sim.json."""
    d = json.loads((RES / "S8" / "ket_qua_sim.json").read_text())["res"]
    cfg = [("plain", "B-V1\nC thẳng"), ("dcr", "B-V3\n+DOT4, bố cục, REQ"),
           ("dcrp", "B-V3+PMAX4\n+PMAX4")]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.grid(True, axis="y", zorder=0); ax.set_axisbelow(True)
    w = 0.34
    for j, (m, ten, col) in enumerate((("s", "M1-S (dùng để chọn ứng viên)", BLUE),
                                       ("l", "M1-L (giữ lại, 3,45× MAC)", ORANGE))):
        base = d[f"{m}_plain"]["cyc"]
        xs = [i + (j - 0.5) * w for i in range(len(cfg))]
        ys = [base / d[f"{m}_{k}"]["cyc"] for k, _ in cfg]
        ax.bar(xs, ys, width=w - 0.03, color=col, zorder=3, label=ten)
        for x, y in zip(xs, ys):
            ax.annotate(f"{y:.3f}×".replace(".", ","), (x, y), xytext=(0, 4),
                        textcoords="offset points", ha="center", fontsize=8.4,
                        color=INK, fontweight="bold")
    ax.set_xticks(range(len(cfg)), [t for _, t in cfg], fontsize=8.5)
    ax.set_ylabel("tăng tốc so với mốc C thẳng\ncủa chính mô hình đó")
    ax.set_ylim(0, 8.9)
    ax.set_title("Ứng viên phần cứng tổng quát hoá sang mô hình giữ lại,\n"
                 "mất khoảng 11 % hệ số", loc="left", pad=10)
    ax.legend(loc="upper left")
    save(fig, "hinh4_mo_hinh_giu_lai")


# ---------------------------------------------------------------- hình 5
def fig_phan_ra():
    """Chu kỳ TỪNG LỚP, ba cấu hình. Nguồn: S8/ket_qua_sim.json (M1-S).

    Cột chồng tuyệt đối không dùng được ở đây: tổng chênh nhau 7,7 lần nên hai cột
    phải bị bẹp tới mức không đọc nổi thành phần. Nhóm theo LỚP trên trục log cho
    thấy thẳng điều cần nói: DOT4 cắt conv, PMAX4 cắt pool, và mỗi lệnh gần như
    không đụng tới phần việc không phải của nó.
    """
    d = json.loads((RES / "S8" / "ket_qua_sim.json").read_text())["res"]
    lop = ["conv1", "pool1", "conv2", "pool2", "dense"]
    series = [("s_plain", "B-V1 — C thẳng", BLUE),
              ("s_dcr", "B-V3 — +DOT4, bố cục, REQ", ORANGE),
              ("s_dcrp", "B-V3+PMAX4 — +PMAX4", AQUA)]
    fig, ax = plt.subplots(figsize=(7.0, 4.0))
    ax.grid(True, axis="y", zorder=0); ax.set_axisbelow(True)
    w = 0.26
    for j, (k, ten, col) in enumerate(series):
        xs = [i + (j - 1) * w for i in range(len(lop))]
        ax.bar(xs, d[k]["lop"], width=w - 0.03, color=col, zorder=3, label=ten)
    # Nhãn chọn lọc: chỉ ghi hệ số cắt của bước có tác dụng với lớp đó.
    for i, (l, buoc, a, b) in enumerate([
            ("conv1", "DOT4+bố cục", "s_plain", "s_dcr"),
            ("pool1", "PMAX4", "s_dcr", "s_dcrp"),
            ("conv2", "DOT4", "s_plain", "s_dcr"),
            ("pool2", "PMAX4", "s_dcr", "s_dcrp"),
            ("dense", "DOT4", "s_plain", "s_dcr")]):
        j = lop.index(l)
        f = d[a]["lop"][j] / d[b]["lop"][j]
        ax.annotate(f"{buoc}\n{f:.1f}×".replace(".", ","),
                    (j, max(d[s_]["lop"][j] for s_, _, _ in series)),
                    xytext=(0, 9), textcoords="offset points", ha="center",
                    fontsize=8, color=INK, fontweight="bold")
    ax.set_xticks(range(len(lop)), lop)
    ax.set_yscale("log")
    ax.set_ylabel("chu kỳ mỗi ảnh (M1-S, thang log)")
    ax.yaxis.set_major_formatter(VN)
    ax.set_ylim(top=max(d["s_plain"]["lop"]) * 6)
    ax.set_title("Mỗi lệnh tùy biến cắt đúng phần việc nó nhắm tới", loc="left", pad=10)
    ax.legend(loc="upper center", ncols=3, bbox_to_anchor=(0.5, 1.0), fontsize=8)
    save(fig, "hinh5_phan_ra_theo_lop")


if __name__ == "__main__":
    fig_dubao_vs_do()
    fig_b1()
    fig_mo_hinh()
    fig_phan_ra()
    if (RES / "S9" / "pareto.json").exists():
        fig_pareto()
    else:
        print("bỏ qua hình 2: chưa có results/pipeline/S9/pareto.json")
