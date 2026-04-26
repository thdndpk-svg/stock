import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="K-Stock 매집주 탐색기", layout="wide")

st.title("🚀 실전 주식: 바닥 매집주 & 60월선 돌파 시스템")

# 탭 구성
tab1, tab2, tab3 = st.tabs(["💎 바닥 매집주 포착", "📈 실시간 급등주", "🔍 종목 검색"])

@st.cache_data(ttl=3600)
def get_krx_list():
    return fdr.StockListing('KRX')

df_krx = get_krx_list()

# --- 기법 적용 함수 ---
def analyze_bottom_accumulation(code, name):
    try:
        # 월봉 데이터를 위해 충분한 기간(약 10년) 호출
        df_month = fdr.DataReader(code, '2015-01-01', interval='monthly')
        if len(df_month) < 60: return None
        
        # 60월 이동평균선 계산
        df_month['MA60'] = df_month['Close'].rolling(window=60).mean()
        
        curr = df_month.iloc[-1]  # 현재 월
        prev = df_month.iloc[-2]  # 직전 월
        
        # 기법 조건 1: 주가가 60월선 근처에 있거나 막 돌파했는가?
        is_breakout = prev['Close'] < prev['MA60'] and curr['Close'] >= curr['MA60']
        is_on_line = abs(curr['Close'] - curr['MA60']) / curr['MA60'] < 0.05 # 60월선과 5% 이내 인접
        
        # 기법 조건 2: 바닥권 확인 (최근 1년 최고점 대비 많이 하락해 있는가?)
        high_1y = df_month['High'].tail(12).max()
        is_bottom = curr['Close'] < high_1y * 0.7 # 고점 대비 30% 이상 하락 상태
        
        if (is_breakout or is_on_line) and is_bottom:
            return {
                "name": name, "code": code, "price": curr['Close'],
                "ma60": curr['MA60'], "df": df_month,
                "type": "골든크로스 돌파" if is_breakout else "60월선 지지/매집"
            }
    except: return None

# --- Tab 1: 바닥 매집주 포착 ---
with tab1:
    st.header("📂 족보집 기법: 60월선 바닥 매집주")
    st.info("5년 평균선(60월선)을 돌파하거나 안착하며 에너지를 모으는 종목을 찾습니다.")
    
    if st.button("바닥 매집주 스캔 시작"):
        targets = df_krx.head(300) # 상위 300개 우선 스캔
        found_stocks = []
        prog = st.progress(0)
        
        for i, row in targets.iterrows():
            res = analyze_bottom_accumulation(row['Code'], row['Name'])
            if res: found_stocks.append(res)
            prog.progress((i+1)/len(targets))
            
        if not found_stocks:
            st.warning("현재 기법에 부합하는 바닥 매집주가 없습니다.")
        else:
            for s in found_stocks:
                with st.expander(f"💎 {s['name']} ({s['code']}) - {s['type']}"):
                    st.write(f"현재가: {s['price']:,}원 | 60월선 위치: {s['ma60']:,.0f}원")
                    
                    # 월봉 차트 시각화
                    fig = go.Figure()
                    fig.add_trace(go.Candlestick(x=s['df'].index, open=s['df']['Open'], 
                                               high=s['df']['High'], low=s['df']['Low'], 
                                               close=s['df']['Close'], name="월봉"))
                    fig.add_trace(go.Scatter(x=s['df'].index, y=s['df']['MA60'], 
                                           line=dict(color='red', width=2), name="60월선"))
                    fig.update_layout(title=f"{s['name']} 월봉 차트 (60월선 포함)", xaxis_rangeslider_visible=False)
                    st.plotly_chart(fig, use_container_width=True)

# (기존 Tab 2, Tab 3 코드는 유지하거나 필요에 따라 통합 가능)