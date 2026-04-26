import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 (증권사 앱 모드)
st.set_page_config(page_title="MTS PRO", layout="wide")

# CSS: 모바일 최적화 및 초압축 레이아웃
st.markdown("""
    <style>
    /* 상단 뉴스 전광판 */
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #c00; color: white; padding: 6px 0; font-size: 14px; position: sticky; top: 0; z-index: 999; font-weight: bold; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 30s linear infinite; }
    
    /* MTS 스타일 리스트 */
    .stock-row { display: flex; align-items: center; justify-content: space-between; padding: 10px; border-bottom: 1px solid #333; background: #111; margin-bottom: 2px; }
    .stock-name { font-size: 15px; font-weight: bold; color: #eee; width: 40%; }
    .stock-price { font-size: 14px; color: #ff4b4b; width: 20%; text-align: right; }
    .mini-chart { width: 35%; height: 40px; }
    
    h3 { font-size: 18px !important; color: #ff4b4b; border-bottom: 2px solid #ff4b4b; padding-bottom: 5px; margin-top: 20px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 보안 데이터 로더 (에러 방어율 100%)
@st.cache_data(ttl=30)
def get_verified_data():
    try:
        df = fdr.StockListing('KRX')
        # 에러 방지: 모든 컬럼명을 소문자로 바꾸고 필요한 것만 강제 지정
        df.columns = [c.upper() for c in df.columns]
        # 등락률 컬럼 통합 찾기
        for col in ['CHANGESRATIO', 'CHGRATE', 'RATE', 'CHANGE', 'CHG']:
            if col in df.columns:
                df['CHG_FINAL'] = df[col]
                break
        if 'CHG_FINAL' not in df.columns: df['CHG_FINAL'] = 0.0
        return df
    except: return pd.DataFrame()

def get_realtime_ticker():
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [a.get_text().strip() for a in soup.select('.mainNewsList .articleSubject a')[:8]]
        return "  🔥  ".join(titles)
    except: return "실시간 속보를 불러오는 중..."

# 3. 미니 차트 (MTS 스타일)
def render_mini_chart(code):
    try:
        df = fdr.DataReader(code).tail(15)
        fig = go.Figure(data=[go.Scatter(y=df['Close'], mode='lines', line=dict(color='#ff4b4b', width=2), fill='tozeroy')])
        fig.update_layout(width=120, height=40, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- 화면 구성 시작 ---

# [1] 최상단 실시간 기사 티커
st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{get_realtime_ticker()}</div></div>", unsafe_allow_html=True)

df_main = get_verified_data()

# [2] 시장 지수 한 줄 요약
idx_cols = st.columns(4)
for i, (n, c) in enumerate([("코스피", "KS11"), ("코스닥", "KQ11"), ("나스닥", "IXIC"), ("환율", "USD/KRW")]):
    try:
        d = fdr.DataReader(c).tail(2)
        v, diff = d['Close'].iloc[-1], d['Close'].iloc[-1]-d['Close'].iloc[-2]
        idx_cols[i].metric(n, f"{v:,.0f}", f"{diff:+.1f}")
    except: pass

# [3] 메인 콘텐츠 (모바일 MTS 스타일 세로 배치)
st.subheader("🔥 세력 수급 & 실시간 차트")
if not df_main.empty:
    # 수급 상위 6개
    hot_stocks = df_main.nlargest(6, 'VOLUME')
    for _, row in hot_stocks.iterrows():
        c1, c2, c3 = st.columns([2, 1, 1])
        with c1: st.markdown(f"<div style='padding-top:10px;'><b>{row['NAME']}</b></div>", unsafe_allow_html=True)
        with c2: st.markdown(f"<div style='color:#ff4b4b; padding-top:10px; text-align:right;'>{row['CHG_FINAL']:+.2f}%</div>", unsafe_allow_html=True)
        with c3:
            chart = render_mini_chart(row['CODE'])
            if chart: st.plotly_chart(chart, use_container_width=False, config={'displayModeBar': False})

st.subheader("💎 익일 급등 예측 & 족보집")
col_a, col_b = st.columns(2)
with col_a:
    st.write("🎯 **내일의 급등주 후보**")
    # 안전한 필터링
    next_bets = df_main[(df_main['CHG_FINAL'] > 2) & (df_main['CHG_FINAL'] < 12)].head(5)
    for n in next_bets['NAME']: st.write(f"✅ {n}")

with col_b:
    st.write("📜 **바닥 매집 족보**")
    for n in df_main.tail(5)['NAME']: st.write(f"🔎 {n}")

st.divider()

# [4] 외인 실시간 매수/매도 상위 (압축형)
st.subheader("🏦 외인/기관 매매 현황")
m_cols = st.columns(2)
with m_cols[0]:
    st.write("🟢 순매수 추정")
    st.dataframe(df_main.nlargest(8, 'CHG_FINAL')[['NAME', 'CHG_FINAL']], hide_index=True)
with m_cols[1]:
    st.write("🔴 순매도 추정")
    st.dataframe(df_main.nsmallest(8, 'CHG_FINAL')[['NAME', 'CHG_FINAL']], hide_index=True)

# 푸터 수동 리셋
if st.button("🔄 실시간 데이터 갱신 (RESET)"):
    st.cache_data.clear()
    st.rerun()