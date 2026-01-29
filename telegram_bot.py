# -*- coding: utf-8 -*-

import requests
import yfinance as yf
from datetime import datetime
from zoneinfo import ZoneInfo
import time

# =========================
# 🔑 TELEGRAM SETTINGS
# =========================
TELEGRAM_TOKEN = "8425170540:AAH4FpyLEX83vn413p-o2yINwZpIplomVEg"
FRED_API_KEY = "27af567b7542c18ee527d92a06f330a0"

TELEGRAM_API = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

# =========================
# 📡 SAFE FRED FETCH
# =========================
def fred(series, limit=24):
    url = "https://api.stlouisfed.org/fred/series/observations"
    params = {
        "series_id": series,
        "api_key": FRED_API_KEY,
        "file_type": "json",
        "sort_order": "desc",
        "limit": limit
    }
    r = requests.get(url, params=params).json()
    if "observations" not in r:
        return []
    return [float(x["value"]) for x in r["observations"] if x["value"] != "."]

def latest(series):
    v = fred(series, 1)
    return v[0] if v else None

# =========================
# 📊 MARKET PRICES
# =========================
def market_prices():
    def asset(ticker, fx=1):
        d2 = yf.Ticker(ticker).history(period="2d")
        m1 = yf.Ticker(ticker).history(period="1mo")

        close = d2["Close"].iloc[-1] * fx
        prev = d2["Close"].iloc[-2] * fx
        chg = close - prev
        high_1m = m1["High"].max() * fx
        low_1m = m1["Low"].min() * fx

        return close, chg, high_1m, low_1m

    usdkrw = asset("USDKRW=X")
    jpykrw = asset("JPYKRW=X", fx=100)
    usdjpy = asset("JPY=X")
    gold = asset("GC=F")
    wti = asset("CL=F")

    dxy = asset("DX-Y.NYB")   # 달러인덱스
    vix = asset("^VIX")       # 변동성 지수

    kospi_d = yf.Ticker("^KS200").history(period="1d")

    return (
        usdkrw,
        jpykrw,
        usdjpy,
        gold,
        wti,
        dxy,
        vix,
        kospi_d["Close"].iloc[-1],
        kospi_d["High"].iloc[-1],
        kospi_d["Low"].iloc[-1]
    )

# =========================
# 🇺🇸 US MACRO
# =========================
def us_macro():
    cpi = fred("CPIAUCSL", 13)
    cpi_yoy = (cpi[0] / cpi[12] - 1) * 100 if len(cpi) >= 13 else None
    cpi_mom = (cpi[0] / cpi[1] - 1) * 100 if len(cpi) >= 2 else None

    return {
        "fed": latest("EFFR"),
        "t3m": latest("DTB3"),
        "t10y": latest("DGS10"),
        "t30y": latest("DGS30"),
        "unrate": latest("UNRATE"),
        "bls": latest("PAYEMS"),
        "adp": latest("ADPWNUSERS"),
        "gdp": latest("A191RL1Q225SBEA"),
        "cpi_yoy": cpi_yoy,
        "cpi_mom": cpi_mom
    }

# =========================
# 📝 FORMAT
# =========================
def arrow(v):
    return "▲" if v > 0 else "▼"

def fmt(v, suf=""):
    return f"{v:.2f}{suf}" if isinstance(v, (int, float)) else "N/A"

# =========================
# 📝 MESSAGE
# =========================
def build_message():
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    usdkrw, jpykrw, usdjpy, gold, wti, dxy, vix, kospi, k_high, k_low = market_prices()
    m = us_macro()

    return f"""
[실시간 시장 브리핑]
{now}

[시장 가격]
달러/원: {fmt(usdkrw[0])} ({arrow(usdkrw[1])}{fmt(usdkrw[1])})
  · 한달: 고 {fmt(usdkrw[2])} / 저 {fmt(usdkrw[3])}

엔/원(100엔): {fmt(jpykrw[0])} ({arrow(jpykrw[1])}{fmt(jpykrw[1])})
  · 한달: 고 {fmt(jpykrw[2])} / 저 {fmt(jpykrw[3])}

달러/엔: {fmt(usdjpy[0])} ({arrow(usdjpy[1])}{fmt(usdjpy[1])})
  · 한달: 고 {fmt(usdjpy[2])} / 저 {fmt(usdjpy[3])}

금: {fmt(gold[0])} ({arrow(gold[1])}{fmt(gold[1])})
WTI: {fmt(wti[0])} ({arrow(wti[1])}{fmt(wti[1])})

[위험 지표]
DXY(달러지수): {fmt(dxy[0])} ({arrow(dxy[1])}{fmt(dxy[1])})
VIX(변동성): {fmt(vix[0])} ({arrow(vix[1])}{fmt(vix[1])})

코스피200: {fmt(kospi)}
  · 당일 고 / 저: {fmt(k_high)} / {fmt(k_low)}

[미국 국채 금리]
기준금리: {fmt(m['fed'], '%')}
3개월: {fmt(m['t3m'], '%')}
10년물: {fmt(m['t10y'], '%')}
30년물: {fmt(m['t30y'], '%')}
""".strip()

# =========================
# 🤖 BOT LOOP
# =========================
def run_bot():
    offset = None
    while True:
        r = requests.get(
            f"{TELEGRAM_API}/getUpdates",
            params={"offset": offset, "timeout": 60}
        ).json()

        for u in r.get("result", []):
            offset = u["update_id"] + 1
            msg = u.get("message", {})
            if msg.get("text", "").strip() == ".":
                requests.post(
                    f"{TELEGRAM_API}/sendMessage",
                    data={"chat_id": msg["chat"]["id"], "text": build_message()}
                )
        time.sleep(1)

if __name__ == "__main__":
    run_bot()
