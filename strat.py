import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# ============================================================================
# Block 0 - 資料匯入 + 因子建立基礎設施（整份報告共用）
# ============================================================================

import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

# ----------------------------------------------------------------------------
# 1. 資料匯入
# ----------------------------------------------------------------------------
DATA_DIR = "merged_csvs/"

price  = pd.read_csv(f"{DATA_DIR}price.csv",     index_col=0, parse_dates=True)
mktcap   = pd.read_csv(f"{DATA_DIR}mktcap.csv",    index_col=0, parse_dates=True)

pb_raw   = pd.read_csv(f"{DATA_DIR}pb_ratio.csv",  index_col=0, parse_dates=True)
eps_raw  = pd.read_csv(f"{DATA_DIR}eps.csv",       index_col=0, parse_dates=True)

returns = price.pct_change(fill_method=None)
print(f"價格資料範圍: {price.index.min().date()} ~ {price.index.max().date()}")
print(f"股票檔數: {price.shape[1]}")

# ----------------------------------------------------------------------------
# 2. 建立 Top300 底池
# ----------------------------------------------------------------------------
cap_rank = mktcap.rank(axis=1, ascending=False, method='first')
universe = (cap_rank <= 300)
print(f"Universe: Top300 by 市值, 月頻 mask")

# ----------------------------------------------------------------------------
# 3. 通用工具：在 Universe 內計算百分位 rank
# ----------------------------------------------------------------------------
def pct_rank_in_universe(score, universe_mask=universe, lower_better=False):
    """
    在 universe 內的股票算百分位（0 = 最好, 1 = 最差）
    lower_better=True → 數值越低越好（如 PE）
    """
    universe_aligned = universe_mask.reindex(score.index, method='ffill') \
                                    .reindex(columns=score.columns)
    masked = score.where(universe_aligned, np.nan)
    return masked.rank(axis=1, ascending=lower_better, pct=True)

# ----------------------------------------------------------------------------
# 4. 通用工具：月報酬計算（幾何累積）
# ----------------------------------------------------------------------------
monthly_ret = (1 + returns).resample('MS').prod() - 1

# ----------------------------------------------------------------------------
# 5. 通用回測引擎（每月再平衡 + 等權）
# ----------------------------------------------------------------------------
def backtest(factor_pct_dict, pct_thresholds, universe_mask=universe,
             returns=returns, start_date='2005-01-01', end_date=None):
    
    filters = [universe_mask.astype(int)]
    
    for name, pct_df in factor_pct_dict.items():
        thr = pct_thresholds[name]
        filters.append((pct_df <= thr).astype(int))
    
    combined = sum(filters)

    # 原始選股訊號
    selected = (combined == len(filters)).astype(int)

    # shift(1) 後，才是真正「當月持股」
    selected_monthly = selected.shift(1).fillna(0).astype(int)

    # 限制回測期間
    selected_monthly_period = selected_monthly.loc[start_date:end_date]

    # 轉成 daily holding
    selected_daily = selected_monthly.reindex(returns.index, method='ffill')
    selected_daily = selected_daily.loc[start_date:end_date]

    n_holdings = selected_daily.sum(axis=1)

    daily_ret = (returns * selected_daily).sum(axis=1) / n_holdings.replace(0, np.nan)
    daily_ret = daily_ret.fillna(0).loc[start_date:end_date]

    ann_ret = (1 + daily_ret).prod() ** (252 / len(daily_ret)) - 1
    ann_vol = daily_ret.std() * np.sqrt(252)
    sharpe = ann_ret / ann_vol if ann_vol > 0 else np.nan

    cum = (1 + daily_ret).cumprod()
    max_dd = ((cum - cum.cummax()) / cum.cummax()).min()

    holdings_daily = n_holdings.loc[start_date:end_date]
    yearly_ret = (1 + daily_ret).groupby(daily_ret.index.year).prod() - 1

    # 每月持股數
    monthly_n_holdings = selected_monthly_period.sum(axis=1)

    # 轉成長表格：每列是一個「月份 × 股票」
    holdings_long = (
        selected_monthly_period
        .stack()
        .reset_index()
    )

    holdings_long.columns = ['date', 'stock', 'holding']

    holdings_long = holdings_long[holdings_long['holding'] == 1].copy()
    holdings_long = holdings_long.drop(columns='holding')

    return {
        'ann_return': ann_ret,
        'ann_volatility': ann_vol,
        'sharpe': sharpe,
        'max_drawdown': max_dd,
        'avg_holdings': holdings_daily.mean(),
        'p5_holdings': holdings_daily[holdings_daily > 0].quantile(0.05) if (holdings_daily > 0).any() else 0,
        'zero_month_ratio': (holdings_daily == 0).mean(),
        'positive_year_ratio': (yearly_ret > 0).mean(),
        'worst_year': yearly_ret.min(),
        'best_year': yearly_ret.max(),
        'daily_ret': daily_ret,
        'yearly_ret': yearly_ret,

        # 新增回傳
        'selected_monthly': selected_monthly_period,
        'monthly_n_holdings': monthly_n_holdings,
        'holdings_long': holdings_long,
    }


print("\nBlock 0 完成。基礎設施已就緒。")
print("可用變數：price, returns, mktcap, pe_raw, pb_raw, eps_raw, yoy_raw,")
print("          beta_raw, yld_raw, universe, monthly_ret, cap_rank")
print("可用函數：pct_rank_in_universe(), backtest()")



# ============================================================================
# Block 1: 建立 10 個因子的百分位 (factor_pcts)
# ============================================================================

# --- 動能類 ---
mom01_score = monthly_ret.rolling(window=1).apply(lambda x: np.prod(1+x)-1, raw=True)
mom03_score = monthly_ret.rolling(window=3).apply(lambda x: np.prod(1+x)-1, raw=True)
mom06_score = monthly_ret.rolling(window=6).apply(lambda x: np.prod(1+x)-1, raw=True)
mom12_score = monthly_ret.rolling(window=12).apply(lambda x: np.prod(1+x)-1, raw=True)

# --- EPS_growth (SUE: ΔEPS / 上月底股價) ---
month_end_price = price.resample('M').last()
month_end_price.index = month_end_price.index + pd.offsets.MonthBegin(0) - pd.offsets.MonthBegin(1)
month_end_price = month_end_price.reindex(eps_raw.index, method='nearest')

eps_diff = eps_raw.diff()
eps_score = eps_diff / month_end_price.shift(1)
eps_score = eps_score.where(eps_raw > 0, np.nan)
eps_score = eps_score.where(eps_diff > 0, np.nan)


pb_clean = pb_raw.where((pb_raw > 0) & (pb_raw <= 30), np.nan)

# --- 全部轉百分位（這就是 factor_pcts）---
factor_pcts = {
    'Mom01':       pct_rank_in_universe(mom01_score, lower_better=False),
    'Mom03':       pct_rank_in_universe(mom03_score, lower_better=False),
    'Mom06':       pct_rank_in_universe(mom06_score, lower_better=False),
    'Mom12':       pct_rank_in_universe(mom12_score, lower_better=False),
    'EPS_growth':  pct_rank_in_universe(eps_score,   lower_better=False),

    'Low_PB':      pct_rank_in_universe(pb_clean,    lower_better=True),
}

# 健檢
print("初始化完成")
print(f"資料範圍: {price.index.min().date()} ~ {price.index.max().date()}")
print(f"因子數量: {len(factor_pcts)} 個")
for name in factor_pcts:
    print(f"  {name}")



factor_pcts["mom_com"] = (  factor_pcts["Mom03"] + factor_pcts["Mom06"]) / 2



r = backtest(
    {
        'EPS': factor_pcts['EPS_growth'],
        'MOM': factor_pcts["mom_com"],
        
        "low_PB": factor_pcts['Low_PB'] 
    },
    
    {
        'EPS':0.2,
        'MOM': 0.3
        ,
        "low_PB": 0.75
    }
)



return_df = r["daily_ret"]

import json
import os
import pandas as pd

# return_df 是一個 Series，index 是 date，values 是 return
s = return_df.copy()

s.index = pd.to_datetime(s.index)

result = {
    "name": "StarSearch",
    "dates": s.index.strftime("%Y-%m-%d").tolist(),
    "ret": s.astype(float).tolist()
}

output_path = "strategy_data/returns/StarSearch.json"
os.makedirs(os.path.dirname(output_path), exist_ok=True)

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("完成:", output_path)



df = (r["holdings_long"])



# df 欄位：date, stock
df["date"] = pd.to_datetime(df["date"])
df["month"] = df["date"].dt.strftime("%Y-%m")
df["stock"] = df["stock"].astype(str)

holdings = (
    df.groupby("month")["stock"]
      .apply(list)
      .to_dict()
)

result = {
    "factor": "StarSearch",
    "asof": "2026-05-25",
    "months": sorted(holdings.keys()),
    "holdings": holdings
}

with open("strategy_data/holdings/StarSearch.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)