import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

# 페이지 설정
st.set_page_config(page_title="내일의 급등주 TOP 5", layout="wide")

st.title("🚀 내일의 급등주 예측기 (v2.1)")
st.write("데이터 제한 에러를 방지하도록 설계된 버전입니다.")

# 분석 대상 종목 (KOSPI 주요 종목)
tickers = ["005930.KS", "000660.KS", "035420.KS", "035720.KS", "005380.KS", "068270.KS", "005490.KS", "000270.KS"]

def analyze_stock(ticker):
    try:
        # 야후 파이낸스 데이터 호출 방식 변경
        stock = yf.Ticker(ticker)
        data = stock.history(period="60d")
        
        if data.empty or len(data) < 20:
            return None
        
        # 이동평균선 및 RSI 직접 계산
        data['SMA20'] = data['Close'].rolling(window=20).mean()
        delta = data['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data['RSI'] = 100 - (100 / (1 + rs))
        
        current_price = data['Close'].iloc[-1]
        current_rsi = data['RSI'].iloc[-1]
        sma_20 = data['SMA20'].iloc[-1]
        
        score = 0
        if current_rsi < 45: score += 50  # 과매도 구간 근접
        if current_price > sma_20: score += 50  # 상승 추세
        
        return {"ticker": ticker, "price": current_price, "rsi": current_rsi, "score": score, "data": data}
    except Exception as e:
        # 에러 발생 시 건너뛰기
        return None

if st.button("📈 지금 분석 시작"):
    results = []
    with st.spinner('종목별 데이터를 불러오는 중...'):
        for t in tickers:
            res = analyze_stock(t)
            if res:
                results.append(res)
    
    if not results:
        st.error("현재 야후 파이낸스 서버 연결이 원활하지 않습니다. 잠시 후 다시 시도해 주세요!")
    else:
        results = sorted(results, key=lambda x: x['score'], reverse=True)[:5]
        for res in results:
            with st.expander(f"📌 종목: {res['ticker']} (예측 점수: {res['score']}점)"):
                st.write(f"현재가: {res['price']:.0f}원 | RSI 지수: {res['rsi']:.1f}")
                fig = go.Figure(data=[go.Candlestick(x=res['data'].index,
                                open=res['data']['Open'], high=res['data']['High'],
                                low=res['data']['Low'], close=res['data']['Close'])])
                st.plotly_chart(fig)