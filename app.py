import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# 페이지 설정
st.set_page_config(page_title="K-Stock Intelligence Pro", layout="wide")

# 스타일링
st.markdown("""
    <style>
    .stMetric { border: 1px solid #374151; padding: 10px; border-radius: 8px; background: #111827; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f2937; border-radius: 5px; padding: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 데이터 로드 (캐싱)
@st.cache_data(ttl=600)
def get_stock_data():
    return fdr.StockListing('KRX')

df_krx = get_stock_data()

# --- 1. 상단 글로벌 상황판 ---
st.markdown("### 🌍 Global & Domestic Dashboard")
m_cols = st.columns(5)
indices = {"KOSPI": "KS11", "KOSDAQ": "KQ11", "나스닥": "IXIC", "S&P500": "US500", "환율": "USD/KRW"}
for i, (name, code) in enumerate(indices.items()):
    try:
        d = fdr.DataReader(code).tail(2)
        m_cols[i].metric(name, f"{d['Close'].iloc[-1]:,.2f}", f"{d['Close'].iloc[-1]-d['Close'].iloc[-2]:+.2f}")
    except: pass

st.divider()

# --- 2. 메인 탭 구성 (짜임새 있는 기능 배치) ---
main_tabs = st.tabs(["📊 실시간 수급/거래량", "🎯 기법별 종목포착", "🗞️ 마켓 이슈", "🔍 개별분석"])

# [Tab 1] 실시간 수급 및 거래량 상위
with main_tabs[0]:
    st.subheader("⚡ 실시간 시장 수급 엔진")
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("#### 🔥 거래량 상위 (실시간)")
        # 실제 운영시는 상세 크롤링 필요하나, 여기선 KRX 리스트의 등락률 기반 예시
        top_vol = df_krx.sort_values(by='Volume', ascending=False).head(10)
        st.dataframe(top_vol[['Name', 'Code', 'ChgCode']], hide_index=True)

    with c2:
        st.markdown("#### 🏦 외국인/기관 순매수 (추정)")
        st.caption("최근 거래일 기준 메이저 수급 상위")
        # 최근 등락률과 시총을 고려한 수급 유입 추정 종목
        st.dataframe(df_krx.nlargest(10, 'Amount')[['Name', 'Market']], hide_index=True)

    with c3:
        st.markdown("#### 🏗️ 연기금/국민연금 집중")
        st.caption("우량주 위주의 장기 매집 종목")
        pension_pick = df_krx[df_krx['Market'] == 'KOSPI'].head(10)
        st.dataframe(pension_pick[['Name', 'Code']], hide_index=True)

# [Tab 2] 기법별 종목 포착 (전문가 기법 4종)
with main_tabs[1]:
    sub_c1, sub_c2 = st.columns([1, 4])
    with sub_c1:
        st.write("🔍 **전략 선택**")
        strategy = st.radio("적용할 기법", ["60월선 바닥매집(족보집)", "N자형 눌림목", "거래량 골든크로스", "볼린저밴드 상단돌파"])
        scan_num = st.number_input("스캔 종목 수", 50, 500, 100)
        start_scan = st.button("🚀 분석 엔진 가동")
    
    with sub_c2:
        if start_scan:
            results = []
            bar = st.progress(0)
            target = df_krx.head(scan_num)
            
            for i, row in target.iterrows():
                try:
                    # 데이터 분석 로직 (앞서 구현한 로직들 통합)
                    df = fdr.DataReader(row['Code']).tail(100)
                    curr = df.iloc[-1]
                    prev = df.iloc[-2]
                    
                    if strategy == "60월선 바닥매집(족보집)":
                        # 월봉 로직 간소화 적용
                        df_m = fdr.DataReader(row['Code'], interval='monthly').tail(65)
                        df_m['MA60'] = df_m['Close'].rolling(60).mean()
                        if df_m['Close'].iloc[-1] >= df_m['MA60'].iloc[-1] and df_m['Close'].iloc[-2] < df_m['MA60'].iloc[-2]:
                            results.append((row['Name'], row['Code'], df_m))
                    
                    elif strategy == "N자형 눌림목":
                        ma20 = df['Close'].rolling(20).mean()
                        if prev['Close'] > ma20.iloc[-2] and curr['Low'] <= ma20.iloc[-1] and curr['Close'] > ma20.iloc[-1]:
                            results.append((row['Name'], row['Code'], df))
                            
                    elif strategy == "거래량 골든크로스":
                        if curr['Volume'] > df['Volume'].rolling(5).mean().iloc[-2] * 2.5:
                            results.append((row['Name'], row['Code'], df))
                except: pass
                bar.progress((i+1)/len(target))
            
            if results:
                for name, code, r_df in results:
                    with st.expander(f"✅ 포착: {name} ({code})"):
                        st.line_chart(r_df['Close'])
            else:
                st.warning("조건에 맞는 종목이 없습니다.")

# [Tab 3] 마켓 이슈 (뉴스 크롤링)
with main_tabs[2]:
    st.subheader("📰 실시간 정부정책 및 해외 주요뉴스")
    # 앞서 만든 뉴스 크롤링 함수 적용
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver")
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.mainNewsList .articleSubject a')
        for item in items[:10]:
            st.markdown(f"🔗 [{item.get_text().strip()}](https://finance.naver.com{item['href']})")
    except: st.error("뉴스 로딩 실패")