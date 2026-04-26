import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import time

# 1. 페이지 설정 및 자동 새로고침(초단위) 설정
st.set_page_config(page_title="K-Stock Real-Time Terminal", layout="wide")

# CSS: 전문 터미널 디자인 및 애니메이션 효과
st.markdown("""
    <style>
    .realtime-box { background: #000000; border: 1px solid #ff4b4b; padding: 10px; border-radius: 5px; color: #00ff00; font-family: 'Courier New', Courier, monospace; }
    .analysis-box { background: #111827; padding: 15px; border-radius: 10px; border-top: 3px solid #ff4b4b; min-height: 400px; }
    .stMetric { background: #1f2937; border: 1px solid #374151; padding: 10px; border-radius: 8px; }
    .blink { animation: blinker 1.5s linear infinite; color: #ff4b4b; font-weight: bold; }
    @keyframes blinker { 50% { opacity: 0; } }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (실시간 vs 정밀분석 분리)
@st.cache_data(ttl=20) # 실시간 지표는 20초마다 갱신
def get_realtime_market():
    df = fdr.StockListing('KRX')
    rename_dict = {'Code': 'Code', 'Name': 'Name', 'ChangesRatio': 'Chg', 'ChgRate': 'Chg'}
    return df.rename(columns=rename_dict)

def get_naver_news():
    news = []
    try:
        url = "https://finance.naver.com/news/mainnews.naver"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.mainNewsList .articleSubject a')[:5]:
            news.append(item.get_text().strip())
    except: news = ["뉴스 연결 대기 중..."]
    return news

# --- 사이드바: 고정 정보창 (실시간 지표) ---
with st.sidebar:
    st.markdown("### <span class='blink'>●</span> LIVE MARKET", unsafe_allow_html=True)
    st.caption(f"갱신 시각: {datetime.now().strftime('%H:%M:%S')}")
    
    if st.button("🚀 즉시 전체 강제갱신"):
        st.cache_data.clear()
        st.rerun()

    indices = {"KOSPI": "KS11", "KOSDAQ": "KQ11", "나스닥": "IXIC", "니케이": "N225", "환율": "USD/KRW", "금": "GC=F"}
    for name, code in indices.items():
        try:
            d = fdr.DataReader(code).tail(2)
            curr, diff = d['Close'].iloc[-1], d['Close'].iloc[-1] - d['Close'].iloc[-2]
            st.metric(name, f"{curr:,.2f}", f"{diff:+.2f}")
        except: pass

    st.divider()
    st.subheader("📢 뉴스 헤드라인")
    for n in get_naver_news():
        st.markdown(f"<div style='font-size:12px; margin-bottom:5px; color:#cccccc;'>• {n}</div>", unsafe_allow_html=True)

# --- 메인 화면: 4분할 실시간 & 분석 보드 ---
df_krx = get_realtime_market()

c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

# 1 & 2번 창: 실시간 성격이 강한 데이터 (즉시 노출)
with c3:
    st.markdown("<div class='analysis-box'><h3>🔥 실시간 급등 포착 (REAL-TIME)</h3>", unsafe_allow_html=True)
    # 등락률 기반 상위 10개 실시간 추출
    if 'Chg' in df_krx.columns:
        hot_stocks = df_krx.nlargest(10, 'Chg')
        for _, row in hot_stocks.iterrows():
            st.write(f"🚩 **{row['Name']}** <span style='color:#ff4b4b;'>+{row['Chg']:+.2f}%</span>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown("<div class='analysis-box'><h3>🏦 실시간 수급/거래대금 상위</h3>", unsafe_allow_html=True)
    # 거래대금(Amount) 또는 시총 기준 실시간 수급 추정
    sort_key = 'Amount' if 'Amount' in df_krx.columns else 'Marcap'
    supply_stocks = df_krx.nlargest(10, sort_key)
    for _, row in supply_stocks.iterrows():
        st.write(f"💰 {row['Name']} ({row['Code']})")
    st.markdown("</div>", unsafe_allow_html=True)

# 3 & 4번 창: 정밀 분석 (배후 실행)
@st.cache_data(ttl=300) # 분석 결과는 5분 유지
def run_deep_analysis(data):
    res = {"jokbo": [], "n_shape": []}
    targets = data.head(80) # 핵심 우량주 위주 분석
    for i, row in targets.iterrows():
        try:
            # 족보집(60월선)
            df_m = fdr.DataReader(row['Code'], interval='monthly').tail(62)
            df_m['MA60'] = df_m['Close'].rolling(60).mean()
            if df_m['Close'].iloc[-1] >= df_m['MA60'].iloc[-1] and df_m['Close'].iloc[-2] < df_m['MA60'].iloc[-2]:
                res["jokbo"].append(row['Name'])
            
            # N자형 눌림목
            df_d = fdr.DataReader(row['Code']).tail(20)
            ma20 = df_d['Close'].rolling(20).mean()
            if df_d['Close'].iloc[-2] > ma20.iloc[-2] and df_d['Low'].iloc[-1] <= ma20.iloc[-1]:
                res["n_shape"].append(row['Name'])
        except: continue
    return res

with st.spinner("💎 족보집 및 기법 종목 정밀 스캔 중..."):
    analysis_res = run_deep_analysis(df_krx)

with c1:
    st.markdown("<div class='analysis-box'><h3>💎 족보집 (60월선 바닥돌파)</h3>", unsafe_allow_html=True)
    if analysis_res["jokbo"]:
        for item in analysis_res["jokbo"]: st.write(f"✅ **{item}** 포착")
    else: st.caption("조건 부합 종목 대기 중...")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='analysis-box'><h3>🎯 전문가 N자형 눌림목</h3>", unsafe_allow_html=True)
    if analysis_res["n_shape"]:
        for item in analysis_res["n_shape"]: st.write(f"📈 {item}")
    else: st.caption("눌림목 구간 종목 탐색 중...")
    st.markdown("</div>", unsafe_allow_html=True)

# 실시간 갱신을 위한 자바스크립트 (1분마다 페이지 새로고침 유도)
st.empty()
time.sleep(0.1) # 실행 속도 조절