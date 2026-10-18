#!/usr/bin/env python3
"""Huấn luyện M1-S trên MNIST (PyTorch), lưu trọng số float.

Kiến trúc M1-S đúng như docs (kế hoạch thí nghiệm), đầu vào 28x28x1:

    Conv 3x3, 1 -> 8 kênh,  ReLU   -> 26x26x8    80 tham số    48.672 MAC
    MaxPool 2x2                    -> 13x13x8     0                 0
    Conv 3x3, 8 -> 16 kênh, ReLU   -> 11x11x16 1.168 tham số  139.392 MAC
    MaxPool 2x2                    ->  5x5x16     0                 0
    Dense 400 -> 10                -> 10       4.010 tham số    4.000 MAC
                                      tổng     5.258           192.064

Không có padding ("valid"), MaxPool lấy sàn (11 -> 5).
Lưu: model/m1s_float.npz (w1,b1,w2,b2,w3,b3) + in độ chính xác float trên 10.000 ảnh test.
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

import mnist

HERE = Path(__file__).resolve().parent


class M1S(nn.Module):
    """Cùng một kiến trúc, số kênh tham số hoá.

    Mặc định (8, 16) là M1-S đúng như kế hoạch. Mô hình giữ lại M1-L dùng (16, 32)
    — gấp đôi kênh — và chạy qua ĐÚNG script này, ĐÚNG script lượng tử hoá, ĐÚNG
    golden của M1-S. Không có nhánh mã riêng cho mô hình giữ lại, nên nó thật sự
    "giữ lại": không gì trong đường đo được chỉnh theo nó.
    """

    def __init__(self, c1=8, c2=16, ncls=10):
        super().__init__()
        self.c1 = nn.Conv2d(1, c1, 3, bias=True)     # 28 -> 26
        self.c2 = nn.Conv2d(c1, c2, 3, bias=True)    # 13 -> 11
        self.fc = nn.Linear(5 * 5 * c2, ncls, bias=True)

    def forward(self, x):
        x = F.relu(self.c1(x))
        x = F.max_pool2d(x, 2)                      # 26 -> 13
        x = F.relu(self.c2(x))
        x = F.max_pool2d(x, 2)                      # 11 -> 5
        x = x.flatten(1)                            # 5*5*C2
        return self.fc(x)


def to_tensor(x_u8: np.ndarray) -> torch.Tensor:
    """uint8 [N,28,28] -> float [N,1,28,28] trong [0,1]."""
    return torch.from_numpy(x_u8.astype(np.float32) / 255.0).unsqueeze(1)


@torch.no_grad()
def accuracy(net, x, y, bs=512) -> float:
    net.eval()
    ok = 0
    for i in range(0, len(x), bs):
        logit = net(x[i:i + bs])
        ok += (logit.argmax(1) == y[i:i + bs]).sum().item()
    return ok / len(x)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--epochs", type=int, default=8)
    ap.add_argument("--batch", type=int, default=128)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=1234)
    ap.add_argument("--out", default=str(HERE / "m1s_float.npz"))
    ap.add_argument("--c1", type=int, default=8, help="số kênh conv1 (M1-S: 8, M1-L: 16)")
    ap.add_argument("--c2", type=int, default=16, help="số kênh conv2 (M1-S: 16, M1-L: 32)")
    ap.add_argument("--name", default=None, help="tên mô hình để in ra (mặc định suy từ kênh)")
    args = ap.parse_args()

    torch.manual_seed(args.seed)
    np.random.seed(args.seed)

    tx, ty, ex, ey = mnist.load()
    xtr = to_tensor(tx)
    ytr = torch.from_numpy(ty.astype(np.int64))
    xte = to_tensor(ex)
    yte = torch.from_numpy(ey.astype(np.int64))

    net = M1S(args.c1, args.c2)
    nparam = sum(p.numel() for p in net.parameters())
    name = args.name or ("M1-S" if (args.c1, args.c2) == (8, 16) else
                         f"M1-?({args.c1}/{args.c2})")
    print(f"# Huấn luyện {name}  (conv1 1->{args.c1}, conv2 {args.c1}->{args.c2})")
    print(f"tham số    : {nparam}" + (" (kế hoạch: 5.258)" if name == "M1-S" else ""))
    print(f"train/test : {len(xtr)} / {len(xte)}")
    print(f"epochs={args.epochs} batch={args.batch} lr={args.lr} seed={args.seed}")

    opt = torch.optim.Adam(net.parameters(), lr=args.lr)
    n = len(xtr)
    t0 = time.time()
    for ep in range(1, args.epochs + 1):
        net.train()
        perm = torch.randperm(n)
        tot = 0.0
        for i in range(0, n, args.batch):
            idx = perm[i:i + args.batch]
            opt.zero_grad()
            loss = F.cross_entropy(net(xtr[idx]), ytr[idx])
            loss.backward()
            opt.step()
            tot += loss.item() * len(idx)
        acc = accuracy(net, xte, yte)
        print(f"epoch {ep}/{args.epochs}  loss {tot/n:.4f}  test acc {acc*100:.2f}%"
              f"  ({time.time()-t0:.0f}s)")

    acc = accuracy(net, xte, yte)
    sd = net.state_dict()
    np.savez(args.out,
             w1=sd["c1.weight"].numpy(), b1=sd["c1.bias"].numpy(),
             w2=sd["c2.weight"].numpy(), b2=sd["c2.bias"].numpy(),
             w3=sd["fc.weight"].numpy(), b3=sd["fc.bias"].numpy(),
             float_acc=np.float64(acc))
    print(f"\nĐộ chính xác float (10.000 ảnh test): {acc*100:.2f}%")
    print(f"Đã lưu {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
