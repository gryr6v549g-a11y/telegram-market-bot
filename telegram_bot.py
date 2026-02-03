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

def latest_with_change(series):
    v = fred(series, 2)
    if len(v) >= 2:
        return v[0], v[0] - v[1]
    elif len(v) == 1:
        return v[0], 0
    return None, None

# =========================
# 📊 MARKET PRICES
# =========================
def market_prices():
    def asset(ticker, fx=1):
        d5 = yf.Ticker(ticker).history(period="5d")
        m1 = yf.Ticker(ticker).history(period="1mo")

        close = d5["Close"].iloc[-1] * fx
        prev = d5["Close"].iloc[-2] * fx
        chg = close - prev
        high_1m = m1["High"].max() * fx
        low_1m = m1["Low"].min() * fx

        return close, chg, high_1m, low_1m

    usdkrw = asset("USDKRW=X")
    jpykrw = asset("JPYKRW=X", fx=100)
    usdjpy = asset("JPY=X", fx=100)
    gold = asset("GC=F")
    wti = asset("CL=F")

    kospi_hist = yf.Ticker("^KS200").history(period="5d")
    kospi_close = kospi_hist["Close"].iloc[-1]
    kospi_prev = kospi_hist["Close"].iloc[-2]
    kospi_chg = kospi_close - kospi_prev

    kospi_day = yf.Ticker("^KS200").history(period="1d")

    return (
        usdkrw,
        jpykrw,
        usdjpy,
        gold,
        wti,
        kospi_close,
        kospi_chg,
        kospi_day["High"].iloc[-1],
        kospi_day["Low"].iloc[-1]
    )

# =========================
# 🇺🇸 US MACRO
# =========================
def us_macro():
    cpi = fred("CPIAUCSL", 13)
    cpi_yoy = (cpi[0] / cpi[12] - 1) * 100 if len(cpi) >= 13 else None
    cpi_mom = (cpi[0] / cpi[1] - 1) * 100 if len(cpi) >= 2 else None

    fed, fed_chg = latest_with_change("EFFR")
    t1y, t1y_chg = latest_with_change("DGS1")
    t5y, t5y_chg = latest_with_change("DGS5")
    t10y, t10y_chg = latest_with_change("DGS10")
    t30y, t30y_chg = latest_with_change("DGS30")

    return {
        "fed": fed, "fed_chg": fed_chg,
        "t1y": t1y, "t1y_chg": t1y_chg,
        "t5y": t5y, "t5y_chg": t5y_chg,
        "t10y": t10y, "t10y_chg": t10y_chg,
        "t30y": t30y, "t30y_chg": t30y_chg,
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

    usdkrw, jpykrw, usdjpy, gold, wti, kospi, kospi_chg, k_high, k_low = market_prices()
    m = us_macro()

    dxy_hist = yf.Ticker("DX-Y.NYB").history(period="5d")
    dxy_close = dxy_hist["Close"].iloc[-1]
    dxy_prev = dxy_hist["Close"].iloc[-2]
    dxy_chg = dxy_close - dxy_prev

    vix_hist = yf.Ticker("^VIX").history(period="5d")
    vix_close = vix_hist["Close"].iloc[-1]
    vix_prev = vix_hist["Close"].iloc[-2]
    vix_chg = vix_close - vix_prev

    # 🔥 VKOSPI 추가 (이 부분만 신규)
    vkospi_hist = yf.Ticker("^VKOSPI").history(period="5d")
    vkospi_close = vkospi_hist["Close"].iloc[-1]
    vkospi_prev = vkospi_hist["Close"].iloc[-2]
    vkospi_chg = vkospi_close - vkospi_prev

    return f"""
[실시간 시장 브리핑]
{now}

[시장 가격]
달러/원: {fmt(usdkrw[0])} ({arrow(usdkrw[1])}{fmt(usdkrw[1])})
  · 한달: 고 {fmt(usdkrw[2])} / 저 {fmt(usdkrw[3])}

엔/원(100엔): {fmt(jpykrw[0])} ({arrow(jpykrw[1])}{fmt(jpykrw[1])})
  · 한달: 고 {fmt(jpykrw[2])} / 저 {fmt(jpykrw[3])}

엔/달러(100엔): {fmt(usdjpy[0])} ({arrow(usdjpy[1])}{fmt(usdjpy[1])})
  · 한달: 고 {fmt(usdjpy[2])} / 저 {fmt(usdjpy[3])}

금: {fmt(gold[0])} ({arrow(gold[1])}{fmt(gold[1])})
  · 한달: 고 {fmt(gold[2])} / 저 {fmt(gold[3])}

WTI: {fmt(wti[0])} ({arrow(wti[1])}{fmt(wti[1])})
  · 한달: 고 {fmt(wti[2])} / 저 {fmt(wti[3])}

코스피200: {fmt(kospi)} ({arrow(kospi_chg)}{fmt(kospi_chg)})
  · 당일: 고 {fmt(k_high)} / 저 {fmt(k_low)}

[미국 국채 금리]
기준금리: {fmt(m['fed'], '%')} ({arrow(m['fed_chg'])}{fmt(m['fed_chg'], '%')})
1년물: {fmt(m['t1y'], '%')} ({arrow(m['t1y_chg'])}{fmt(m['t1y_chg'], '%')})
5년물: {fmt(m['t5y'], '%')} ({arrow(m['t5y_chg'])}{fmt(m['t5y_chg'], '%')})
10년물: {fmt(m['t10y'], '%')} ({arrow(m['t10y_chg'])}{fmt(m['t10y_chg'], '%')})
30년물: {fmt(m['t30y'], '%')} ({arrow(m['t30y_chg'])}{fmt(m['t30y_chg'], '%')})

[미국 거시지표]
CPI YoY: {fmt(m['cpi_yoy'], '%')}
CPI MoM: {fmt(m['cpi_mom'], '%')}
실업률: {fmt(m['unrate'], '%')}
비농업고용(BLS): {fmt(m['bls'])}
ADP 민간고용: {fmt(m['adp'])}
실질 GDP 성장률: {fmt(m['gdp'], '%')}

[위험 지표]
달러 인덱스: {fmt(dxy_close)} ({arrow(dxy_chg)}{fmt(dxy_chg)})
VIX(변동성): {fmt(vix_close)} ({arrow(vix_chg)}{fmt(vix_chg)})
VKOSPI(코스피 변동성): {fmt(vkospi_close)} ({arrow(vkospi_chg)}{fmt(vkospi_chg)})
어어 로켓 쏜다 쏜다 포모 바로 옆에 있다
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
            text = msg.get("text", "")
            chat_id = msg.get("chat", {}).get("id")

            if text.strip() == ".":
                requests.post(
                    f"{TELEGRAM_API}/sendMessage",
                    data={"chat_id": chat_id, "text": build_message()}
                )

        time.sleep(1)

if __name__ == "__main__":
    run_bot()
