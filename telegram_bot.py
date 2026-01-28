# -*- coding: utf-8 -*-

import requests
import yfinance as yf
from datetime import datetime
import time

TELEGRAM_TOKEN = "8425170540:AAH59mm5RL1uRciPNb-7XFKSkwUxptMPSWQ"
FRED_API_KEY = "27af567b7542c18ee527d92a06f330a0"

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

    usd = asset("USDKRW=X")
    jpy = asset("JPYKRW=X", fx=100)
    gold = asset("GC=F")
    wti = asset("CL=F")

    kospi_d = yf.Ticker("^KS200").history(period="1d")
    kospi_close = kospi_d["Close"].iloc[-1]
    kospi_high = kospi_d["High"].iloc[-1]
    kospi_low = kospi_d["Low"].iloc[-1]

    return usd, jpy, gold, wti, kospi_close, kospi_high, kospi_low

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
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    usd, jpy, gold, wti, kospi, k_high, k_low = market_prices()
    m = us_macro()

    return f"""
[실시간 시장 브리핑]
{now}

[시장 가격]
달러/원: {fmt(usd[0])} ({arrow(usd[1])}{fmt(usd[1])})
  · 한달: 고 {fmt(usd[2])} / 저 {fmt(usd[3])}

엔/원(100엔): {fmt(jpy[0])} ({arrow(jpy[1])}{fmt(jpy[1])})
  · 한달: 고 {fmt(jpy[2])} / 저 {fmt(jpy[3])}

금: {fmt(gold[0])} ({arrow(gold[1])}{fmt(gold[1])})
  · 한달: 고 {fmt(gold[2])} / 저 {fmt(gold[3])}

WTI: {fmt(wti[0])} ({arrow(wti[1])}{fmt(wti[1])})
  · 한달: 고 {fmt(wti[2])} / 저 {fmt(wti[3])}

코스피200: {fmt(kospi)}
  · 당일 고 / 저: {fmt(k_high)} / {fmt(k_low)}

[미국 국채 금리 커브]
기준금리: {fmt(m['fed'], '%')}
3개월: {fmt(m['t3m'], '%')}
10년물: {fmt(m['t10y'], '%')}
30년물: {fmt(m['t30y'], '%')}

[미국 거시지표]
CPI YoY: {fmt(m['cpi_yoy'], '%')}
CPI MoM: {fmt(m['cpi_mom'], '%')}
실업률: {fmt(m['unrate'], '%')}
비농업고용(BLS): {fmt(m['bls'])}
ADP 민간고용: {fmt(m['adp'])}
실질 GDP 성장률: {fmt(m['gdp'], '%')}
""".strip()

# =========================
# 🤖 TELEGRAM BOT
# =========================
def run_bot():
    print("🤖 텔레그램 시장 브리핑 봇 실행 중...")
    offset = None

    while True:
        updates = requests.get(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
            params={"offset": offset, "timeout": 30}
        ).json()

        for u in updates.get("result", []):
            offset = u["update_id"] + 1
            text = u["message"].get("text", "")
            chat_id = u["message"]["chat"]["id"]

            if text.strip() == ".":
                requests.post(
                    f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
                    data={"chat_id": chat_id, "text": build_message()}
                )

        time.sleep(1)

if __name__ == "__main__":
    run_bot()
