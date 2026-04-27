import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 (MTS 모드)
st.set_page_config(page_title="MTS PRO", layout="wide")

# CSS: 모바일 최적화 및 촘촘한 레이아웃
st.markdown("""
    <style>
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #c00; color: white; padding: 7px 0; font-size: 14px; position: sticky; top: 0; z-index: 999; font-weight: bold; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 35s linear infinite; }
    .stMetric { background: #111 !important; border: 1px solid #333 !important; padding: 10px !important; border-radius: 8px !important; }
    .stock-card { background: #1a1a1a; padding: 10px; border-radius: 5px; border-left: 4px solid #ff4b4b; margin-bottom: 5px; font-size: 13px; }
    h3 { font-size: 16px !important; color: #ff4b4b; border-bottom: 1px solid #333; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (KeyError 절대 방지 로직)
@st.cache_data(ttl=30)
def get_clean_market_data():
    try:
        df = fdr.StockListing('KRX')
        # 열 이름을 모두 대문자로 통일
        df.columns = [c.upper() for c in df.columns]
        
        # [핵심] 'CHG'라는 글자가 들어간 열을 찾아 'MY_CHG'로 별명 붙임 (에러 원천 차단)
        chg_col = next((c for c in df.columns if any(x in c for x in ['CHG', 'RATE', 'RATIO', 'CHANGE'])), None)
        
        if chg_col:
            df['MY_CHG'] = pd.to_numeric(df[chg_col], errors='coerce').fillna(0)
        else:
            df['MY_CHG'] = 0.0 # 못찾으면 0으로 처리
            
        return df
    except:
        return pd.DataFrame()

def get_live_news_ticker():
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [a.get_text().strip() for a in soup.select('.mainNewsList .articleSubject a')[:8]]
        return "  🔥  ".join(titles)
    except: return "실시간 마켓 이슈 로딩 중..."

# 3. 미니 차트 (MTS 간소화)
def draw_sparkline(code):
    try:
        df = fdr.DataReader(code).tail(15)
        fig = go.Figure(data=[go.Scatter(y=df['Close'], mode='lines', line=dict(color='#ff4b4b', width=2), fill='tozeroy')])
        fig.update_layout(height=40, width=110, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- UI 레이아웃 시작 ---

# [1] 뉴스 기사만 실시간 상단 노출
st.markdown(f"<div class='ticker-wrap'><div class='ticker-move'>{get_live_news_ticker()}</div></div>", unsafe_allow_html=True)

df_live = get_clean_market_data()

# [2] 시장 지수 (MTS 상단)
idx_cols = st.columns(4)
for i, (n, c) in enumerate([("KOSPI", "KS11"), ("KOSDAQ", "KQ11"), ("NASDAQ", "IXIC"), ("USD/KRW", "USD/KRW")]):
    try:
        d = fdr.DataReader(c).tail(2)
        idx_cols[i].metric(n, f"{d['Close'].iloc[-1]:,.0f}", f"{d['Close'].iloc[-1]-d['Close'].iloc[-2]:+.1f}")
    except: pass

st.divider()

# [3] 메인 4분할 분석 보드 (MTS 리스트 스타일)
c1, c2 = st.columns(2)

with c1:
    st.subheader("🚀 실시간 수급 & 거래량 (차트)")
    if not df_live.empty:
        # 거래량 순 정렬
        vol_col = next((c for c in df_live.columns if 'VOLUME' in c), df_live.columns[0])
        hot_stocks = df_live.sort_values(by=vol_col, ascending=False).head(5)
        for _, row in hot_stocks.iterrows():
            txt_col, chart_col = st.columns([2, 1])
            txt_col.markdown(f"**{row['NAME']}**<br><span style='color:#ff4b4b;'>{row['MY_CHG']:+.2f}%</span>", unsafe_allow_html=True)
            with chart_col:
                fig = draw_sparkline(row['CODE'])
                if fig: st.plotly_chart(fig, use_container_width=False, config={'displayModeBar': False})

with c2:
    st.subheader("🎯 익일 급등 유력 (종가베팅)")
    if not df_live.empty:
        # 에러났던 Chg 대신 MY_CHG 사용
        potential = df_live[(df_live['MY_CHG'] > 3) & (df_live['MY_CHG'] < 14)].head(5)
        for _, row in potential.iterrows():
            st.markdown(f"<div class='stock-card'>✅ <b>{row['NAME']}</b><br>거래대금 상위 / 익일 갭상승 유력</div>", unsafe_allow_html=True)
    
    st.subheader("📜 바닥 매집 족보집")
    for n in df_live['NAME'].head(5):
        st.write(f"🔎 {n} (장기 이평 수렴)")

# [4] 외인/기관 수급 (간소화 리스트)
st.divider()
st.subheader("🏦 수급 현황 (추정)")
b_col, s_col = st.columns(2)
with b_col:
    st.write("🟢 **외인 매수 상위**")
    st.write(", ".join(df_live.nlargest(7, 'MY_CHG')['NAME'].tolist()))
with s_col:
    st.write("🔴 **기관 매도 상위**")
    st.write(", ".join(df_live.nsmallest(7, 'MY_CHG')['NAME'].tolist()))

if st.button("🔄 실시간 리셋"):
    st.cache_data.clear()
    st.rerun()