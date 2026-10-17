#!/usr/bin/env python3
"""Nạp MNIST từ bốn file idx.gz trong model/data/ (không cần torchvision)."""
from __future__ import annotations

import gzip
import struct
from pathlib import Path

import numpy as np

DATA = Path(__file__).resolve().parent / "data"

FILES = {
    "train_x": "train-images-idx3-ubyte.gz",
    "train_y": "train-labels-idx1-ubyte.gz",
    "test_x": "t10k-images-idx3-ubyte.gz",
    "test_y": "t10k-labels-idx1-ubyte.gz",
}


def _read_idx(path: Path) -> np.ndarray:
    with gzip.open(path, "rb") as f:
        magic, = struct.unpack(">I", f.read(4))
        ndim = magic & 0xFF
        dims = struct.unpack(">" + "I" * ndim, f.read(4 * ndim))
        buf = f.read()
    return np.frombuffer(buf, dtype=np.uint8).reshape(dims)


def load():
    """Trả về (train_x, train_y, test_x, test_y); ảnh uint8 [N,28,28], nhãn uint8 [N]."""
    out = {}
    for k, name in FILES.items():
        p = DATA / name
        if not p.exists():
            raise SystemExit(f"Thiếu {p}. Tải bằng:\n"
                             f"  curl -LO https://storage.googleapis.com/cvdf-datasets/mnist/{name}")
        out[k] = _read_idx(p)
    return out["train_x"], out["train_y"], out["test_x"], out["test_y"]


if __name__ == "__main__":
    tx, ty, ex, ey = load()
    print(f"train {tx.shape} {ty.shape}   test {ex.shape} {ey.shape}")
    print(f"pixel min/max {tx.min()}/{tx.max()}   nhãn {sorted(set(ty.tolist()))}")
