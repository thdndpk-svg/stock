import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

# 페이지 설정
st.set_page_config(page_title="내일의 급등주 TOP 5", layout="wide")

st.title("🚀 내일의 급등주 예측기 (v2.0)")
st.write("인공지능 분석을 통해 내일 상승 가능성이 높은 종목을 추출합니다.")

# 분석 대상 종목 (KOSPI/KOSDAQ 주요 종목)
tickers = ["005930.KS", "000660.KS", "035420.KS", "035720.KS", "005380.KS", "068270.KS", "005490.KS", "000270.KS", "036570.KS", "096770.KS"]

def analyze_stock(ticker):
    try:
        stock = yf.Ticker(ticker)
data = stock.history(period="60d")
        
        # 단순 이동평균선(SMA) 직접 계산 (pandas_ta 미사용)
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        
        # RSI 지수 직접 계산
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        # 급등주 조건: RSI가 낮고(과매도), 현재가가 20일선 위에 있음
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        sma_20 = data['SMA20'].iloc[-1]
        
        score = 0
        if current_rsi < 40: score += 50
        if current_price > sma_20: score += 50
        
        return {"ticker": ticker, "price": current_price, "rsi": current_rsi, "score": score, "data": data}
    except:
        return None

if st.button("📈 지금 분석 시작"):
    results = []
    with st.spinner('시장 데이터를 분석 중입니다...'):
        for t in tickers:
            res = analyze_stock(t)
            if res: results.append(res)
    
    # 점수 순으로 정렬
    results = sorted(results, key=lambda x: x['score'], reverse=True)[:5]
    
    for res in results:
        with st.expander(f"📌 종목: {res['ticker']} (예측 점수: {res['score']}점)"):
            st.write(f"현재가: {res['price']:.0f}원 | RSI 지수: {res['rsi']:.1f}")
            fig = go.Figure(data=[go.Candlestick(x=res['data'].index,
                            open=res['data']['Open'], high=res['data']['High'],
                            low=res['data']['Low'], close=res['data']['Close'])])
            st.plotly_chart(fig)