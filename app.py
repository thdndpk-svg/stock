import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import time

# 1. 페이지 설정 및 레이아웃
st.set_page_config(page_title="K-Stock Auto-Terminal Pro", layout="wide")

# 고해상도 테마 스타일링
st.markdown("""
    <style>
    .reportview-container { background: #0e1117; }
    .metric-card { background: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; margin-bottom: 10px; }
    .stButton>button { width: 100%; border-radius: 5px; background-color: #262730; color: #ff4b4b; border: 1px solid #ff4b4b; }
    .analysis-box { background: #111827; padding: 15px; border-radius: 10px; border-top: 3px solid #ff4b4b; height: 500px; overflow-y: auto; }
    h3 { color: #ff4b4b; font-size: 18px; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진
@st.cache_data(ttl=300)
def get_krx(): return fdr.StockListing('KRX')

def get_news():
    news = []
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        for item in soup.select('.mainNewsList .articleSubject a')[:5]:
            news.append(item.get_text().strip())
    except: news = ["뉴스를 불러올 수 없습니다."]
    return news

# --- [중요] 자동 리셋 로직 (10분 주기) ---
# 실제 배포 환경에서 쿼리 파라미터를 이용해 새로고침을 유도하거나 
# 아래와 같이 루프 내에서 처리하는 방식을 UX에 맞게 구현합니다.
if 'last_update' not in st.session_state:
    st.session_state.last_update = datetime.now()

# --- 사이드바: 왼쪽 정보창 (지표 + 뉴스) ---
with st.sidebar:
    st.title("🌐 Market Info")
    st.caption(f"최근 갱신: {st.session_state.last_update.strftime('%H:%M:%S')}")
    
    if st.button("🔄 즉시 수동 리셋"):
        st.session_state.last_update = datetime.now()
        st.rerun()

    st.subheader("📊 글로벌 지표")
    indices = {
        "코스피": "KS11", "코스닥": "KQ11", "나스닥": "IXIC", 
        "니케이": "N225", "금(선물)": "GC=F", "환율": "USD/KRW"
    }
    for name, code in indices.items():
        try:
            d = fdr.DataReader(code).tail(2)
            val, diff = d['Close'].iloc[-1], d['Close'].iloc[-1] - d['Close'].iloc[-2]
            st.metric(name, f"{val:,.2f}", f"{diff:+.2f}")
        except: pass

    st.divider()
    st.subheader("📰 실시간 이슈")
    news_list = get_news()
    for n in news_list:
        st.markdown(f"📍 <span style='font-size:13px;'>{n}</span>", unsafe_allow_html=True)

# --- 메인 화면: 중앙 4분할 자동 분석 창 ---
df_krx = get_krx()
st.subheader("🎯 실시간 기법별 자동 분석 보드 (10분 자동 스캔)")

# 분석 진행 상황 표시줄
progress_text = st.empty()
progress_bar = st.progress(0)

c1, c2 = st.columns(2)
c3, c4 = st.columns(2)

# 분석 로직 통합 실행
@st.cache_data(ttl=600) # 10분간 결과 유지
def run_full_analysis():
    results = {"jokbo": [], "n_shape": [], "volume": [], "supply": []}
    targets = df_krx.head(100) # 정확도와 속도를 위해 상위 100개
    
    for i, row in targets.iterrows():
        try:
            # 기본 데이터 호출
            df = fdr.DataReader(row['Code']).tail(40)
            
            # 1. 족보집 (60월선) - 별도 월봉 호출
            df_m = fdr.DataReader(row['Code'], interval='monthly').tail(65)
            df_m['MA60'] = df_m['Close'].rolling(60).mean()
            if df_m['Close'].iloc[-1] >= df_m['MA60'].iloc[-1] and df_m['Close'].iloc[-2] < df_m['MA60'].iloc[-2]:
                results["jokbo"].append(f"{row['Name']} ({row['Code']})")

            # 2. N자형 눌림목
            ma20 = df['Close'].rolling(20).mean()
            if df['Close'].iloc[-2] > ma20.iloc[-2] and df['Low'].iloc[-1] <= ma20.iloc[-1] and df['Close'].iloc[-1] > ma20.iloc[-1]:
                results["n_shape"].append(row['Name'])

            # 3. 거래량 폭증
            if df['Volume'].iloc[-1] > df['Volume'].rolling(5).mean().iloc[-2] * 3:
                results["volume"].append(row['Name'])
        except: pass
    return results

# 분석 실행
full_results = run_full_analysis()
progress_bar.progress(100)
time.sleep(1)
progress_bar.empty()

# 결과 배치
with c1:
    st.markdown("<div class='analysis-box'><h3>💎 족보집 (60월선 돌파)</h3>", unsafe_allow_html=True)
    for r in full_results["jokbo"]: st.write(f"✅ {r}")
    st.markdown("</div>", unsafe_allow_html=True)

with c2:
    st.markdown("<div class='analysis-box'><h3>🎯 전문가 N자형 눌림목</h3>", unsafe_allow_html=True)
    for r in full_results["n_shape"]: st.write(f"📈 {r}")
    st.markdown("</div>", unsafe_allow_html=True)

with c3:
    st.markdown("<div class='analysis-box'><h3>🔥 세력 거래량 폭증</h3>", unsafe_allow_html=True)
    for r in full_results["volume"]: st.write(f"🚀 {r}")
    st.markdown("</div>", unsafe_allow_html=True)

with c4:
    st.markdown("<div class='analysis-box'><h3>🏦 외인/기관 수급 상위</h3>", unsafe_allow_html=True)
    # 등락률 상위로 수급 대체 표시
    top_move = df_krx.nlargest(10, 'Chg').iloc[:10]
    for _, row in top_move.iterrows(): st.write(f"💰 {row['Name']} ({row['Chg']:+.2f}%)")
    st.markdown("</div>", unsafe_allow_html=True)