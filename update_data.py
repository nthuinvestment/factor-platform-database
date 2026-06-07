import pandas as pd
import numpy as np

import re

import importlib
import clean_data


import pandas as pd
import re

def clean_price(df):
    """
    清理每日收盤價表：
    - 從第一欄提取 YYYYMMDD
    - 設為 index
    - 只留下股票代號欄位
    """
    df = df.copy()
    
    # 第一欄名稱（應該是 '股票代號'）
    first_col = df.columns[0]
    
    # 從文字中抽出 YYYYMMDD
    df["date"] = df[first_col].astype(str).str.extract(r"(\d{8})", expand=False)
    df = df.dropna(subset=["date"])

    # 設為索引
    df = df.set_index("date")
    df.index.name = "date"
    
    # 股票代號欄位（4~6位數字）
    code_cols = [c for c in df.columns if re.fullmatch(r"\d{4,6}", str(c))]
    df = df[code_cols].apply(pd.to_numeric, errors="coerce")

    return df


def clean_code_table_ready(df):
    """
    清洗表格：
      - index 轉成 YYYYMM（2025Q1 -> 202501）
      - columns 為股票代號（1101, 1102, ...）
    """
    df = df.copy()
    
    # 1️⃣ 找出股票代號欄
    code_cols = [c for c in df.columns if re.fullmatch(r"\d{4,6}", str(c))]
    if not code_cols:
        raise ValueError("找不到股票代號欄（4~6位數）。")

    first_col = df.columns[0]

    # 2️⃣ 抽取期別並轉換 Q1→01、Q2→02、Q3→03、Q4→04
    def extract_period(s):
        s = str(s)
        m = re.search(r"(\d{4})Q([1-4])", s)
        if m:
            year, q = m.group(1), m.group(2)
            return f"{year}0{q}"  # 2025Q1 → 202501
        m = re.search(r"(\d{6})", s)  # 月資料
        if m:
            return m.group(1)
        return None

    df["period"] = df[first_col].map(extract_period)
    df = df.dropna(subset=["period"])

    # 3️⃣ 數值化
    df[code_cols] = df[code_cols].apply(pd.to_numeric, errors="coerce")

    # 4️⃣ 以 period 聚合
    out = df.groupby("period", as_index=True)[code_cols].mean().sort_index()
    out.index.name = "period"
    out.columns = [str(c) for c in out.columns]
    return out


def clean_eps(df):
    """
    清洗EPS格式資料：
    - 保留所有期別 (202508、202509、202510...)
    - index 為年月
    - 欄位為股票代號
    """
    df = df.copy()

    # ✅ 不要用第一列當欄名，直接保留所有資料
    # 改成用第 0 欄當 period 來源
    first_col = df.columns[0]
    
    # 取出年月
    df["period"] = df[first_col].astype(str).str.extract(r"(\d{6})", expand=False)
    df = df.dropna(subset=["period"])

    # 設 index
    df = df.set_index("period")
    df.index.name = "period"

    # 股票代號欄位：4~6 位數字
    code_cols = [c for c in df.columns if re.fullmatch(r"\d{4,6}", str(c))]
    df = df[code_cols].apply(pd.to_numeric, errors="coerce")

    return df
import re
import pandas as pd

def to_ym_by_code(df):
    """
    df 形狀同你截圖：
      第一欄標題為 '股票代號'，
      其餘欄為 1101、1102...，
      列標示如 '20250829本益比'。
    回傳：index=YYYYMM, columns=股票代碼
    """
    df = df.copy()
    df = df.iloc[:,4:].drop(index=0,axis=0)

    # 1) 抓第一欄（日期+指標字串），萃取 YYYYMM
    first_col = df.columns[0]              # '股票代號'
    ym = df[first_col].astype(str).str.extract(r'(\d{6})', expand=False)
    mask = ym.notna()
    ym = ym[mask].astype(int)

    # 2) 只保留 4~6 位數的股票代碼欄
    code_cols = [c for c in df.columns if re.fullmatch(r'\d{4,6}', str(c))]
    if not code_cols:
        raise ValueError("找不到股票代碼欄（4~6位數）。")

    # 3) 取出數值並轉型
    values = df.loc[mask, code_cols].apply(pd.to_numeric, errors='coerce')

    # 4) 設年月為索引；若同月重複，取平均
    values.index = ym.values
    out = values.groupby(values.index).mean().sort_index()
    out.index.name = "period"
    # 欄名統一成字串（可要可不要）
    out.columns = [str(c) for c in out.columns]
    return out

# 使用：
# res = to_ym_by_code(df)
# res.head()
# res.to_csv("cleaned.csv", encoding="utf-8-sig")
# res.to_excel("cleaned.xlsx")

price = pd.read_csv("merged_csvs/price.csv",parse_dates=["date"],index_col="date")

import pandas as pd

# 設定資料夾路徑前綴，方便修改
path = "merged_csvs/"

# 開始依序匯入所有 CSV 檔案
beta      = pd.read_csv(f"{path}beta.csv",      parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
earn_yoy  = pd.read_csv(f"{path}earn_yoy.csv",  parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
eps       = pd.read_csv(f"{path}eps.csv",       parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
gross     = pd.read_csv(f"{path}gross.csv",     parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
mktcap    = pd.read_csv(f"{path}mktcap.csv",    parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
pb_ratio  = pd.read_csv(f"{path}pb_ratio.csv",  parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
pe_ratio  = pd.read_csv(f"{path}pe_ratio.csv",  parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")

rev       = pd.read_csv(f"{path}rev.csv",       parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")
yd        = pd.read_csv(f"{path}yd.csv",        parse_dates=["Unnamed: 0"], index_col="Unnamed: 0")

print("所有因子資料已匯入完成！")



import pandas as pd

# === 因子資料 ===
pe_df      = pd.read_excel("更新因子.xlsx", sheet_name="本益比", dtype=object)
pb_df      = pd.read_excel("更新因子.xlsx", sheet_name="pb", dtype=object)
yields_df  = pd.read_excel("更新因子.xlsx", sheet_name="殖利率", dtype=object)
beta_df    = pd.read_excel("更新因子.xlsx", sheet_name="Beta", dtype=object)
mv_df      = pd.read_excel("更新因子.xlsx", sheet_name="市值_", dtype=object)



pe_new     = to_ym_by_code(pe_df)
pb_new     = to_ym_by_code(pb_df)
beta_new   = to_ym_by_code(beta_df)
mv_new     = to_ym_by_code(mv_df)
yields_new = to_ym_by_code(yields_df)


# === 收盤價 ===
price_df = pd.read_excel("更新因子.xlsx", sheet_name="收盤價", dtype=object)
cleaned_price_new = clean_price(price_df.iloc[:, 4:].drop(index=0, axis=0))

# === EPS ===
eps_df = pd.read_excel("更新因子.xlsx", sheet_name="預估eps", dtype=object)
cleaned_eps_new = clean_eps(eps_df.iloc[:, 4:].drop(index=0, axis=0))

# === 毛利率與營業利益率 ===
gross_df = pd.read_excel("更新因子.xlsx", sheet_name="毛利率", dtype=object)
rev_df   = pd.read_excel("更新因子.xlsx", sheet_name="營業利益率", dtype=object)

gross_new = clean_code_table_ready(gross_df.iloc[:, 4:].drop(index=0, axis=0))
rev_new   = clean_code_table_ready(rev_df.iloc[:, 4:].drop(index=0, axis=0))

# === 月營收 ===
rev_month_df = pd.read_excel("更新因子.xlsx", sheet_name="月營收", dtype=object)
rev_month_new = clean_eps(rev_month_df.iloc[:, 4:].drop(index=0, axis=0))


# === 月資料：轉成 YYYY-MM ===
pe_new.index = pe_new.index.astype(str).str.strip().str[:4] + "-" + pe_new.index.astype(str).str.strip().str[4:6]
pb_new.index = pb_new.index.astype(str).str.strip().str[:4] + "-" + pb_new.index.astype(str).str.strip().str[4:6]
yields_new.index = yields_new.index.astype(str).str.strip().str[:4] + "-" + yields_new.index.astype(str).str.strip().str[4:6]
beta_new.index = beta_new.index.astype(str).str.strip().str[:4] + "-" + beta_new.index.astype(str).str.strip().str[4:6]
mv_new.index = mv_new.index.astype(str).str.strip().str[:4] + "-" + mv_new.index.astype(str).str.strip().str[4:6]

cleaned_eps_new.index = cleaned_eps_new.index.astype(str).str.strip().str[:4] + "-" + cleaned_eps_new.index.astype(str).str.strip().str[4:6]
gross_new.index = gross_new.index.astype(str).str.strip().str[:4] + "-" + gross_new.index.astype(str).str.strip().str[4:6]
rev_new.index = rev_new.index.astype(str).str.strip().str[:4] + "-" + rev_new.index.astype(str).str.strip().str[4:6]
rev_month_new.index = rev_month_new.index.astype(str).str.strip().str[:4] + "-" + rev_month_new.index.astype(str).str.strip().str[4:6]

# === 日資料：保留原日期格式 ===
cleaned_price_new.index = pd.to_datetime(cleaned_price_new.index.astype(str).str.strip(), errors="coerce")











print("✔ 月資料已轉為 YYYY-MM；cleaned_price_new 保留日期格式")




# 1. 本益比 (pe)
pe_final = pe_new.combine_first(pe_ratio).sort_index()

# 2. 股價淨值比 (pb)
pb_final = pb_new.combine_first(pb_ratio).sort_index()

# 3. 殖利率 (yd)
yd_final = yields_new.combine_first(yd).sort_index()

# 4. Beta
beta_final = beta_new.combine_first(beta).sort_index()

# 5. 市值 (mktcap)
mktcap_final = mv_new.combine_first(mktcap).sort_index()

# 6. 每股盈餘 (eps)
eps_final = cleaned_eps_new.combine_first(eps).sort_index()

# 7. 毛利率 (gross)
gross_final = gross_new.combine_first(gross).sort_index()

# 8. 營業利益率 (rev)
rev_final = rev_new.combine_first(rev).sort_index()

earn_yoy_final = rev_month_new.combine_first(earn_yoy).sort_index()

# 9. 收盤價 (price)
price_final = cleaned_price_new.combine_first(price).sort_index()

print("✔ 合併完成：已保留歷史資料，並用新資料更新重疊部分。")

# 建立一個映射表：{ "檔名": 變數 }
save_map = {
    "pe_ratio.csv": pe_final,
    "pb_ratio.csv": pb_final,
    "yd.csv":       yd_final,
    "beta.csv":     beta_final,
    "mktcap.csv":   mktcap_final,
    "eps.csv":      eps_final,
    "gross.csv":    gross_final,
    "rev.csv":      rev_final,
    "earn_yoy.csv": earn_yoy_final,
    "price.csv":    price_final
}



import os

# 1. 定義路徑
path = "merged_csvs/"

# 2. 檢查資料夾是否存在，不存在就建立它 (關鍵修正！)
if not os.path.exists(path):
    os.makedirs(path)
    print(f"📁 偵測到資料夾不存在，已自動建立：{path}")
# 用一個簡單的迴圈一次搞定
for filename, df in save_map.items():
    df.to_csv(f"{path}{filename}")
    print(f"✅ {filename} 已更新")

