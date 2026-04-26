import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup

# 1. 페이지 설정
st.set_page_config(page_title="K-Stock Intelligence Hub", layout="wide")

# 2. 실시간 뉴스 크롤링 함수 (네이버 경제 뉴스 기반)
def get_realtime_news():
    news_list = []
    try:
        url = "https://finance.naver.com/news/mainnews.naver"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        items = soup.select('.mainNewsList .articleSubject a')
        for item in items[:8]: # 최신 뉴스 8개
            news_list.append({"title": item.get_text().strip(), "link": "https://finance.naver.com" + item['href']})
    except:
        news_list.append({"title": "뉴스를 불러올 수 없습니다.", "link": "#"})
    return news_list

# --- 상단 전광판 (해외 및 국내 지표) ---
st.markdown("### 🌍 Global Market Dashboard")
cols = st.columns(5)

indices = {
    "KOSPI": "KS11", "KOSDAQ": "KQ11", 
    "나스닥": "IXIC", "S&P500": "US500", "환율(USD/KRW)": "USD/KRW"
}

for i, (name, code) in enumerate(indices.items()):
    try:
        idx_df = fdr.DataReader(code).tail(2)
        curr = idx_df['Close'].iloc[-1]
        prev = idx_df['Close'].iloc[-2]
        change = curr - prev
        cols[i].metric(name, f"{curr:,.2f}", f"{change:+.2f}")
    except:
        cols[i].write(f"{name} 로딩중...")

st.divider()

# --- 메인 레이아웃 (뉴스 vs 분석) ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("📰 실시간 핵심 이슈")
    news = get_realtime_news()
    for n in news:
        st.markdown(f"📍 [{n['title']}]({n['link']})")
    
    st.divider()
    st.info("💡 정부 정책이나 해외 이슈는 뉴스 제목을 통해 즉시 확인하세요.")

with col_right:
    st.subheader("🎯 전략별 종목 탐색")
    tabs = st.tabs(["💎 족보집 바닥주", "🔥 전문가 눌림목"])
    
    # --- 바닥주 로직 (생략 - 이전 버전과 동일하게 배치) ---
    with tabs[0]:
        if st.button("바닥 매집주 스캔"):
            st.write("분석 엔진 가동 중...")
            # (여기에 이전 60월선 분석 코드 삽입)

    with tabs[1]:
        if st.button("전문가 기법 스캔"):
            st.write("수급 및 N자형 패턴 분석 중...")
            # (여기에 이전 전문가 전략 코드 삽입)