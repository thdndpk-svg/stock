import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="K-주식 급등주 탐색기", layout="wide")

st.title("🇰🇷 한국 시장 실시간 급등주 탐색기")
st.write("네이버 금융 데이터를 분석하여 현재 시장에서 가장 뜨거운 종목을 찾아냅니다.")

# 1. 한국 시장 전체 종목 리스트 가져오기 (KOSPI, KOSDAQ)
@st.cache_data(ttl=3600) # 1시간마다 리스트 갱신
def get_stock_list():
    df_krx = fdr.StockListing('KRX') # 코스피, 코스닥, 코넥스 통합
    return df_krx[['Code', 'Name', 'Market']]

def analyze_stock(code, name):
    try:
        # 최근 40일치 데이터 (주말 제외 약 2달치)
        df = fdr.DataReader(code, (datetime.now() - timedelta(days=60)).strftime('%Y-%m-%d'))
        if len(df) < 20: return None
        
        current_price = df['Close'].iloc[-1]
        prev_price = df['Close'].iloc[-2]
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        # 기술적 지표 계산 (이동평균선, RSI)
        ma20 = df['Close'].rolling(window=20).mean().iloc[-1]
        
        delta = df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]

        # 급등주 필터링 조건: 오늘 3% 이상 상승 중이며 이평선 정배열
        if change_pct > 3 and current_price > ma20:
            return {
                "name": name, "code": code, "price": current_price,
                "change": change_pct, "rsi": current_rsi, "df": df
            }
    except:
        return None

if st.button("🔍 실시간 시장 스캔 (상위 종목 분석)"):
    stock_list = get_stock_list()
    # 너무 많으면 느려지므로 시가총액 상위나 거래량 상위 느낌으로 100개 정도만 우선 스캔
    target_stocks = stock_list.head(150) 
    
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()

    for i, row in target_stocks.iterrows():
        status_text.text(f"분석 중: {row['Name']}")
        res = analyze_stock(row['Code'], row['Name'])
        if res:
            results.append(res)
        progress_bar.progress((i + 1) / len(target_stocks))
    
    status_text.text("분석 완료!")
    
    if not results:
        st.warning("현재 조건에 맞는 급등 종목이 없습니다.")
    else:
        st.success(f"오늘의 급등 유망주 {len(results)}개를 찾았습니다!")
        for res in results:
            with st.expander(f"🚩 {res['name']} ({res['code']}) - 현재 {res['change']:.2f}% 상승 중"):
                col1, col2 = st.columns(2)
                col1.metric("현재가", f"{res['price']:,}원", f"{res['change']:.2f}%")
                col2.metric("RSI(심리도)", f"{res['rsi']:.1f}")
                
                fig = go.Figure(data=[go.Candlestick(
                    x=res['df'].index,
                    open=res['df']['Open'], high=res['df']['High'],
                    low=res['df']['Low'], close=res['df']['Close']
                )])
                fig.update_layout(xaxis_rangeslider_visible=False, margin=dict(l=10, r=10, t=10, b=10))
                st.plotly_chart(fig, use_container_width=True)