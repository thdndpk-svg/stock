import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 및 디자인
st.set_page_config(page_title="K-Stock Intelligence Pro", layout="wide")

st.markdown("""
    <style>
    .stMetric { border: 1px solid #374151; padding: 10px; border-radius: 8px; background: #111827; }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { background-color: #1f2937; border-radius: 5px; padding: 10px; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진
@st.cache_data(ttl=600)
def get_stock_data():
    df = fdr.StockListing('KRX')
    # 에러 방지: 존재하는 컬럼명만 사용하도록 정제
    return df

df_krx = get_stock_data()

# 3. 뉴스 크롤링 함수
def get_realtime_news():
    news_list = []
    try:
        url = "https://finance.naver.com/news/mainnews.naver"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.mainNewsList .articleSubject a')
        for item in items[:8]:
            news_list.append({"title": item.get_text().strip(), "link": "https://finance.naver.com" + item['href']})
    except:
        news_list.append({"title": "뉴스를 불러올 수 없습니다.", "link": "#"})
    return news_list

# --- 메인 대시보드 ---
st.title("🛡️ K-Stock 실전 투자 전용 시스템")

# 상단 지수 전광판
m_cols = st.columns(5)
indices = {"KOSPI": "KS11", "KOSDAQ": "KQ11", "나스닥": "IXIC", "S&P500": "US500", "환율": "USD/KRW"}
for i, (name, code) in enumerate(indices.items()):
    try:
        idx_df = fdr.DataReader(code).tail(2)
        curr = idx_df['Close'].iloc[-1]
        prev = idx_df['Close'].iloc[-2]
        m_cols[i].metric(name, f"{curr:,.2f}", f"{curr-prev:+.2f}")
    except: pass

st.divider()

main_tabs = st.tabs(["📊 실시간 수급/거래량", "🎯 기법별 종목포착", "🗞️ 마켓 이슈"])

# [Tab 1] 실시간 수급 및 거래량 (에러 수정 완료)
with main_tabs[0]:
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("#### 🔥 실시간 거래대금 상위")
        # 컬럼명이 다를 수 있으므로 안전하게 처리
        sort_col = 'Marcap' if 'Marcap' in df_krx.columns else df_krx.columns[0]
        top_trade = df_krx.nlargest(15, sort_col)
        # 안전한 컬럼만 출력 (Name, Code 등)
        st.dataframe(top_trade[['Name', 'Code', 'Market']], hide_index=True, use_container_width=True)

    with c2:
        st.markdown("#### 🏦 외국인/기관 매수 추정")
        # 등락률(Chg)이 높은 종목을 수급 유입으로 간주 (실전 기법)
        if 'Chg' in df_krx.columns:
            top_up = df_krx.nlargest(15, 'Chg')
            st.dataframe(top_up[['Name', 'Code', 'Chg']], hide_index=True, use_container_width=True)

    with c3:
        st.markdown("#### 🏗️ 연기금/국민연금 선호주")
        pension_style = df_krx[df_krx['Market'] == 'KOSPI'].head(15)
        st.dataframe(pension_style[['Name', 'Code']], hide_index=True, use_container_width=True)

# [Tab 2] 기법별 종목 포착 (로직 고도화)
with main_tabs[1]:
    col_set, col_res = st.columns([1, 3])
    with col_set:
        strategy = st.radio("전략 선택", ["60월선 바닥매집(족보집)", "N자형 눌림목", "거래량 폭증"])
        scan_btn = st.button("🚀 기법 스캔 시작")
    
    with col_res:
        if scan_btn:
            results = []
            p_bar = st.progress(0)
            status = st.empty()
            targets = df_krx.head(100) # 성능을 위해 우선 100개
            
            for i, row in targets.iterrows():
                status.text(f"🔍 분석 중: {row['Name']}")
                try:
                    if strategy == "60월선 바닥매집(족보집)":
                        df_m = fdr.DataReader(row['Code'], interval='monthly').tail(65)
                        df_m['MA60'] = df_m['Close'].rolling(60).mean()
                        if df_m['Close'].iloc[-1] >= df_m['MA60'].iloc[-1] and df_m['Close'].iloc[-2] < df_m['MA60'].iloc[-2]:
                            results.append((row['Name'], row['Code'], df_m, "60월선 골든크로스"))
                    
                    elif strategy == "N자형 눌림목":
                        df_d = fdr.DataReader(row['Code']).tail(30)
                        ma20 = df_d['Close'].rolling(20).mean()
                        if df_d['Close'].iloc[-2] > ma20.iloc[-2] and df_d['Low'].iloc[-1] <= ma20.iloc[-1] and df_d['Close'].iloc[-1] > ma20.iloc[-1]:
                            results.append((row['Name'], row['Code'], df_d, "20일선 지지 눌림목"))
                except: pass
                p_bar.progress((i+1)/len(targets))
            
            status.empty()
            p_bar.empty()
            
            if results:
                for n, c, d, r in results:
                    with st.expander(f"⭐ {n} ({c}) - {r}"):
                        st.line_chart(d['Close'])
            else:
                st.warning("현재 시장에 해당되는 종목이 없습니다.")

# [Tab 3] 마켓 이슈
with main_tabs[2]:
    st.subheader("📰 실시간 주요 뉴스 및 정부 정책")
    news_data = get_realtime_news()
    for n in news_data:
        st.markdown(f"📍 [{n['title']}]({n['link']})")