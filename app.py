import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import time

# 1. 페이지 환경 설정
st.set_page_config(page_title="K-Stock Master v4", layout="wide", initial_sidebar_state="expanded")

# 커스텀 CSS로 UI 디자인 보강
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stMetric { background-color: #1f2937; padding: 15px; border-radius: 10px; border: 1px solid #374151; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #ff4b4b; color: white; }
    </style>
    """, unsafe_allow_html=True)

# 2. 데이터 로드 함수
@st.cache_data(ttl=3600)
def get_krx_list():
    return fdr.StockListing('KRX')

df_krx = get_krx_list()

# --- 사이드바: 시장 현황 ---
with st.sidebar:
    st.header("🌍 Market Index")
    for name, code in [("KOSPI", "KS11"), ("KOSDAQ", "KQ11")]:
        try:
            idx_df = fdr.DataReader(code).tail(2)
            curr_val = idx_df['Close'].iloc[-1]
            diff = curr_val - idx_df['Close'].iloc[-2]
            st.metric(name, f"{curr_val:,.2f}", f"{diff:+.2f}")
        except: st.write(f"{name} 로딩 실패")
    st.divider()
    st.write("⚙️ **설정**")
    scan_count = st.slider("스캔 종목 수", 50, 500, 100)

# --- 메인 화면 ---
st.title("🛡️ K-Stock 실전 투자 시스템")
st.caption("바닥 매집주 기법 및 실시간 급등주 탐색 엔진")

tabs = st.tabs(["💎 바닥 매집주 (족보집)", "🔥 실시간 급등주", "🔍 종목 돋보기"])

# --- Tab 1: 바닥 매집주 (60월선 기법) ---
with tabs[0]:
    st.subheader("60월선 바닥 돌파 및 매집 탐색")
    if st.button("💎 족보집 기법으로 바닥주 찾기"):
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        target_list = df_krx.head(scan_count)
        
        for i, row in target_list.iterrows():
            status_text.text(f"🔍 분석 중: {row['Name']} ({row['Code']})")
            try:
                # 월봉 분석
                df_m = fdr.DataReader(row['Code'], '2018-01-01', interval='monthly')
                if len(df_m) < 60: continue
                df_m['MA60'] = df_m['Close'].rolling(60).mean()
                
                curr = df_m.iloc[-1]
                prev = df_m.iloc[-2]
                
                # 기법 조건: 60월선 돌파 혹은 근접 안착
                is_break = prev['Close'] < prev['MA60'] and curr['Close'] >= curr['MA60']
                is_near = abs(curr['Close'] - curr['MA60']) / curr['MA60'] < 0.03
                
                if is_break or is_near:
                    results.append({'name': row['Name'], 'code': row['Code'], 'df': df_m, 'curr': curr})
            except: continue
            progress_bar.progress((i + 1) / len(target_list))
        
        status_text.empty()
        progress_bar.empty()
        
        if results:
            st.success(f"✅ 기법에 부합하는 종목 {len(results)}개를 찾았습니다.")
            cols = st.columns(2)
            for idx, res in enumerate(results):
                with cols[idx % 2]:
                    with st.container():
                        st.markdown(f"### {res['name']} ({res['code']})")
                        fig = go.Figure()
                        fig.add_trace(go.Candlestick(x=res['df'].index, open=res['df']['Open'], high=res['df']['High'], low=res['df']['Low'], close=res['df']['Close'], name="월봉"))
                        fig.add_trace(go.Scatter(x=res['df'].index, y=res['df']['MA60'], line=dict(color='red', width=3), name="60월선"))
                        fig.update_layout(height=400, xaxis_rangeslider_visible=False, template="plotly_dark", margin=dict(l=0,r=0,t=30,b=0))
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("조건에 맞는 종목이 없습니다. 스캔 범위를 늘려보세요.")

# --- Tab 2: 실시간 급등주 ---
with tabs[1]:
    st.subheader("거래량 동반 단기 급등주")
    if st.button("🔥 실시간 급등 스캔 시작"):
        results = []
        p_bar = st.progress(0)
        s_text = st.empty()
        
        targets = df_krx.head(scan_count)
        for i, row in targets.iterrows():
            s_text.text(f"🚀 실시간 체크: {row['Name']}")
            try:
                df = fdr.DataReader(row['Code']).tail(20)
                curr = df.iloc[-1]
                prev = df.iloc[-2]
                change = ((curr['Close'] - prev['Close']) / prev['Close']) * 100
                
                if change > 4: # 4% 이상 급등 중
                    results.append({'name': row['Name'], 'code': row['Code'], 'change': change, 'price': curr['Close']})
            except: continue
            p_bar.progress((i+1)/len(targets))
            
        s_text.empty()
        p_bar.empty()
        
        if results:
            for res in sorted(results, key=lambda x: x['change'], reverse=True):
                st.info(f"**{res['name']}** ({res['code']}) | 현재가: {res['price']:,}원 | **+{res['change']:.2f}%** 상승 중")
        else:
            st.write("현재 급등 중인 종목이 없습니다.")

# --- Tab 3: 종목 돋보기 (검색) ---
with tabs[2]:
    search_stock = st.selectbox("종목명을 입력하세요", df_krx['Name'].tolist())
    if search_stock:
        code = df_krx[df_krx['Name'] == search_stock]['Code'].values[0]
        data = fdr.DataReader(code).tail(120)
        st.subheader(f"🔍 {search_stock} 상세 분석")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("현재가", f"{data['Close'].iloc[-1]:,}원")
        c2.metric("거래량", f"{data['Volume'].iloc[-1]:,}")
        c3.metric("최고가(120일)", f"{data['High'].max():,}원")
        
        st.line_chart(data['Close'])