"""Public quota fields only. Never read account credentials or session history."""
from __future__ import annotations

import math


def remaining(window: dict | None) -> float | None:
    if not isinstance(window, dict) or window.get("usedPercent") is None:
        return None
    if isinstance(window["usedPercent"], bool):
        raise ValueError("额度百分比无效")
    try:
        value = float(window["usedPercent"])
    except (ValueError, TypeError, OverflowError) as exc:
        raise ValueError("额度百分比无效") from exc
    if not math.isfinite(value):
        raise ValueError("额度百分比无效")
    return max(0.0, min(100.0, 100.0 - value))


def quota_view(payload: dict) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("Invalid quota payload")
    def mapping(value):
        return value if isinstance(value, dict) else {}
    buckets = mapping(payload.get("rateLimitsByLimitId"))
    codex = mapping(buckets.get("codex")) or mapping(payload.get("rateLimits"))
    windows = [w for w in (codex.get("primary"), codex.get("secondary"))
               if isinstance(w, dict)]
    week = next((w for w in windows if w.get("windowDurationMins") == 10080), None)
    # The legacy primary/secondary mapping is short/weekly. Never label a known
    # 5-hour window as weekly merely because the weekly window is unavailable.
    if week is None:
        week = next((w for w in reversed(windows) if not w.get("windowDurationMins")), None)
    short = next((w for w in windows if w.get("windowDurationMins") == 300), None)
    reserve = mapping(buckets.get("base_model_inference")).get("primary")
    if remaining(week) is None:
        raise ValueError("未返回周额度；请检查 Codex 登录或稍后刷新")

    def normalize(window: dict | None) -> dict | None:
        amount = remaining(window)
        if amount is None:
            return None
        reset = window.get("resetsAt")
        # Missing/malformed reset times must not become '1970' or Invalid Date.
        if (isinstance(reset, bool) or not isinstance(reset, (int, float))
                or not math.isfinite(reset) or not 0 < reset <= 253402300799):
            reset = None
        return {"remaining": amount, "resetsAt": reset}

    return {"week": normalize(week), "short": normalize(short), "reserve": normalize(reserve)}
