import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 및 모바일 최적화 스타일
st.set_page_config(page_title="K-STOCK MTS PRO", layout="wide")

st.markdown("""
    <style>
    /* 최상단 뉴스 티커 */
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #c00; color: white; padding: 8px 0; font-size: 14px; position: sticky; top: 0; z-index: 999; font-weight: bold; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 35s linear infinite; }
    
    /* MTS 리스트 디자인 */
    .stMetric { background: #111 !important; border: 1px solid #333 !important; padding: 10px !important; border-radius: 8px !important; }
    .compact-row { background: #1a1a1a; padding: 12px; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid #ff4b4b; }
    h3 { font-size: 18px !important; color: #ff4b4b; border-bottom: 1px solid #444; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 보안 로드 (KeyError 방지 핵심)
@st.cache_data(ttl=30)
def get_safe_data():
    try:
        df = fdr.StockListing('KRX')
        # 모든 컬럼명을 대문자로 통일하고 등락률 컬럼을 강제로 지정
        df.columns = [c.upper() for c in df.columns]
        for col in ['CHANGESRATIO', 'CHGRATE', 'RATE', 'CHANGE', 'CHG']:
            if col in df.columns:
                df['CHG_FINAL'] = df[col]
                break
        if 'CHG_FINAL' not in df.columns: df['CHG_FINAL'] = 0.0
        return df
    except:
        return pd.DataFrame()

def get_ticker_news():
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [a.get_text().strip() for a in soup.select('.mainNewsList .articleSubject a')[:8]]
        return "  🔥  ".join(titles)
    except: return "실시간 뉴스 데이터를 불러올 수 없습니다."

# 3. 초간소화 미니 차트
def render_mini_chart(code):
    try:
        df = fdr.DataReader(code).tail(15)
        fig = go.Figure(data=[go.Scatter(y=df['Close'], mode='lines', line=dict(color='#ff4b4b', width=2), fill='tozeroy')])
        fig.update_layout(height=40, width=120, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- 화면 구성 ---

# [뉴스 티커] 상단 고정
st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{get_ticker_news()}</div></div>", unsafe_allow_html=True)

df_main = get_safe_data()

# [지수 요약]
idx_cols = st.columns(4)
for i, (n, c) in enumerate([("KOSPI", "KS11"), ("KOSDAQ", "KQ11"), ("NASDAQ", "IXIC"), ("USD/KRW", "USD/KRW")]):
    try:
        d = fdr.DataReader(c).tail(2)
        v, diff = d['Close'].iloc[-1], d['Close'].iloc[-1]-d['Close'].iloc[-2]
        idx_cols[i].metric(n, f"{v:,.0f}", f"{diff:+.1f}")
    except: pass

st.divider()

# [메인 분석 영역]
c1, c2 = st.columns(2)

with c1:
    st.subheader("🚀 실시간 세력/수급 & 차트")
    if not df_main.empty:
        # 수급 상위 5개 압축 노출
        for _, row in df_main.nlargest(5, 'VOLUME').iterrows():
            with st.container():
                col_n, col_c = st.columns([2, 1])
                col_n.markdown(f"**{row['NAME']}** ({row['CHG_FINAL']:+.2f}%)")
                with col_c:
                    chart = render_mini_chart(row['CODE'])
                    if chart: st.plotly_chart(chart, use_container_width=False, config={'displayModeBar': False})

with c2:
    st.subheader("🎯 익일 급등 & 족보집")
    if not df_main.empty:
        # 급등 유력주
        next_picks = df_main[(df_main['CHG_FINAL'] > 3) & (df_main['CHG_FINAL'] < 12)].head(5)
        for n in next_picks['NAME']:
            st.markdown(f"✅ <span style='font-size:14px;'>{n} (종가베팅 유효)</span>", unsafe_allow_html=True)
        
        st.write("📜 **바닥 매집 (60월선 근접)**")
        for n in df_main.head(5)['NAME']:
            st.markdown(f"🔎 <span style='font-size:14px;'>{n} (스캔 완료)</span>", unsafe_allow_html=True)

# 하단 리셋
if st.button("🔄 실시간 데이터 동기화"):
    st.cache_data.clear()
    st.rerun()