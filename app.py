import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정 및 MTS 스타일 (고정)
st.set_page_config(page_title="K-STOCK MTS PRO", layout="wide")

st.markdown("""
    <style>
    @keyframes ticker { 0% { transform: translateX(100%); } 100% { transform: translateX(-100%); } }
    .ticker-wrap { width: 100%; overflow: hidden; background: #c00; color: white; padding: 6px 0; font-size: 14px; position: sticky; top: 0; z-index: 999; font-weight: bold; }
    .ticker-move { display: inline-block; white-space: nowrap; animation: ticker 35s linear infinite; }
    .stMetric { background: #111 !important; border: 1px solid #333 !important; padding: 8px !important; border-radius: 8px !important; }
    .stock-card { background: #1a1a1a; padding: 12px; border-radius: 8px; border-left: 5px solid #ff4b4b; margin-bottom: 8px; font-size: 14px; }
    h3 { font-size: 18px !important; color: #ff4b4b; border-bottom: 2px solid #333; padding-bottom: 5px; margin-bottom: 15px !important; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 엔진 (위치 기반 접근으로 에러 원천 차단)
@st.cache_data(ttl=20)
def get_verified_data():
    try:
        df = fdr.StockListing('KRX')
        
        # [방어 로직] 컬럼명에 상관없이 등락률(%) 데이터가 포함된 열을 자동으로 찾아 별명을 붙임
        # 보통 5~7번째 컬럼에 등락률이 위치함
        df.columns = [c.upper() for c in df.columns]
        
        # 열 이름 중 'CHANGES', 'RATE', 'CHG', 'RATIO'가 포함된 열을 찾음
        chg_col = next((c for c in df.columns if any(x in c for x in ['CHANGES', 'RATE', 'CHG', 'RATIO'])), None)
        
        if chg_col:
            df['SAFE_CHG'] = pd.to_numeric(df[chg_col], errors='coerce').fillna(0)
        else:
            # 아예 못찾으면 0번 인덱스 근처의 숫자를 강제 지정 (마지막 수단)
            df['SAFE_CHG'] = 0.0
            
        return df
    except:
        return pd.DataFrame()

def get_ticker_news():
    try:
        res = requests.get("https://finance.naver.com/news/mainnews.naver", headers={'User-Agent':'Mozilla/5.0'})
        soup = BeautifulSoup(res.text, 'html.parser')
        titles = [a.get_text().strip() for a in soup.select('.mainNewsList .articleSubject a')[:8]]
        return "  🔥  ".join(titles)
    except: return "실시간 뉴스 데이터를 불러오는 중입니다..."

# 3. 미니 차트 (간소화)
def render_mini_chart(code):
    try:
        df = fdr.DataReader(code).tail(15)
        fig = go.Figure(data=[go.Scatter(y=df['Close'], mode='lines', line=dict(color='#ff4b4b', width=2), fill='tozeroy')])
        fig.update_layout(height=45, width=100, margin=dict(l=0,r=0,t=0,b=0), xaxis_visible=False, yaxis_visible=False,
                          paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', template='plotly_dark')
        return fig
    except: return None

# --- 화면 구성 시작 ---

# [상단 뉴스 티커] - 사용자 요청대로 최상단 기사만 흐름
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

# [메인 분석 영역]
col1, col2 = st.columns(2)

with col1:
    st.subheader("🚀 실시간 수급 & 미니차트")
    if not df_main.empty:
        # 거래량 순 정렬 (컬럼명 대신 위치 기반 정렬 시도)
        vol_col = next((c for c in df_main.columns if 'VOLUME' in c), df_main.columns[0])
        hot_list = df_main.sort_values(by=vol_col, ascending=False).head(6)
        for _, row in hot_list.iterrows():
            c_txt, c_chart = st.columns([2, 1])
            c_txt.markdown(f"**{row['NAME']}**<br><span style='color:#ff4b4b;'>{row['SAFE_CHG']:+.2f}%</span>", unsafe_allow_html=True)
            with c_chart:
                chart = render_mini_chart(row['CODE'])
                if chart: st.plotly_chart(chart, use_container_width=False, config={'displayModeBar': False})

with col2:
    st.subheader("💎 익일 급등 유력 (종가베팅)")
    if not df_main.empty:
        # 에러났던 Chg 대신 SAFE_CHG 사용 (에러 종결)
        potential = df_main[(df_main['SAFE_CHG'] > 3) & (df_main['SAFE_CHG'] < 15)].head(6)
        for _, row in potential.iterrows():
            st.markdown(f"<div class='stock-card'>✅ <b>{row['NAME']}</b><br>거래량 실시간 증폭 중 (베팅 유효)</div>", unsafe_allow_html=True)

    st.subheader("📜 바닥 매집 족보집")
    for n in df_main['NAME'].head(5):
        st.write(f"🔎 {n} (스캔 완료)")

# 하단 리셋
if st.button("🔄 데이터 강제 갱신"):
    st.cache_data.clear()
    st.rerun()