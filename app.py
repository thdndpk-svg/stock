import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(page_title="K-Stock Intelligence Terminal", layout="wide")

# 2. 고해상도 다크 UI 스타일링
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 5px; height: 3.5em; background-color: #262730; color: #ff4b4b; border: 1px solid #ff4b4b; font-weight: bold; margin-bottom: 10px; }
    .stButton>button:hover { background-color: #ff4b4b; color: white; }
    .status-box { background-color: #111827; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; }
    .news-card { padding: 10px; border-bottom: 1px solid #374151; font-size: 14px; }
    </style>
    """, unsafe_allow_html=True)

# 3. 데이터 및 뉴스 로드 함수
@st.cache_data(ttl=600)
def get_krx(): return fdr.StockListing('KRX')

def get_news():
    news = []
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.mainNewsList .articleSubject a')[:6]:
            news.append({"title": item.get_text().strip(), "link": "https://finance.naver.com"+item['href']})
    except: news = [{"title": "뉴스 정보를 가져올 수 없습니다.", "link": "#"}]
    return news

df_krx = get_krx()

# --- 사이드바: 기법 선택 및 정보 센터 ---
with st.sidebar:
    st.title("🛠️ 분석 센터")
    st.subheader("📊 기법별 즉시 스캔")
    
    # 각각의 버튼으로 기법 배치
    btn_jokbo = st.button("💎 족보집: 60월선 바닥매집")
    btn_nshape = st.button("🎯 전문가: N자형 눌림목")
    btn_vol = st.button("🔥 세력: 거래량 폭증")
    btn_top = st.button("🏦 외인/기관 수급상위")
    
    st.divider()
    st.subheader("🌍 시장 지표")
    for name, code in [("KOSPI", "KS11"), ("KOSDAQ", "KQ11"), ("나스닥", "IXIC")]:
        try:
            d = fdr.DataReader(code).tail(2)
            st.metric(name, f"{d['Close'].iloc[-1]:,.2f}", f"{d['Close'].iloc[-1]-d['Close'].iloc[-2]:+.2f}")
        except: pass

# --- 메인 화면: 실시간 이슈 및 결과창 ---
col_issue, col_main = st.columns([1, 2.5])

with col_issue:
    st.subheader("📰 실시간 마켓 이슈")
    all_news = get_news()
    for n in all_news:
        st.markdown(f"<div class='news-card'>📍 <a href='{n['link']}' style='color:white;text-decoration:none;'>{n['title']}</a></div>", unsafe_allow_html=True)
    
    st.divider()
    st.subheader("📊 실시간 거래대금 상위")
    st.dataframe(df_krx.nlargest(10, 'Marcap')[['Name', 'Code']], hide_index=True)

with col_main:
    # 어떤 버튼을 눌렀느냐에 따라 분석 시작
    active_strategy = None
    if btn_jokbo: active_strategy = "족보집"
    if btn_nshape: active_strategy = "눌림목"
    if btn_vol: active_strategy = "거래량"
    if btn_top: active_strategy = "수급"

    if active_strategy:
        st.subheader(f"🚀 {active_strategy} 분석 엔진 가동 중...")
        status_area = st.empty()
        progress_bar = st.progress(0)
        result_area = st.container()
        
        results = []
        targets = df_krx.head(150) # 스캔 속도와 정확도 사이의 최적값
        
        for i, row in targets.iterrows():
            status_area.markdown(f"<div class='status-box'>🔍 분석 중: <b>{row['Name']}</b> ({row['Code']})</div>", unsafe_allow_html=True)
            try:
                if active_strategy == "족보집":
                    df_m = fdr.DataReader(row['Code'], interval='monthly').tail(65)
                    df_m['MA60'] = df_m['Close'].rolling(60).mean()
                    if df_m['Close'].iloc[-1] >= df_m['MA60'].iloc[-1] and df_m['Close'].iloc[-2] < df_m['MA60'].iloc[-2]:
                        results.append((row['Name'], row['Code'], df_m, "60월선 골든크로스"))
                
                elif active_strategy == "눌림목":
                    df_d = fdr.DataReader(row['Code']).tail(40)
                    ma20 = df_d['Close'].rolling(20).mean()
                    if df_d['Close'].iloc[-2] > ma20.iloc[-2] and df_d['Low'].iloc[-1] <= ma20.iloc[-1] and df_d['Close'].iloc[-1] > ma20.iloc[-1]:
                        results.append((row['Name'], row['Code'], df_d, "20일선 지지"))
            except: pass
            progress_bar.progress((i+1)/len(targets))
        
        status_area.empty()
        progress_bar.empty()
        
        if results:
            st.success(f"✅ 총 {len(results)}개의 종목을 포착했습니다!")
            for n, c, d, r in results:
                with st.expander(f"⭐ {n} ({c}) - {r}"):
                    fig = go.Figure(data=[go.Candlestick(x=d.index, open=d['Open'], high=d['High'], low=d['Low'], close=d['Close'])])
                    fig.update_layout(xaxis_rangeslider_visible=False, template="plotly_dark", height=300, margin=dict(l=0,r=0,t=0,b=0))
                    st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("조건에 맞는 종목이 현재 시장에 없습니다.")
    else:
        st.info("👈 왼쪽 분석 센터에서 기법 버튼을 눌러 스캔을 시작하세요.")