"""cdp spec — kiểm và chuẩn hoá đặc tả thí nghiệm YAML (SPEC mục 2).

Kiểm ba lớp:
  1. cú pháp YAML
  2. lược đồ pipeline/schemas/spec.schema.json
  3. phân giải về đúng MỘT cấu hình trong targets.py (cờ + lõi + tham số RTL),
     và đối chiếu các trường `expect` với bảng kết quả đã công bố
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

import jsonschema
import yaml

from . import paths, targets
from .util import fmt_int
from .targets import Target

SCHEMA_PATH = paths.SCHEMAS / "spec.schema.json"


@dataclass
class Spec:
    path: Path
    raw: dict
    target: Target
    warnings: list[str] = field(default_factory=list)

    # ---- truy cập tiện ----
    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def flags(self) -> list[str]:
        return [f.removeprefix("-D") for f in self.raw["firmware"].get("flags", [])]

    @property
    def rtl_params(self) -> dict:
        return dict(self.raw["core"].get("rtl_params", {}))

    @property
    def images(self) -> int:
        return int(self.raw.get("evaluate", {}).get("images", 10))

    @property
    def clock_mhz(self) -> float:
        return float(self.raw.get("clock_mhz", targets.CLOCK_MHZ))

    def stage(self, name: str) -> bool:
        return bool(self.raw.get("evaluate", {}).get(name, False))

    def as_dict(self) -> dict:
        return {"path": str(self.path), "spec": self.raw,
                "target": self.target.as_dict(), "warnings": self.warnings}


def load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text())


def load(path: str | Path) -> Spec:
    p = Path(path)
    if not p.is_absolute():
        cand = [p, paths.ROOT / p, paths.SPECS / p]
        for c in cand:
            if c.exists():
                p = c
                break
    if not p.exists():
        raise FileNotFoundError(f"không thấy đặc tả {path}")
    p = p.resolve()
    raw = yaml.safe_load(p.read_text())
    if not isinstance(raw, dict):
        raise ValueError(f"{p}: đặc tả phải là một map YAML")
    jsonschema.validate(raw, load_schema())

    warn: list[str] = []

    core = raw["core"]["name"]
    tgt = targets.resolve(core, raw["firmware"].get("flags", []),
                          raw["core"].get("rtl_params", {}))

    fw_id = raw["firmware"].get("id")
    if fw_id and fw_id != tgt.fw_id:
        raise ValueError(f"{p}: firmware.id={fw_id} nhưng cờ ứng với {tgt.fw_id}")

    src = paths.ROOT / raw["firmware"]["source"]
    if not src.exists():
        raise ValueError(f"{p}: không thấy firmware.source {src}")

    tm = raw["core"].get("timing_model")
    if tm and not (paths.ROOT / tm).exists():
        warn.append(f"chưa có mô hình chu kỳ {tm} (S2 mới dựng) — bỏ qua ở S0/S1")

    clk = raw.get("clock_mhz")
    if clk is not None and float(clk) != targets.CLOCK_MHZ:
        warn.append(f"clock_mhz={clk} khác xung nhịp cố định {targets.CLOCK_MHZ} MHz "
                    "của mọi phép đo đã có")

    exp = raw.get("expect", {})
    if "target" in exp and exp["target"] != tgt.name:
        raise ValueError(f"{p}: expect.target={exp['target']} nhưng cờ+lõi+tham số "
                         f"ứng với {tgt.name}")
    if "total_cycles" in exp and int(exp["total_cycles"]) != tgt.expect_total_median:
        raise ValueError(
            f"{p}: expect.total_cycles={exp['total_cycles']} khác số đã công bố cho "
            f"{tgt.name} ({tgt.expect_total_median}) trong docs/KET_QUA_TONG_HOP.md")

    if raw.get("evaluate", {}).get("images", 10) != 10:
        warn.append("số ảnh khác 10: mọi số đã công bố là trung vị của 10 ảnh")

    return Spec(path=p, raw=raw, target=tgt, warnings=warn)


def check_many(items) -> tuple[list[Spec], list[tuple[Path, Exception]]]:
    ok, bad = [], []
    for it in items:
        try:
            ok.append(load(it))
        except Exception as exc:                            # noqa: BLE001
            bad.append((Path(it), exc))
    return ok, bad


def main(args, run) -> int:
    """cdp spec <file.yaml ...> — mặc định kiểm mọi file trong pipeline/specs/."""
    items = args.files or sorted(paths.SPECS.glob("*.yaml"))
    if not items:
        run.say("không có đặc tả nào để kiểm")
        return 1
    ok, bad = check_many(items)
    for s in ok:
        t = s.target
        run.say(f"ĐẠT  {s.path.relative_to(paths.ROOT)}")
        run.say(f"     name={s.name} · model={s.raw['model']} · lõi={t.core}")
        run.say(f"     → cấu hình {t.name} (dòng {t.row} của KET_QUA_TONG_HOP) · {t.hw}")
        run.say(f"     firmware {t.fw_id} cờ {sorted(t.fw_flags) or '(không)'} "
                f"· báo VARIANT={t.fw_variant}")
        run.say(f"     make: -C {t.fw_dir} {t.t_fw}  ·  -C {t.make_dir} {t.t_sim} / "
                f"{t.t_build} / {t.t_check}"
                + (f" {t.make_vars}" if t.make_vars else ""))
        run.say(f"     trung vị đã công bố: {fmt_int(t.expect_total_median)} chu kỳ "
                f"= {t.ms:.1f} ms @ {targets.CLOCK_MHZ:g} MHz")
        for w in s.warnings:
            run.say(f"     CẢNH BÁO: {w}")
    for p, exc in bad:
        run.say(f"KHÔNG ĐẠT  {p}")
        for ln in str(exc).splitlines():
            run.say(f"     {ln}")
    run.say("")
    run.say(f"Tổng: {len(ok)} đặc tả hợp lệ, {len(bad)} không hợp lệ")
    out = run.path("specs.json")
    out.write_text(json.dumps([s.as_dict() for s in ok], indent=2, ensure_ascii=False))
    run.finish("ok" if not bad else "fail",
               {"n_ok": len(ok), "n_bad": len(bad),
                "specs": [str(s.path.relative_to(paths.ROOT)) for s in ok],
                "targets": [s.target.name for s in ok],
                "warnings": {str(s.path.name): s.warnings for s in ok if s.warnings},
                "errors": {str(p): str(e) for p, e in bad}})
    return 0 if not bad else 1
