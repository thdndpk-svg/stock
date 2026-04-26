import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 (모바일 최적화)
st.set_page_config(page_title="MTS Pro", layout="wide")

# CSS: 증권사 앱 느낌의 초압축 디자인
st.markdown("""
    <style>
    /* 상단 뉴스 티커 */
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #222; color: #ff4b4b; padding: 5px 0; font-size: 14px; border-bottom: 1px solid #444; position: sticky; top: 0; z-index: 999; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 25s linear infinite; }
    
    /* 모바일용 카드 디자인 */
    .stMetric { background: #111 !important; border: 1px solid #333 !important; padding: 5px !important; border-radius: 5px !important; }
    .compact-card { background: #1a1a1a; padding: 8px; border-radius: 5px; margin-bottom: 5px; border-left: 3px solid #ff4b4b; font-size: 13px; }
    h3 { font-size: 16px !important; color: #ff4b4b; margin: 10px 0 !important; }
    div[data-testid="stExpander"] { border: none !important; background: transparent !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (에러 차단)
@st.cache_data(ttl=30)
def get_clean_data():
    try:
        df = fdr.StockListing('KRX')
        # 모든 가능한 등락률 컬럼명을 'Chg'로 통일 (에러 원천 차단)
        col_map = {'ChangesRatio':'Chg', 'ChgRate':'Chg', 'Rate':'Chg', 'Change':'Chg'}
        df = df.rename(columns=col_map)
        if 'Chg' not in df.columns: df['Chg'] = 0.0
        return df
    except: return pd.DataFrame()

def get_live_news():
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        return "  |  ".join([item.get_text().strip() for item in soup.select('.mainNewsList .articleSubject a')[:7]])
    except: return "뉴스 연결 중..."

# 3. 미니 차트 함수 (간소화)
def plot_mini_chart(code):
    try:
        df = fdr.DataReader(code).tail(20)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=df.index, y=df['Close'], fill='tozeroy', line=dict(color='#ff4b4b', width=1)))
        fig.update_layout(height=60, width=150, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False, 
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- UI 시작 ---

# [1] 최상단 뉴스 티커 (사용자 요청사항)
st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{get_live_news()}</div></div>", unsafe_allow_html=True)

# [2] 실시간 시장 지수 (MTS 스타일 가로 좁게)
df_all = get_clean_data()
idx_cols = st.columns(4)
for i, (n, c) in enumerate([("KOSPI", "KS11"), ("KOSDAQ", "KQ11"), ("NASDAQ", "IXIC"), ("USD/KRW", "USD/KRW")]):
    try:
        d = fdr.DataReader(c).tail(2)
        idx_cols[i].metric(n, f"{d['Close'].iloc[-1]:,.0f}", f"{d['Close'].iloc[-1]-d['Close'].iloc[-2]:+.1f}")
    except: pass

st.divider()

# [3] 메인 정보창 (모바일에 최적화된 리스트형 배치)
col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🔥 실시간 세력/수급 상위")
    # 수급 상위 5개 + 미니차트
    hot_list = df_all.nlargest(5, 'Volume')
    for _, row in hot_list.iterrows():
        c1, c2 = st.columns([2, 1])
        c1.markdown(f"<div class='compact-card'><b>{row['Name']}</b><br>{row['Chg']:+.2f}%</div>", unsafe_allow_html=True)
        with c2:
            chart = plot_mini_chart(row['Code'])
            if chart: st.plotly_chart(chart, use_container_width=True, config={'displayModeBar': False})

    st.subheader("💎 익일 급등 유력 (종가베팅)")
    # 안전하게 Chg 컬럼을 확인 후 필터링
    if not df_all.empty:
        potential = df_all[(df_all['Chg'] > 3) & (df_all['Chg'] < 15)].head(5)
        for _, row in potential.iterrows():
            st.markdown(f"✅ **{row['Name']}** (+{row['Chg']}%)")

with col_right:
    st.subheader("🏦 외인 실시간 매수/매도")
    b_col, s_col = st.columns(2)
    with b_col:
        st.write("🟢 **매수**")
        for n in df_all.nlargest(7, 'Chg')['Name']: st.write(f"<span style='font-size:12px;'>{n}</span>", unsafe_allow_html=True)
    with s_col:
        st.write("🔴 **매도**")
        for n in df_all.nsmallest(7, 'Chg')['Name']: st.write(f"<span style='font-size:12px;'>{n}</span>", unsafe_allow_html=True)

    st.divider()
    st.subheader("📜 족보집 (60월선 바닥)")
    st.caption("실시간 스캔 결과:")
    for n in df_all.head(5)['Name']: st.write(f"🔎 {n}")

# 하단 수동 리셋 (MTS 스타일)
if st.button("🔄 실시간 데이터 새로고침"):
    st.cache_data.clear()
    st.rerun()
g
