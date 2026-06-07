from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
RET_DIR = APP_ROOT / "data" / "returns"
OUT_DIR = APP_ROOT / "data" / "global_wave"
OUT_DIR.mkdir(parents=True, exist_ok=True)

WAVE_XLSX = APP_ROOT / "global_wave.xlsx"  # 你專案根目錄那份


def read_factor_returns(fp: Path) -> pd.Series:
    """讀 data/returns/*.json → 日報酬 Series(date -> ret)"""
    obj = json.loads(fp.read_text(encoding="utf-8"))
    dates = pd.to_datetime(obj["dates"])
    ret = pd.to_numeric(pd.Series(obj["ret"]), errors="coerce")
    s = pd.Series(ret.values, index=dates).sort_index()
    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    s.name = fp.stem
    return s


def forward_window_return(daily_ret: pd.Series, anchor: pd.Timestamp, months: int) -> float | None:
    """
    從 anchor 之後開始算 (下一個交易日到 anchor+months) 的累積報酬
    cum = prod(1+r)-1
    """
    if daily_ret.empty:
        return None

    anchor = pd.to_datetime(anchor)
    end = anchor + pd.DateOffset(months=months)

    # 使用 (anchor, end]，避免把事件當天也算進去（通常事件當天是轉折點）
    win = daily_ret[(daily_ret.index > anchor) & (daily_ret.index <= end)]
    if win.empty:
        return None

    return float((1.0 + win).prod() - 1.0)


def build_factor_global_wave(factor_name: str, daily_ret: pd.Series, wave_df: pd.DataFrame) -> Dict:
    """
    wave_df 需有欄位: 'Trough Dates', 'Peak Dates'
    """
    events: List[Dict] = []

    def add_events(col: str, event_type: str):
        nonlocal events
        for d in wave_df[col].dropna().tolist():
            t = pd.to_datetime(d)
            r6 = forward_window_return(daily_ret, t, 6)
            r12 = forward_window_return(daily_ret, t, 12)
            events.append(
                {
                    "type": event_type,
                    "date": t.strftime("%Y-%m-%d"),
                    "r_6m": r6,
                    "r_12m": r12,
                }
            )

    add_events("Trough Dates", "trough")
    add_events("Peak Dates", "peak")

    # summary
    def summarize(event_type: str) -> Dict:
        rows = [e for e in events if e["type"] == event_type]
        r6 = [e["r_6m"] for e in rows if e["r_6m"] is not None]
        r12 = [e["r_12m"] for e in rows if e["r_12m"] is not None]
        return {
            "n_events": len(rows),
            "n_6m": len(r6),
            "n_12m": len(r12),
            "avg_6m": float(np.mean(r6)) if r6 else None,
            "avg_12m": float(np.mean(r12)) if r12 else None,
        }

    payload = {
        "factor": factor_name,
        "summary": {
            "trough": summarize("trough"),
            "peak": summarize("peak"),
        },
        "events": events,  # 給你之後想畫點圖/箱型圖用
    }
    return payload


def main():
    if not WAVE_XLSX.exists():
        raise FileNotFoundError(f"找不到 {WAVE_XLSX}，請確認 global_wave.xlsx 在專案根目錄")

    wave = pd.read_excel(WAVE_XLSX)
    need_cols = {"Trough Dates", "Peak Dates"}
    if not need_cols.issubset(set(wave.columns)):
        raise RuntimeError(f"global_wave.xlsx 欄位需包含 {need_cols}，目前是：{wave.columns.tolist()}")

    files = sorted(RET_DIR.glob("*.json"))
    if not files:
        raise RuntimeError(f"找不到任何因子 returns 檔：{RET_DIR}")

    wrote = 0
    for fp in files:
        factor = fp.stem
        s = read_factor_returns(fp)
        payload = build_factor_global_wave(factor, s, wave)

        out_fp = OUT_DIR / f"{factor}.json"
        out_fp.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
        wrote += 1

    print(f"[OK] Wrote global wave files: {wrote} factors -> {OUT_DIR}")


if __name__ == "__main__":
    main()
