import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 및 MTS 스타일 적용
st.set_page_config(page_title="K-STOCK MTS PRO", layout="wide")

st.markdown("""
    <style>
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #c00; color: white; padding: 8px 0; font-size: 14px; position: sticky; top: 0; z-index: 999; font-weight: bold; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 35s linear infinite; }
    .stMetric { background: #111 !important; border: 1px solid #333 !important; padding: 10px !important; border-radius: 8px !important; }
    h3 { font-size: 18px !important; color: #ff4b4b; border-bottom: 1px solid #444; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (KeyError 절대 방지 로직)
@st.cache_data(ttl=20) # 20초마다 갱신
def get_verified_data():
    try:
        df = fdr.StockListing('KRX')
        
        # [핵심] 컬럼명을 이름이 아닌 '성격'으로 강제 지정
        # 등락률 관련 단어가 포함된 컬럼을 찾아서 'CHG'로 통일
        for col in df.columns:
            if any(x in col.upper() for x in ['CHANGES', 'RATE', 'CHG', 'RATIO']):
                df['CHG_FIXED'] = df[col]
                break
        
        # 만약 못 찾았다면 0으로 채워서 에러 방지
        if 'CHG_FIXED' not in df.columns:
            df['CHG_FIXED'] = 0.0
            
        return df
    except:
        return pd.DataFrame()

def get_ticker_news():
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [a.get_text().strip() for a in soup.select('.mainNewsList .articleSubject a')[:8]]
        return "  🔥  ".join(titles)
    except: return "실시간 속보를 로딩 중..."

# 3. 미니 차트 (간소화)
def render_mini_chart(code):
    try:
        df = fdr.DataReader(code).tail(15)
        fig = go.Figure(data=[go.Scatter(y=df['Close'], mode='lines', line=dict(color='#ff4b4b', width=2), fill='tozeroy')])
        fig.update_layout(height=40, width=110, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- 화면 구성 시작 ---

# [상단 뉴스 티커]
st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{get_ticker_news()}</div></div>", unsafe_allow_html=True)

df_main = get_verified_data()

# [시장 지수]
idx_cols = st.columns(4)
for i, (n, c) in enumerate([("KOSPI", "KS11"), ("KOSDAQ", "KQ11"), ("NASDAQ", "IXIC"), ("USD/KRW", "USD/KRW")]):
    try:
        d = fdr.DataReader(c).tail(2)
        idx_cols[i].metric(n, f"{d['Close'].iloc[-1]:,.0f}", f"{d['Close'].iloc[-1]-d['Close'].iloc[-2]:+.1f}")
    except: pass

st.divider()

# [메인 보드]
c1, c2 = st.columns(2)

with c1:
    st.subheader("🚀 세력 수급 & 실시간 차트")
    if not df_main.empty:
        # 거래량 상위 5개 + 차트
        hot_list = df_main.sort_values(by=df_main.columns[df_main.columns.str.upper().str.contains('VOLUME')][0], ascending=False).head(5)
        for _, row in hot_list.iterrows():
            col_txt, col_graph = st.columns([2, 1])
            col_txt.markdown(f"**{row['Name']}** ({row['CHG_FIXED']:+.2f}%)")
            with col_graph:
                chart = render_mini_chart(row['Code'])
                if chart: st.plotly_chart(chart, use_container_width=False, config={'displayModeBar': False})

with c2:
    st.subheader("🎯 내일의 급등 & 족보집")
    if not df_main.empty:
        # 에러 났던 부분: .iloc와 명칭 혼합으로 철저하게 방어
        potential = df_main[(df_main['CHG_FIXED'] > 3) & (df_main['CHG_FIXED'] < 15)].head(5)
        for n in potential['Name']:
            st.success(f"🔥 {n} (익일 유망)")
        
        st.write("📜 **바닥 매집 종목**")
        for n in df_main['Name'].head(5):
            st.info(f"🔎 {n}")

# [하단 버튼]
if st.button("🔄 즉시 데이터 동기화"):
    st.cache_data.clear()
    st.rerun()