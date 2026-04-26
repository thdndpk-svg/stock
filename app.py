import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go

# --- 설정 및 스타일 ---
st.set_page_config(page_title="급등주 지니", layout="wide")
st.markdown("<style>.stApp { background-color: #0e1117; color: white; }</style>", unsafe_allow_html=True)

# --- 분석 로직 ---
def analyze(name, ticker):
    try:
        df = yf.Ticker(ticker).history(period="60d")
        if len(df) < 20: return None
        df['MA5'] = ta.sma(df['Close'], length=5)
        df['MA20'] = ta.sma(df['Close'], length=20)
        df['RSI'] = ta.rsi(df['Close'], length=14)
        
        last = df.iloc[-1]
        score = 0
        if last['Volume'] > df['Volume'].tail(20).mean() * 1.5: score += 40
        if last['MA5'] > last['MA20']: score += 30
        if 50 < last['RSI'] < 70: score += 30
        
        return {"name": name, "price": last['Close'], "pct": ((last['Close']-df['Close'].iloc[-2])/df['Close'].iloc[-2])*100, "score": score, "df": df}
    except: return None

# --- UI ---
st.title("🚀 내일의 급등주 TOP 5")
target_dict = {"삼성전자": "005930.KS", "SK하이닉스": "000660.KS", "NAVER": "035420.KS", "카카오": "035720.KS", "에코프로비엠": "247540.KQ", "한미반도체": "042700.KS"}

if st.button("🔍 분석 시작"):
    results = []
    bar = st.progress(0)
    for i, (n, c) in enumerate(target_dict.items()):
        res = analyze(n, c)
        if res: results.append(res)
        bar.progress((i+1)/len(target_dict))
    
    for i, s in enumerate(sorted(results, key=lambda x: x['score'], reverse=True)[:5]):
        st.markdown(f"### {i+1}위: {s['name']} (예측강도 {s['score']}%)")
        st.write(f"현재가: {int(s['price']):,}원 ({s['pct']:.2f}%)")
        with st.expander("차트 보기"):
            fig = go.Figure(data=[go.Candlestick(x=s['df'].index, open=s['df']['Open'], high=s['df']['High'], low=s['df']['Low'], close=s['df']['Close'])])
            st.plotly_chart(fig, use_container_width=True)