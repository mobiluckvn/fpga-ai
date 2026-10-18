"""cdp propose — tạo gói đầu vào cho AI + kiểm đầu ra theo schema; --rules cho bộ sinh theo luật.

CHƯA HIỆN THỰC. Dự kiến ở bước S5: sandbox mù theo SPEC 4.6, kiểm candidates.json theo pipeline/schemas/candidate.schema.json
"""
from __future__ import annotations

STEP = "S5"
WHAT = "sandbox mù theo SPEC 4.6, kiểm candidates.json theo pipeline/schemas/candidate.schema.json"


def main(args, run) -> int:
    run.say(f"cdp propose: chưa hiện thực — dự kiến ở S5")
    run.say(f"    sandbox mù theo SPEC 4.6, kiểm candidates.json theo pipeline/schemas/candidate.schema.json")
    run.finish("not_implemented", {"planned_step": STEP, "planned_work": WHAT})
    return 2
