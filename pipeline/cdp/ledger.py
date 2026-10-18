"""Sổ cái SQLite của pipeline (SPEC mục 3) + xuất CSV.

Ba bảng:
  runs          — mọi lần chạy một lệnh cdp, đủ khoá tái lập
  candidates    — ứng viên tối ưu: dự báo TRƯỚC, số đo SAU (SPEC 0.3: không sửa lùi)
  measurements  — số chu kỳ/CRC từng ảnh từng lớp, nguồn iss|verilator|kit
                  (thêm ngoài SPEC: S1/S2 cần so từng ảnh, không chỉ trung vị)
"""
from __future__ import annotations

import csv
import json
import sqlite3
import time
from pathlib import Path

from . import paths

SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id       TEXT PRIMARY KEY,
    cmd          TEXT NOT NULL,
    step         TEXT,
    spec         TEXT,
    target       TEXT,
    status       TEXT NOT NULL,
    started_at   TEXT,
    finished_at  TEXT,
    duration_s   REAL,
    git_commit   TEXT,
    git_dirty    INTEGER,
    src_hash     TEXT,
    params_json  TEXT,
    tools_json   TEXT,
    result_json  TEXT,
    run_dir      TEXT,
    note         TEXT
);

CREATE TABLE IF NOT EXISTS candidates (
    id                  TEXT PRIMARY KEY,
    round               INTEGER,
    level               TEXT,
    origin              TEXT,
    title               TEXT,
    spec_json           TEXT,
    predicted_cycles    INTEGER,
    predicted_speedup   REAL,
    predicted_cost_json TEXT,
    status              TEXT,
    measured_cycles_sim INTEGER,
    measured_cycles_kit INTEGER,
    measured_cost_json  TEXT,
    fmax_mhz            REAL,
    crc_ok              INTEGER,
    src_hash            TEXT,
    git_commit          TEXT,
    ai_model            TEXT,
    prompt_hash         TEXT,
    input_hash          TEXT,
    created_at          TEXT,
    updated_at          TEXT,
    run_id              TEXT
);

CREATE TABLE IF NOT EXISTS measurements (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id      TEXT,
    target      TEXT,
    variant     TEXT,
    source      TEXT,
    img         INTEGER,
    conv1       INTEGER,
    pool1       INTEGER,
    conv2       INTEGER,
    pool2       INTEGER,
    dense       INTEGER,
    total       INTEGER,
    instret     INTEGER,
    crc_a1      TEXT,
    crc_p1      TEXT,
    crc_a2      TEXT,
    crc_p2      TEXT,
    crc_logit   TEXT,
    pred        INTEGER,
    pred_golden INTEGER,
    crc_ok      INTEGER,
    src_hash    TEXT,
    created_at  TEXT,
    UNIQUE (run_id, target, source, img)
);

CREATE INDEX IF NOT EXISTS idx_meas_target ON measurements (target, source);
CREATE INDEX IF NOT EXISTS idx_runs_cmd    ON runs (cmd, status);
"""

TABLES = ("runs", "candidates", "measurements")
CSV_NAME = {"runs": "ledger.csv", "candidates": "candidates.csv",
            "measurements": "measurements.csv"}


def connect(path: Path | None = None) -> sqlite3.Connection:
    path = Path(path or paths.LEDGER)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(str(path))
    con.row_factory = sqlite3.Row
    con.executescript(SCHEMA)
    con.commit()
    return con


def _cols(con, table) -> list[str]:
    return [r[1] for r in con.execute(f"PRAGMA table_info({table})")]


def upsert(con, table: str, row: dict) -> None:
    """Ghi/ghi đè một dòng. Giá trị dict/list tự chuyển sang JSON."""
    cols = _cols(con, table)
    data = {}
    for k, v in row.items():
        if k not in cols:
            raise KeyError(f"bảng {table} không có cột {k}")
        data[k] = json.dumps(v, ensure_ascii=False) if isinstance(v, (dict, list)) else v
    names = ", ".join(data)
    marks = ", ".join("?" for _ in data)
    con.execute(f"INSERT OR REPLACE INTO {table} ({names}) VALUES ({marks})",
                list(data.values()))
    con.commit()


def insert_measurements(con, rows: list[dict]) -> int:
    n = 0
    for r in rows:
        r = dict(r)
        r.setdefault("created_at", time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        upsert(con, "measurements", r)
        n += 1
    return n


def export_csv(con, out_dir: Path | None = None) -> list[Path]:
    out_dir = Path(out_dir or paths.DB)
    out_dir.mkdir(parents=True, exist_ok=True)
    written = []
    for table in TABLES:
        cols = _cols(con, table)
        rows = con.execute(f"SELECT * FROM {table}").fetchall()
        p = out_dir / CSV_NAME[table]
        with open(p, "w", newline="") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for r in rows:
                w.writerow([r[c] for c in cols])
        written.append(p)
    return written


def counts(con) -> dict:
    return {t: con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0] for t in TABLES}


def upsert_candidate(con, cid: str, **fields) -> None:
    """Ghi/cập nhật một dòng `candidates`, giữ `created_at` của lần đầu."""
    row = con.execute("SELECT created_at FROM candidates WHERE id=?", (cid,)).fetchone()
    now = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    data = {"id": cid, "created_at": row["created_at"] if row else now,
            "updated_at": now}
    if row:                      # giữ nguyên các cột không được truyền vào
        cur = con.execute("SELECT * FROM candidates WHERE id=?", (cid,)).fetchone()
        for k in cur.keys():
            if k not in ("id", "created_at", "updated_at") and cur[k] is not None:
                data[k] = cur[k]
    data.update({k: v for k, v in fields.items() if v is not None})
    upsert(con, "candidates", data)
