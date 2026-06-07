import pandas as pd
import re
import numpy as np

def clean_mktcap(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.copy()
    df.columns = df.iloc[1]
    df = df.iloc[4:].set_index("參考標題")

    # 確保 index 是年月
    df.index = pd.to_datetime(df.index.astype(str), format="%Y%m", errors="coerce")
    df = df[~df.index.isna()]   # 去掉非年月列

    # 正則：只抓股票代號
    new_cols = {}
    for c in df.columns:
        m = re.match(r"(\d+)", str(c))
        if m:
            new_cols[c] = m.group(1)
        else:
            new_cols[c] = None  # 非股票欄位丟掉

    df = df.rename(columns=new_cols)
    df = df.loc[:, df.columns.notna()]  # 只保留股票欄位

    # 數值轉 float
    df = df.apply(pd.to_numeric, errors="coerce")

    # 轉 PeriodIndex，只保留年+月
    df.index = df.index.to_period("M")

    # 設定 index name, columns name
    df.index.name = "month"
    df.columns.name = "ticker"

    return df


# 用法



def clean_price(df):
    df.columns = df.iloc[1]
    df = df.iloc[4:].set_index("參考標題")
    # 確保 index 轉成日期
    df.index = pd.to_datetime(df.index, errors="coerce")
    df = df[~df.index.isna()]  # 去掉不是日期的列

    # 正則：擷取前面的數字代號
    new_cols = {}
    for c in df.columns:
        m = re.match(r"(\d+)", str(c))  # 只抓前面的數字
        if m:
            new_cols[c] = m.group(1)    # 股票代號
        else:
            new_cols[c] = None          # 不是股票欄就丟掉

    # 換名稱
    df = df.rename(columns=new_cols)

    # 只保留真正股票代號的欄位（丟掉 None 或空值）
    df = df.loc[:, df.columns.notna()]

    # 去掉完全空的股票
    df = df.dropna(axis=1, how="all")

    # （可選）轉數值，保證是 float
    df = df.apply(pd.to_numeric, errors="coerce")

    # 現在 df：index=日期, columns=股票代號


    df.index.name  = "date"
    df.columns.name="tickers"

    return df



