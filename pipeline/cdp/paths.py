"""Đường dẫn cố định của dự án. Gói nằm ở <ROOT>/pipeline/cdp/."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PIPELINE = ROOT / "pipeline"
CDP      = PIPELINE / "cdp"
RUNS     = PIPELINE / "runs"
DB       = PIPELINE / "db"
SPECS    = PIPELINE / "specs"
SCHEMAS  = PIPELINE / "schemas"
CATALOG  = PIPELINE / "catalog"
PROMPTS  = PIPELINE / "prompts"

LEDGER   = DB / "ledger.sqlite"
KIT_LOCK = RUNS / "kit.lock"

RESULTS      = ROOT / "results"
RESULTS_PIPE = RESULTS / "pipeline"

M1S      = ROOT / "experiment" / "m1s"
MYCORE   = ROOT / "rtl" / "mycore"
SCRIPTS  = ROOT / "scripts"
FW       = ROOT / "fw"
DOCS     = ROOT / "docs"
ENV_SH   = ROOT / "env" / "setup_env.sh"

VENV_PY  = ROOT / ".venv" / "bin" / "python"

# Hai file CSV số đo đã có của giai đoạn trước (chỉ ĐỌC, không bao giờ ghi).
CSV_A = RESULTS / "experiment" / "m1s" / "m1s.csv"
CSV_B = RESULTS / "branch_b" / "m1s_b.csv"
