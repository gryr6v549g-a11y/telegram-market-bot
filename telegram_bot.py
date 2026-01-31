def build_message():
    now = datetime.now(ZoneInfo("Asia/Seoul")).strftime("%Y-%m-%d %H:%M:%S")

    usdkrw, jpykrw, usdjpy, gold, wti, kospi, kospi_chg, k_high, k_low = market_prices()
    m = us_macro()

    dxy_hist = yf.Ticker("DX-Y.NYB").history(period="2d")
    dxy_close = dxy_hist["Close"].iloc[-1]
    dxy_prev = dxy_hist["Close"].iloc[-2]
    dxy_chg = dxy_close - dxy_prev

    vix_hist = yf.Ticker("^VIX").history(period="2d")
    vix_close = vix_hist["Close"].iloc[-1]
    vix_prev = vix_hist["Close"].iloc[-2]
    vix_chg = vix_close - vix_prev

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

솔빈이 횽아 화이팅! 용치리 픽스터도 화이팅!
""".strip()
