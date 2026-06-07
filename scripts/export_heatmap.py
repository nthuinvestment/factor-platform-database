from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


APP_ROOT = Path(__file__).resolve().parents[1]
RET_DIR = APP_ROOT / "data" / "returns"
OUT_DIR = APP_ROOT / "data" / "heatmap"
OUT_DIR.mkdir(parents=True, exist_ok=True)

OUT_FP = OUT_DIR / "heatmap_12m.json"


def read_factor_returns(fp: Path) -> pd.Series:
    """讀 data/returns/*.json → 日報酬 Series(date -> ret)"""
    obj = json.loads(fp.read_text(encoding="utf-8"))
    dates = pd.to_datetime(obj["dates"])
    ret = pd.to_numeric(pd.Series(obj["ret"]), errors="coerce")
    s = pd.Series(ret.values, index=dates).sort_index()
    s = s.replace([np.inf, -np.inf], np.nan).dropna()
    return s


def daily_to_monthly_return(s: pd.Series) -> pd.Series:
    """月報酬 = 當月(1+r)連乘 - 1；用 MonthEnd 對齊"""
    m = (1 + s).resample("ME").prod() - 1  # ✅ 修 warning: M -> ME
    m.index = m.index.to_period("M")
    return m


def main():
    files = sorted(RET_DIR.glob("*.json"))
    if not files:
        raise RuntimeError(f"找不到任何因子檔：{RET_DIR}")

    # 1) 讀所有因子 → 月報酬（index=Period(M), columns=factors）
    monthly = {}
    for fp in files:
        name = fp.stem
        s = read_factor_returns(fp)
        monthly[name] = daily_to_monthly_return(s)

    df_m = pd.DataFrame(monthly).sort_index()  # rows=month, cols=factors

    # 2) 取近 12 個月（以資料最後一個月為準）
    last_m = df_m.index.max()
    months = pd.period_range(last_m - 11, last_m, freq="M")
    df_12 = df_m.reindex(months)

    # ---- (A) 保留「傳統 heatmap」需要的資料：factors + matrix ----
    factors = sorted(df_12.columns.tolist())
    mat = df_12[factors].T  # shape: factors x months

    # ---- (B) 產出「每月排名」：ranked_factors / ranked_returns ----
    # 目標 shape:
    # ranked_factors: 12 x N（每個月份一列，由高到低因子名）
    # ranked_returns: 12 x N（同排序的月報酬）
    ranked_factors = []
    ranked_returns = []

    for m in months:
        row = df_12.loc[m]  # Series: factor -> return
        # 排序規則：NaN 放最後；其餘由大到小
        row_sorted = row.sort_values(ascending=False, na_position="last")
        ranked_factors.append(row_sorted.index.tolist())
        # 注意：NaN 轉成 None（JSON 乾淨；前端可判斷）
        ranked_returns.append(
            [None if pd.isna(v) else float(v) for v in row_sorted.values]
        )

    payload = {
        # 你前端要的（每月一欄、由高到低）
        "months": [str(p) for p in months],                 # 12 個月份（字串）
        "ranked_factors": ranked_factors,                   # 12 x N
        "ranked_returns": ranked_returns,                   # 12 x N

        # 我建議保留：一般 heatmap 也能用
        "factors": factors,                                 # 排序後的固定因子列表
        "matrix": mat.to_numpy(dtype=float).tolist(),       # factors x months

        "updated_at": datetime.now(timezone(timedelta(hours=8))).isoformat(),
    }

    OUT_FP.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    print(f"[OK] Wrote heatmap file: {OUT_FP}")
    print(f"     factors={len(factors)}, months=12")
    print("     ranked_factors shape: 12 x", len(ranked_factors[0]) if ranked_factors else 0)


if __name__ == "__main__":
    main()
