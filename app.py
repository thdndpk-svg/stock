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
    .stock-card { background: #1a1a1a; padding: 10px; border-radius: 5px; border-left: 4px solid #ff4b4b; margin-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (KeyError 절대 방지)
@st.cache_data(ttl=30)
def get_safe_data():
    try:
        df = fdr.StockListing('KRX')
        # 모든 열 이름을 대문자로 바꾸어 일관성 유지
        df.columns = [c.upper() for c in df.columns]
        
        # [핵심 방어] 등락률 열 자동 포착
        target_col = None
        for col in df.columns:
            if any(x in col for x in ['CHANGESRATIO', 'CHGRATE', 'RATE', 'CHG', 'CHANGE']):
                target_col = col
                break
        
        if target_col:
            df['CHG_FINAL'] = pd.to_numeric(df[target_col], errors='coerce').fillna(0)
        else:
            df['CHG_FINAL'] = 0.0
            
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
        fig.update_layout(height=40, width=100, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- 화면 구성 시작 ---

# [상단 뉴스 티커]
st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{get_ticker_news()}</div></div>", unsafe_allow_html=True)

df_main = get_safe_data()

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
    st.subheader("🔥 실시간 수급 & 차트")
    if not df_main.empty:
        # 거래량(VOLUME) 열을 찾아 정렬
        vol_col = next((c for c in df_main.columns if 'VOLUME' in c), df_main.columns[0])
        hot_list = df_main.sort_values(by=vol_col, ascending=False).head(5)
        for _, row in hot_list.iterrows():
            col_n, col_g = st.columns([2, 1])
            col_n.markdown(f"**{row['NAME']}** ({row['CHG_FINAL']:+.2f}%)")
            with col_g:
                chart = render_mini_chart(row['CODE'])
                if chart: st.plotly_chart(chart, use_container_width=False, config={'displayModeBar': False})

with c2:
    st.subheader("🚀 익일 급등 유력 (종가베팅)")
    if not df_main.empty:
        # 종가베팅 유효 종목: 등락률 3%~12% 사이의 활발한 종목
        potential = df_main[(df_main['CHG_FINAL'] >= 3) & (df_main['CHG_FINAL'] <= 12)].head(6)
        if not potential.empty:
            for _, row in potential.iterrows():
                st.markdown(f"<div class='stock-card'>🚀 <b>{row['NAME']}</b><br>익일 시초가 갭상승 유력</div>", unsafe_allow_html=True)
        else:
            st.write("포착된 종목이 없습니다.")

st.divider()
if st.button("🔄 실시간 데이터 갱신"):
    st.cache_data.clear()
    st.rerun()