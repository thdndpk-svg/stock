import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings('ignore')

# ═══════════════════════════════════════════════════════════════════
# 페이지 설정
# ═══════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="세력추적 PRO",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ═══════════════════════════════════════════════════════════════════
# 글로벌 CSS
# ═══════════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;700;900&family=JetBrains+Mono:wght@400;600;700&display=swap');

:root {
  --bg:       #07090f;
  --bg2:      #0d1118;
  --bg3:      #121820;
  --border:   #1e2636;
  --border2:  #2a3550;
  --text:     #dce6f5;
  --muted:    #4a6080;
  --red:      #ff2d2d;
  --red2:     #ff6044;
  --blue:     #1a8cff;
  --blue2:    #44b4ff;
  --gold:     #ffb400;
  --green:    #00d46a;
  --purple:   #9966ff;
}

html, body, [data-testid="stAppViewContainer"],
[data-testid="stApp"], .main { background: var(--bg) !important; }

[data-testid="stHeader"]  { display: none !important; }
[data-testid="stSidebar"] { display: none !important; }
[data-testid="stToolbar"] { display: none !important; }
footer { display: none !important; }

.block-container {
    padding: 0 !important;
    max-width: 100% !important;
}

/* ── 뉴스 티커 ── */
@keyframes ticker {
  0%   { transform: translateX(100vw); }
  100% { transform: translateX(-100%); }
}
.ticker-wrap {
  width: 100%;
  overflow: hidden;
  background: #0a0204;
  border-bottom: 1px solid rgba(255,45,45,.25);
  padding: 7px 0;
  position: sticky;
  top: 0;
  z-index: 9999;
}
.ticker-inner {
  display: inline-block;
  white-space: nowrap;
  animation: ticker 45s linear infinite;
  font-size: 12.5px;
  font-weight: 700;
  color: #ff6044;
  font-family: 'Noto Sans KR', sans-serif;
  letter-spacing: .3px;
}

/* ── 헤더 ── */
.app-header {
  background: linear-gradient(180deg,#0d1118 0%,#07090f 100%);
  border-bottom: 1px solid var(--border);
  padding: 14px 28px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.logo {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.logo-main {
  font-family: 'Noto Sans KR', sans-serif;
  font-size: 22px;
  font-weight: 900;
  color: #fff;
  letter-spacing: -1px;
}
.logo-main em { color: var(--red); font-style: normal; }
.logo-sub {
  font-size: 11px;
  font-weight: 700;
  color: var(--muted);
  letter-spacing: 2px;
  text-transform: uppercase;
}
.header-right {
  display: flex;
  align-items: center;
  gap: 20px;
}
.market-status {
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 4px;
}
.mst-open  { background: rgba(0,212,106,.12); color: var(--green); border: 1px solid rgba(0,212,106,.25); }
.mst-close { background: rgba(74,96,128,.12); color: var(--muted); border: 1px solid rgba(74,96,128,.25); }
.header-time {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  color: var(--muted);
}

/* ── 지수 바 ── */
.index-strip {
  background: var(--bg2);
  border-bottom: 1px solid var(--border);
  padding: 10px 28px;
  display: flex;
  gap: 40px;
  overflow-x: auto;
}
.index-strip::-webkit-scrollbar { display: none; }
.idx-block { display: flex; flex-direction: column; gap: 2px; flex-shrink: 0; }
.idx-label { font-size: 10px; font-weight: 700; color: var(--muted); letter-spacing: 1.5px; text-transform: uppercase; }
.idx-value { font-family: 'JetBrains Mono', monospace; font-size: 19px; font-weight: 700; }
.idx-change { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; }
.c-up   { color: var(--red); }
.c-down { color: var(--blue); }
.c-flat { color: var(--muted); }

/* ── 탭 ── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--bg2) !important;
  border-bottom: 1px solid var(--border) !important;
  gap: 0 !important;
  padding: 0 20px !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  color: var(--muted) !important;
  font-weight: 700 !important;
  font-size: 13px !important;
  padding: 13px 18px !important;
  border-bottom: 2px solid transparent !important;
  border-radius: 0 !important;
  font-family: 'Noto Sans KR', sans-serif !important;
}
.stTabs [aria-selected="true"] {
  color: #fff !important;
  border-bottom-color: var(--red) !important;
}
.stTabs [data-baseweb="tab-panel"] {
  background: var(--bg) !important;
  padding: 20px 24px !important;
}

/* ── 종목 카드 ── */
.s-card {
  background: var(--bg2);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 14px 16px;
  margin-bottom: 8px;
  transition: border-color .15s, background .15s;
  cursor: default;
}
.s-card:hover { border-color: var(--border2); background: var(--bg3); }
.sc-row1 { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 8px; }
.sc-name { font-size: 14px; font-weight: 700; color: var(--text); }
.sc-code { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--muted); margin-top: 2px; }
.sc-price { font-family: 'JetBrains Mono', monospace; font-size: 18px; font-weight: 700; text-align: right; }
.sc-chg   { font-family: 'JetBrains Mono', monospace; font-size: 11px; font-weight: 600; text-align: right; margin-top: 2px; }
.sc-row2  { display: flex; gap: 8px; flex-wrap: wrap; }

/* ── 뱃지 ── */
.badge {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 7px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  font-family: 'Noto Sans KR', sans-serif;
}
.b-red    { background: rgba(255,45,45,.12);  color: var(--red);    border: 1px solid rgba(255,45,45,.25); }
.b-blue   { background: rgba(26,140,255,.12); color: var(--blue);   border: 1px solid rgba(26,140,255,.25); }
.b-gold   { background: rgba(255,180,0,.12);  color: var(--gold);   border: 1px solid rgba(255,180,0,.25); }
.b-green  { background: rgba(0,212,106,.12);  color: var(--green);  border: 1px solid rgba(0,212,106,.25); }
.b-purple { background: rgba(153,102,255,.12);color: var(--purple); border: 1px solid rgba(153,102,255,.25); }
.b-muted  { background: rgba(74,96,128,.12);  color: var(--muted);  border: 1px solid rgba(74,96,128,.2); }

/* ── 섹션 타이틀 ── */
.sec-title {
  font-size: 11px;
  font-weight: 900;
  color: var(--muted);
  letter-spacing: 2.5px;
  text-transform: uppercase;
  padding-bottom: 10px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
}
.sec-title b { color: var(--text); }

/* ── 설명 박스 ── */
.desc-box {
  background: linear-gradient(135deg, var(--bg2), var(--bg3));
  border: 1px solid var(--border);
  border-left: 3px solid var(--red);
  border-radius: 0 8px 8px 0;
  padding: 14px 18px;
  margin-bottom: 18px;
}
.desc-box.gold   { border-left-color: var(--gold); }
.desc-box.purple { border-left-color: var(--purple); }
.desc-box.blue   { border-left-color: var(--blue); }
.desc-box.green  { border-left-color: var(--green); }
.db-title { font-size: 14px; font-weight: 900; color: #fff; margin-bottom: 5px; }
.db-body  { font-size: 12px; color: #6a8090; line-height: 1.7; }
.db-tags  { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }

/* ── 강조 카드 (익일 급등) ── */
.highlight-card {
  background: linear-gradient(160deg, var(--bg2), #120d1f);
  border: 1px solid rgba(153,102,255,.2);
  border-top: 3px solid var(--purple);
  border-radius: 10px;
  padding: 18px 16px;
  text-align: center;
  height: 100%;
}
.hc-rank  { font-size: 20px; margin-bottom: 6px; }
.hc-name  { font-size: 15px; font-weight: 900; color: var(--text); margin-bottom: 6px; line-height: 1.3; }
.hc-price { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: var(--red); }
.hc-stats { margin-top: 10px; display: flex; flex-direction: column; gap: 4px; }
.hc-stat  { font-size: 11px; color: var(--muted); }
.hc-stat b { color: var(--text); }

/* ── 수급 바 ── */
.flow-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 9px 0;
  border-bottom: 1px solid var(--border);
}
.flow-name  { width: 85px; font-size: 12px; font-weight: 700; color: #c0cce0; flex-shrink: 0; }
.flow-bar   { flex: 1; height: 5px; background: var(--border); border-radius: 3px; overflow: hidden; }
.flow-fill-up   { height: 100%; border-radius: 3px; background: linear-gradient(90deg,var(--red),var(--red2)); }
.flow-fill-down { height: 100%; border-radius: 3px; background: linear-gradient(90deg,var(--blue),var(--blue2)); float: right; }
.flow-val { width: 55px; text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 12px; font-weight: 600; flex-shrink: 0; }

/* ── 스탯 그리드 ── */
.stat-grid { display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px; }
.stat-item { display: flex; flex-direction: column; gap: 2px; }
.stat-label { font-size: 10px; color: var(--muted); font-weight: 700; letter-spacing: .5px; }
.stat-value { font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: var(--text); }

/* ── 버튼 ── */
.stButton > button {
  background: transparent !important;
  border: 1px solid var(--border2) !important;
  color: var(--text) !important;
  font-family: 'Noto Sans KR', sans-serif !important;
  font-weight: 700 !important;
  font-size: 12px !important;
  border-radius: 6px !important;
  padding: 5px 14px !important;
  transition: all .15s !important;
  width: 100% !important;
}
.stButton > button:hover {
  border-color: var(--red) !important;
  color: var(--red) !important;
  background: rgba(255,45,45,.06) !important;
}

/* ── 메트릭 ── */
[data-testid="stMetric"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  padding: 12px 14px !important;
}
[data-testid="stMetricLabel"] p { font-size: 11px !important; color: var(--muted) !important; font-weight: 700 !important; }
[data-testid="stMetricValue"] { font-family: 'JetBrains Mono', monospace !important; font-size: 18px !important; }

/* ── 데이터프레임 ── */
[data-testid="stDataFrame"] {
  background: var(--bg2) !important;
  border: 1px solid var(--border) !important;
  border-radius: 8px !important;
  overflow: hidden !important;
}

/* ── 스크롤바 ── */
::-webkit-scrollbar { width: 3px; height: 3px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border2); border-radius: 2px; }

/* ── 구분선 ── */
hr { border-color: var(--border) !important; margin: 20px 0 !important; }

/* ── 정보 메시지 ── */
[data-testid="stInfo"] {
  background: rgba(26,140,255,.08) !important;
  border: 1px solid rgba(26,140,255,.2) !important;
  border-radius: 8px !important;
  color: var(--text) !important;
}
</style>
""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# 데이터 로더
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=60)
def load_krx():
    try:
        df = fdr.StockListing('KRX')
        df.columns = [c.upper() for c in df.columns]
        # 등락률
        for col in ['CHANGESRATIO','CHGRATE','RATE','CHANGE','CHG']:
            if col in df.columns:
                df['CHG_FINAL'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                break
        if 'CHG_FINAL' not in df.columns:
            df['CHG_FINAL'] = 0.0
        # 거래량
        if 'VOLUME' in df.columns:
            df['VOLUME'] = pd.to_numeric(df['VOLUME'], errors='coerce').fillna(0)
        else:
            df['VOLUME'] = 0
        # 종가
        for col in ['CLOSE','PRICE','LAST']:
            if col in df.columns:
                df['PRICE_FINAL'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                break
        if 'PRICE_FINAL' not in df.columns:
            df['PRICE_FINAL'] = 0.0
        # 시가총액
        for col in ['MARCAP','MARKETCAP','CAP']:
            if col in df.columns:
                df['CAP_FINAL'] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                break
        if 'CAP_FINAL' not in df.columns:
            df['CAP_FINAL'] = 0.0
        return df.dropna(subset=['NAME']) if 'NAME' in df.columns else df
    except:
        return pd.DataFrame()


@st.cache_data(ttl=60)
def load_indices():
    result = {}
    targets = [("코스피","KS11"), ("코스닥","KQ11"), ("나스닥","IXIC"), ("USD/KRW","USD/KRW")]
    for name, code in targets:
        try:
            d = fdr.DataReader(code).tail(5)
            v    = float(d['Close'].iloc[-1])
            prev = float(d['Close'].iloc[-2])
            diff = v - prev
            pct  = diff / prev * 100
            result[name] = dict(v=v, diff=diff, pct=pct)
        except:
            result[name] = dict(v=0, diff=0, pct=0)
    return result


@st.cache_data(ttl=30)
def load_news():
    try:
        r = requests.get(
            "https://finance.naver.com/news/mainnews.naver",
            headers={'User-Agent':'Mozilla/5.0'}, timeout=5
        )
        soup = BeautifulSoup(r.text, 'html.parser')
        titles = [a.get_text().strip()
                  for a in soup.select('.mainNewsList .articleSubject a')[:12]]
        if titles:
            return "  ◆  ".join(titles)
    except:
        pass
    return "📡 뉴스 연결 중...  ◆  코스피·코스닥 실시간 수급 분석  ◆  세력추적 PRO"


@st.cache_data(ttl=300)
def load_ohlcv(code: str, days: int = 120):
    try:
        end   = datetime.today()
        start = end - timedelta(days=days + 40)
        df    = fdr.DataReader(code, start, end)
        if df is None or df.empty:
            return None
        df['MA5']     = df['Close'].rolling(5).mean()
        df['MA20']    = df['Close'].rolling(20).mean()
        df['MA60']    = df['Close'].rolling(60).mean()
        df['VOL_MA5'] = df['Volume'].rolling(5).mean()
        df['VOL_R']   = df['Volume'] / df['VOL_MA5'].replace(0, np.nan)
        return df.tail(days)
    except:
        return None


# ═══════════════════════════════════════════════════════════════════
# 분석 엔진
# ═══════════════════════════════════════════════════════════════════

def analyze_n_pattern(df_all: pd.DataFrame) -> pd.DataFrame:
    """N자형 눌림목: 20일선 근접 + 5일선 우위 + 거래량 감소"""
    if df_all.empty:
        return pd.DataFrame()
    results = []
    pool = df_all[(df_all['CHG_FINAL'].between(-6, 6)) & (df_all['VOLUME'] > 5000)].head(150)

    for _, row in pool.iterrows():
        try:
            code = str(row.get('CODE', ''))
            if not code:
                continue
            df = load_ohlcv(code, 60)
            if df is None or len(df) < 25:
                continue

            close   = float(df['Close'].iloc[-1])
            ma5     = float(df['MA5'].iloc[-1])
            ma20    = float(df['MA20'].iloc[-1])
            ma20_5d = float(df['MA20'].iloc[-5])
            if ma20 == 0:
                continue

            dist = (close - ma20) / ma20 * 100
            chg5 = (close - float(df['Close'].iloc[-5])) / float(df['Close'].iloc[-5]) * 100
            vol_r = float(df['VOL_R'].iloc[-1]) if not pd.isna(df['VOL_R'].iloc[-1]) else 1.0

            cond = [
                -4 <= dist <= 6,       # 20일선 근접
                ma5 >= ma20 * 0.995,   # 5일선 ≥ 20일선
                ma20 > ma20_5d,        # 20일선 우상향
                -10 <= chg5 <= 2,      # 최근 조정 중
                0.2 <= vol_r <= 1.3,   # 거래량 조용 (세력 대기)
            ]
            score = sum(cond)
            if score >= 3:
                results.append({
                    'NAME': row.get('NAME', ''),
                    'CODE': code,
                    'PRICE': close,
                    'CHG': row['CHG_FINAL'],
                    'MA20거리(%)': round(dist, 1),
                    '5일수익(%)': round(chg5, 1),
                    '거래량비율': round(vol_r, 2),
                    '점수': score,
                })
        except:
            continue

    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).sort_values(['점수', 'MA20거리(%)'],
                                              ascending=[False, True]).head(15)


def analyze_vol_surge(df_all: pd.DataFrame) -> pd.DataFrame:
    """거래량 폭증: 5일 평균 대비 2.5배 이상 + 고가권 마감 + 양봉"""
    if df_all.empty:
        return pd.DataFrame()
    results = []
    pool = df_all[df_all['VOLUME'] > 20000].head(300)

    for _, row in pool.iterrows():
        try:
            code = str(row.get('CODE', ''))
            if not code:
                continue
            df = load_ohlcv(code, 30)
            if df is None or len(df) < 10:
                continue

            t     = df.iloc[-1]
            close = float(t['Close'])
            high  = float(t['High'])
            low   = float(t['Low'])
            open_ = float(t['Open'])
            vol_r = float(t['VOL_R']) if not pd.isna(t['VOL_R']) else 1.0

            if high == low:
                continue

            body_pos   = (close - low) / (high - low) * 100   # 종가 위치 (높을수록 고가 마감)
            upper_tail = (high - close) / (high - low) * 100  # 윗꼬리 비율

            cond = [
                vol_r >= 2.5,        # 거래량 2.5배+
                body_pos >= 65,      # 고가권 마감
                upper_tail <= 30,    # 짧은 윗꼬리
                close >= open_,      # 양봉
            ]
            score = sum(cond)
            if score >= 3:
                results.append({
                    'NAME': row.get('NAME', ''),
                    'CODE': code,
                    'PRICE': close,
                    'CHG': row['CHG_FINAL'],
                    '거래량배율': round(vol_r, 1),
                    '고가권마감(%)': round(body_pos, 0),
                    '윗꼬리(%)': round(upper_tail, 0),
                    '점수': score,
                })
        except:
            continue

    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).sort_values('거래량배율', ascending=False).head(15)


def analyze_tomorrow(df_all: pd.DataFrame) -> pd.DataFrame:
    """익일 급등 후보: 종가 베팅 5조건"""
    if df_all.empty:
        return pd.DataFrame()
    results = []
    pool = df_all[(df_all['CHG_FINAL'] > 0.5) & (df_all['VOLUME'] > 10000)].head(200)

    for _, row in pool.iterrows():
        try:
            code = str(row.get('CODE', ''))
            if not code:
                continue
            df = load_ohlcv(code, 90)
            if df is None or len(df) < 25:
                continue

            t     = df.iloc[-1]
            close = float(t['Close'])
            high  = float(t['High'])
            low   = float(t['Low'])
            open_ = float(t['Open'])
            ma20  = float(t['MA20']) if not pd.isna(t['MA20']) else 0
            vol_r = float(t['VOL_R']) if not pd.isna(t['VOL_R']) else 1.0
            h52w  = float(df['High'].max())

            if high == low or ma20 == 0 or h52w == 0:
                continue

            body_pos = (close - low) / (high - low) * 100

            cond = [
                close >= h52w * 0.85,  # 52주 고가 85% 이상
                body_pos >= 75,        # 고가 마감
                close >= open_,        # 양봉
                close >= ma20,         # 20일선 위
                vol_r >= 1.5,          # 거래량 증가
            ]
            score = sum(cond)
            if score >= 3:
                results.append({
                    'NAME': row.get('NAME', ''),
                    'CODE': code,
                    'PRICE': close,
                    'CHG오늘': row['CHG_FINAL'],
                    '고가마감(%)': round(body_pos, 0),
                    '거래량배율': round(vol_r, 1),
                    '52주고가비(%)': round(close / h52w * 100, 0),
                    '점수': score,
                })
        except:
            continue

    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).sort_values('점수', ascending=False).head(12)


def analyze_foreign(df_all: pd.DataFrame) -> dict:
    """외인/기관 수급 추정 (시총 상위 500종목 기준)"""
    if df_all.empty:
        return dict(buy=pd.DataFrame(), sell=pd.DataFrame())
    top = df_all.nlargest(500, 'CAP_FINAL')
    buy  = top[top['CHG_FINAL'] >  1].nlargest(10, 'CHG_FINAL')
    sell = top[top['CHG_FINAL'] < -1].nsmallest(10, 'CHG_FINAL')
    return dict(buy=buy, sell=sell)


# ═══════════════════════════════════════════════════════════════════
# 차트 렌더러
# ═══════════════════════════════════════════════════════════════════

def render_chart(code: str, name: str):
    df = load_ohlcv(code, 120)
    if df is None:
        st.warning(f"차트 데이터 없음: {code}")
        return

    fig = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        vertical_spacing=0.02,
        row_heights=[0.70, 0.30]
    )

    # 캔들
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df['Open'], high=df['High'],
        low=df['Low'],   close=df['Close'],
        increasing=dict(line=dict(color='#ff2d2d'), fillcolor='#ff2d2d'),
        decreasing=dict(line=dict(color='#1a8cff'), fillcolor='#1a8cff'),
        name='', showlegend=False,
    ), row=1, col=1)

    # 이동평균선
    for col, color, name_ in [('MA5','#ffcc00','MA5'), ('MA20','#00d46a','MA20'), ('MA60','#c084fc','MA60')]:
        if col in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df[col],
                line=dict(color=color, width=1.4),
                name=name_, opacity=.9,
            ), row=1, col=1)

    # 거래량
    vol_colors = ['#ff2d2d' if c >= o else '#1a8cff'
                  for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(
        x=df.index, y=df['Volume'],
        marker_color=vol_colors, opacity=.6,
        name='거래량', showlegend=False,
    ), row=2, col=1)

    if 'VOL_MA5' in df.columns:
        fig.add_trace(go.Scatter(
            x=df.index, y=df['VOL_MA5'],
            line=dict(color='#ffcc00', width=1),
            name='VOL MA5', opacity=.8,
        ), row=2, col=1)

    CHART_THEME = dict(
        paper_bgcolor='#0d1118',
        plot_bgcolor='#0d1118',
        font=dict(family='JetBrains Mono', color='#4a6080', size=10),
        legend=dict(
            orientation='h', yanchor='bottom', y=1.02,
            xanchor='right', x=1,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11, color='#dce6f5'),
        ),
        margin=dict(l=8, r=8, t=45, b=8),
        height=520,
        xaxis_rangeslider_visible=False,
    )
    AXIS_STYLE = dict(gridcolor='#1e2636', zeroline=False, showline=False)

    fig.update_layout(
        title=dict(
            text=f"<b style='color:#dce6f5'>{name}</b>"
                 f"<span style='color:#4a6080;font-size:13px;'> ({code})</span>",
            font=dict(size=15),
        ),
        **CHART_THEME,
        xaxis=AXIS_STYLE,
        yaxis={**AXIS_STYLE, 'tickformat': ',.0f'},
        xaxis2=AXIS_STYLE,
        yaxis2=AXIS_STYLE,
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


def render_spark(code: str):
    try:
        df = load_ohlcv(code, 20)
        if df is None:
            return None
        c0, c1 = float(df['Close'].iloc[0]), float(df['Close'].iloc[-1])
        col = '#ff2d2d' if c1 >= c0 else '#1a8cff'
        fig = go.Figure(go.Scatter(
            y=df['Close'], mode='lines',
            line=dict(color=col, width=1.5),
            fill='tozeroy', fillcolor=f'{col}18',
        ))
        fig.update_layout(
            width=100, height=40,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis_visible=False, yaxis_visible=False,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
        )
        return fig
    except:
        return None


# ═══════════════════════════════════════════════════════════════════
# 바닥매집주 족보 분석 (PDF: 60월선 + 박스권 매집)
# ═══════════════════════════════════════════════════════════════════

@st.cache_data(ttl=600)
def load_monthly_ohlcv(code: str, months: int = 120):
    """월봉 데이터 + 60월선 계산"""
    try:
        end   = datetime.today()
        start = end - timedelta(days=months * 31 + 90)
        df    = fdr.DataReader(code, start, end)
        if df is None or df.empty:
            return None
        df_m             = df['Close'].resample('ME').last().to_frame()
        df_m['High']     = df['High'].resample('ME').max()
        df_m['Low']      = df['Low'].resample('ME').min()
        df_m['Open']     = df['Open'].resample('ME').first()
        df_m['Volume']   = df['Volume'].resample('ME').sum()
        df_m['MA60']     = df_m['Close'].rolling(60).mean()   # 60월선 (5년)
        df_m['MA12']     = df_m['Close'].rolling(12).mean()   # 12월선 (1년)
        return df_m.dropna(subset=['Close']).tail(months)
    except:
        return None


def analyze_jokbo(df_all: pd.DataFrame) -> pd.DataFrame:
    """
    바닥매집주 족보 탐지 (승관쌤 PDF 기법):
    ① 현재가가 60월선 아래 or 10% 이내 (저평가 구간)
    ② 최근 120일 박스권 형성 (고저 40% 이내)
    ③ 박스 하단 30% 이내 위치 (매수 타점)
    ④ 거래량 감소 (세력 조용히 매집 중)
    ⑤ 월봉 바닥 2회 이상 반복 지지
    ⑥ 12개월 횡보 (±30% 이내)
    """
    if df_all.empty:
        return pd.DataFrame()
    results = []
    pool = df_all[
        (df_all['PRICE_FINAL'] >= 500) &
        (df_all['VOLUME'] > 1000) &
        (df_all['CHG_FINAL'].between(-8, 8))
    ].head(200)

    for _, row in pool.iterrows():
        try:
            code = str(row.get('CODE', ''))
            if not code:
                continue
            df_m = load_monthly_ohlcv(code, 120)
            df_d = load_ohlcv(code, 180)
            if df_m is None or len(df_m) < 24 or df_d is None or len(df_d) < 60:
                continue

            close  = float(df_d['Close'].iloc[-1])
            ma60_m = float(df_m['MA60'].iloc[-1]) if not pd.isna(df_m['MA60'].iloc[-1]) else None
            if ma60_m is None or ma60_m == 0:
                continue

            # ① 60월선 대비 위치
            pos60      = (close - ma60_m) / ma60_m * 100
            below_ma60 = pos60 <= 10

            # ② 박스권 범위
            r120      = df_d.tail(120)
            box_high  = float(r120['High'].max())
            box_low   = float(r120['Low'].min())
            if box_low == 0:
                continue
            box_range = (box_high - box_low) / box_low * 100
            is_box    = box_range <= 40

            # ③ 박스 하단 근접
            box_pos  = (close - box_low) / (box_high - box_low) * 100 if box_high != box_low else 50
            near_bot = box_pos <= 30

            # ④ 거래량 감소
            vol_r     = float(df_d['VOL_R'].iloc[-1]) if not pd.isna(df_d['VOL_R'].iloc[-1]) else 1.0
            quiet_vol = 0.1 <= vol_r <= 1.2

            # ⑤ 월봉 바닥 반복 지지
            low_zone   = box_low * 1.15
            touch_cnt  = int((df_m.tail(24)['Low'] <= low_zone).sum())
            multi_touch= touch_cnt >= 2

            # ⑥ 12개월 횡보
            chg_12m  = (close - float(df_m['Close'].iloc[-12])) / float(df_m['Close'].iloc[-12]) * 100 \
                       if len(df_m) >= 12 else 0
            sideways = abs(chg_12m) <= 30

            score = sum([below_ma60, is_box, near_bot, quiet_vol, multi_touch, sideways])
            if score >= 3:
                results.append({
                    'NAME':       row.get('NAME', ''),
                    'CODE':       code,
                    'PRICE':      close,
                    'CHG':        row['CHG_FINAL'],
                    '60월선위치': f"{pos60:+.1f}%",
                    '박스권범위': f"{box_range:.0f}%",
                    '하단위치':   f"{box_pos:.0f}%",
                    '거래량비율': f"{vol_r:.1f}x",
                    '바닥터치':   f"{touch_cnt}회",
                    '점수':       score,
                })
        except:
            continue

    if not results:
        return pd.DataFrame()
    return pd.DataFrame(results).sort_values('점수', ascending=False).head(15)


def render_jokbo_chart(code: str, name: str):
    """
    족보 전용 차트
    ─ 상단: 월봉 캔들 + 60월선(굵은 흰선) + 12월선 + 바닥 지지선
    ─ 중단: 일봉 캔들 + MA5/20/60 + 박스권 상하단선
    ─ 하단: 거래량 + VOL MA5
    """
    df_m = load_monthly_ohlcv(code, 120)
    df_d = load_ohlcv(code, 360)
    if df_m is None or df_d is None:
        st.warning(f"차트 데이터 없음: {code}")
        return

    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=False,
        vertical_spacing=0.05,
        row_heights=[0.38, 0.38, 0.24],
        subplot_titles=[
            "📅 월봉 — 60월선 기준 (저평가 확인)",
            "📊 일봉 — 박스권 매수 타점",
            "📊 거래량",
        ]
    )
    AXIS = dict(gridcolor='#1e2636', zeroline=False, showline=False, color='#4a6080')

    # ── 월봉 캔들 ──
    fig.add_trace(go.Candlestick(
        x=df_m.index, open=df_m['Open'], high=df_m['High'],
        low=df_m['Low'], close=df_m['Close'],
        increasing=dict(line=dict(color='#ff2d2d'), fillcolor='#ff2d2d'),
        decreasing=dict(line=dict(color='#1a8cff'), fillcolor='#1a8cff'),
        name='월봉', showlegend=False,
    ), row=1, col=1)

    # 60월선 ─ 굵은 흰선 (PDF 핵심 기준선)
    if 'MA60' in df_m.columns:
        fig.add_trace(go.Scatter(
            x=df_m.index, y=df_m['MA60'],
            line=dict(color='#e0e6f0', width=3),
            name='60월선',
        ), row=1, col=1)

    # 12월선
    if 'MA12' in df_m.columns:
        fig.add_trace(go.Scatter(
            x=df_m.index, y=df_m['MA12'],
            line=dict(color='#ffb400', width=1.5, dash='dot'),
            name='12월선', opacity=0.85,
        ), row=1, col=1)

    # 박스 하단 지지선 (월봉)
    box_low  = float(df_d.tail(120)['Low'].min())
    box_high = float(df_d.tail(120)['High'].max())
    fig.add_hline(y=box_low,
                  line=dict(color='#ff2d2d', width=1.5, dash='dot'),
                  annotation_text="바닥 지지",
                  annotation_font_color='#ff2d2d',
                  row=1, col=1)

    # ── 일봉 캔들 ──
    df_show = df_d.tail(240)
    fig.add_trace(go.Candlestick(
        x=df_show.index, open=df_show['Open'], high=df_show['High'],
        low=df_show['Low'], close=df_show['Close'],
        increasing=dict(line=dict(color='#ff2d2d'), fillcolor='#ff2d2d'),
        decreasing=dict(line=dict(color='#1a8cff'), fillcolor='#1a8cff'),
        name='일봉', showlegend=False,
    ), row=2, col=1)

    for col_, color_, nm_ in [('MA5','#ffcc00','MA5'),('MA20','#00d46a','MA20'),('MA60','#c084fc','MA60')]:
        if col_ in df_show.columns:
            fig.add_trace(go.Scatter(
                x=df_show.index, y=df_show[col_],
                line=dict(color=color_, width=1.2),
                name=nm_, opacity=0.9,
            ), row=2, col=1)

    # 박스권 상하단선 (일봉)
    for y_, lbl_, clr_ in [
        (box_high, '박스 상단 (분할매도)', '#ffb400'),
        (box_low,  '박스 하단 (매수타점)', '#ff2d2d'),
    ]:
        fig.add_hline(y=y_,
                      line=dict(color=clr_, width=1.5, dash='dot'),
                      annotation_text=lbl_,
                      annotation_font_color=clr_,
                      annotation_position='right',
                      row=2, col=1)

    # ── 거래량 ──
    vol_colors = ['#ff2d2d' if c >= o else '#1a8cff'
                  for c, o in zip(df_show['Close'], df_show['Open'])]
    fig.add_trace(go.Bar(
        x=df_show.index, y=df_show['Volume'],
        marker_color=vol_colors, opacity=0.65,
        name='거래량', showlegend=False,
    ), row=3, col=1)
    if 'VOL_MA5' in df_show.columns:
        fig.add_trace(go.Scatter(
            x=df_show.index, y=df_show['VOL_MA5'],
            line=dict(color='#ffcc00', width=1),
            name='VOL MA5',
        ), row=3, col=1)

    fig.update_layout(
        paper_bgcolor='#0d1118', plot_bgcolor='#0d1118',
        font=dict(family='JetBrains Mono', color='#4a6080', size=10),
        legend=dict(orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1,
                    bgcolor='rgba(0,0,0,0)', font=dict(size=10, color='#dce6f5')),
        margin=dict(l=8, r=8, t=60, b=8),
        height=840,
        xaxis_rangeslider_visible=False,
        xaxis2_rangeslider_visible=False,
    )
    for ax in ['xaxis','yaxis','xaxis2','yaxis2','xaxis3','yaxis3']:
        fig.update_layout(**{ax: AXIS})
    fig.update_yaxes(tickformat=',.0f')
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # ── 분석 요약 ──
    ma60_now  = float(df_m['MA60'].iloc[-1]) if not pd.isna(df_m['MA60'].iloc[-1]) else 0
    close_now = float(df_d['Close'].iloc[-1])
    pos60     = (close_now - ma60_now) / ma60_now * 100 if ma60_now else 0
    box_pos   = (close_now - box_low) / (box_high - box_low) * 100 if box_high != box_low else 50
    verdict   = "🟢 저평가 매집 구간" if pos60 <= 0 else \
                ("🟡 60월선 근접 — 관찰" if pos60 <= 15 else "🔵 60월선 위 — 상승 추세")

    st.markdown(f"""
    <div style='background:var(--bg2);border:1px solid var(--border);
                border-left:3px solid #00d46a;border-radius:0 10px 10px 0;
                padding:14px 18px;margin-top:12px;'>
      <div style='font-size:13px;font-weight:900;color:#00d46a;margin-bottom:8px;'>
        📋 족보 분석 요약
      </div>
      <div style='font-size:12px;color:#6a8090;line-height:2.2;'>
        ▶ 60월선 대비: <b style='color:#dce6f5;'>{pos60:+.1f}%</b> &nbsp;{verdict}<br>
        ▶ 박스권: <b style='color:#dce6f5;'>{box_low:,.0f}원 ~ {box_high:,.0f}원</b>
           &nbsp;(범위 {(box_high-box_low)/box_low*100:.0f}%)<br>
        ▶ 박스 내 위치: <b style='color:#dce6f5;'>하단에서 {box_pos:.0f}%</b><br>
        ▶ 매수 타점: <b style='color:#ff2d2d;'>
           박스 하단 ({box_low:,.0f}원) 근처 일봉 양봉 + 거래량 폭증 시</b><br>
        ▶ 분할매도: <b style='color:#ffb400;'>
           박스 상단 ({box_high:,.0f}원) 돌파 후 60월선 부근</b>
      </div>
    </div>
    """, unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════
# 메인
# ═══════════════════════════════════════════════════════════════════

def main():
    # 세션 초기화
    if 'sel_code' not in st.session_state:
        st.session_state.sel_code = None
    if 'sel_name' not in st.session_state:
        st.session_state.sel_name = ''

    # ── 뉴스 티커 ──────────────────────────────────────────────────
    news = load_news()
    st.markdown(
        f"<div class='ticker-wrap'><div class='ticker-inner'>"
        f"📡&nbsp;{news}&nbsp;&nbsp;&nbsp;&nbsp;📡&nbsp;{news}"
        f"</div></div>",
        unsafe_allow_html=True
    )

    # ── 헤더 ───────────────────────────────────────────────────────
    now  = datetime.now()
    h, m = now.hour, now.minute
    is_open = (9 <= h < 15) or (h == 15 and m < 30)
    mst_cls  = 'mst-open'  if is_open else 'mst-close'
    mst_text = '● 장중'    if is_open else '○ 장마감'

    st.markdown(f"""
    <div class='app-header'>
      <div class='logo'>
        <div class='logo-main'>세력추적<em>PRO</em></div>
        <div class='logo-sub'>Real-time Market Intelligence</div>
      </div>
      <div class='header-right'>
        <div class='market-status {mst_cls}'>{mst_text}</div>
        <div class='header-time'>{now.strftime('%Y.%m.%d %H:%M:%S')}</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    # ── 지수 스트립 ────────────────────────────────────────────────
    with st.spinner(""):
        idx = load_indices()
    strip = "<div class='index-strip'>"
    for name, d in idx.items():
        cls  = 'c-up' if d['pct'] >= 0 else ('c-down' if d['pct'] < 0 else 'c-flat')
        sign = '+' if d['diff'] >= 0 else ''
        strip += f"""
        <div class='idx-block'>
          <div class='idx-label'>{name}</div>
          <div class='idx-value {cls}'>{d['v']:,.2f}</div>
          <div class='idx-change {cls}'>{sign}{d['diff']:,.2f} ({sign}{d['pct']:.2f}%)</div>
        </div>"""
    strip += "</div>"
    st.markdown(strip, unsafe_allow_html=True)

    # ── KRX 데이터 로드 ────────────────────────────────────────────
    with st.spinner("📡 KRX 전종목 데이터 로딩 중..."):
        df = load_krx()

    if df.empty:
        st.error("⚠️ 데이터 로드 실패. 잠시 후 새로고침해주세요.")
        if st.button("🔄 새로고침"):
            st.cache_data.clear()
            st.rerun()
        return

    # ── 선택 차트 팝업 ─────────────────────────────────────────────
    if st.session_state.sel_code:
        with st.container():
            cc, _ = st.columns([1, 7])
            with cc:
                if st.button("✕ 닫기"):
                    st.session_state.sel_code = None
                    st.rerun()
        render_chart(st.session_state.sel_code, st.session_state.sel_name)
        st.markdown("<hr/>", unsafe_allow_html=True)

    # ── 탭 ─────────────────────────────────────────────────────────
    tabs = st.tabs([
        "🔥 세력 수급",
        "📈 N자형 눌림목",
        "💥 거래량 폭증",
        "🌙 익일 급등 예측",
        "🏦 외인/기관 수급",
        "📊 바닥매집주 족보",
    ])

    # ══════════════════════════════════════════════════════════════
    # TAB 1: 세력 수급 & 미니 차트
    # ══════════════════════════════════════════════════════════════
    with tabs[0]:
        st.markdown("<div class='sec-title'>🔥 <b>거래량 상위</b> — 세력의 발자국</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='desc-box'>
          <div class='db-title'>💡 거래량이 곧 세력이다</div>
          <div class='db-body'>
            개미는 거래량을 속일 수 있지만, 세력은 반드시 돈을 써야 합니다.<br>
            갑작스러운 거래량 폭발은 큰 움직임이 임박했다는 강력한 신호입니다.
          </div>
        </div>
        """, unsafe_allow_html=True)

        hot = df.nlargest(12, 'VOLUME')

        for i in range(0, len(hot), 2):
            c1, c2 = st.columns(2)
            for ci, col_ctx in enumerate([c1, c2]):
                idx_r = i + ci
                if idx_r >= len(hot):
                    break
                row = hot.iloc[idx_r]
                chg  = float(row.get('CHG_FINAL', 0))
                code = str(row.get('CODE', ''))
                name = str(row.get('NAME', ''))
                price = float(row.get('PRICE_FINAL', 0))
                vol   = int(row.get('VOLUME', 0))
                cls   = 'c-up' if chg >= 0 else 'c-down'

                with col_ctx:
                    st.markdown(f"""
                    <div class='s-card'>
                      <div class='sc-row1'>
                        <div>
                          <div class='sc-name'>{name}
                            <span class='badge b-red'>수급 상위</span>
                          </div>
                          <div class='sc-code'>{code}</div>
                        </div>
                        <div>
                          <div class='sc-price {cls}'>{price:,.0f}</div>
                          <div class='sc-chg {cls}'>{chg:+.2f}%</div>
                        </div>
                      </div>
                      <div class='sc-row2'>
                        <span class='badge b-muted'>거래량 {vol:,}</span>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)

                    if st.button("📊 차트 보기", key=f"hot_{idx_r}"):
                        st.session_state.sel_code = code
                        st.session_state.sel_name = name
                        st.rerun()

        # 미니 스파크라인
        st.markdown("<div class='sec-title' style='margin-top:28px;'>⚡ <b>실시간 미니 차트</b></div>",
                    unsafe_allow_html=True)
        sp_cols = st.columns(4)
        for i, (_, row) in enumerate(hot.head(8).iterrows()):
            with sp_cols[i % 4]:
                fig = render_spark(str(row.get('CODE', '')))
                if fig:
                    st.plotly_chart(fig, use_container_width=False,
                                    config={'displayModeBar': False})
                chg = float(row.get('CHG_FINAL', 0))
                cls = '#ff2d2d' if chg >= 0 else '#1a8cff'
                st.markdown(
                    f"<div style='font-size:11px;font-weight:700;color:#c0cce0;'>"
                    f"{row.get('NAME','')}</div>"
                    f"<div style='font-family:JetBrains Mono,monospace;font-size:11px;"
                    f"color:{cls};'>{chg:+.2f}%</div>",
                    unsafe_allow_html=True
                )

    # ══════════════════════════════════════════════════════════════
    # TAB 2: N자형 눌림목
    # ══════════════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("<div class='sec-title'>📈 <b>N자형 눌림목</b> — 20일선 지지 반등</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='desc-box green'>
          <div class='db-title'>🎯 달리는 말에 올라타는 최적 타이밍</div>
          <div class='db-body'>
            "너무 오른 것은 무섭다" — 하지만 생명선(20일선)에서 지지받고 재상승하는 종목은
            가장 안전하고 수익률이 높은 구간입니다.
          </div>
          <div class='db-tags'>
            <span class='badge b-green'>20일선 ±4% 이내</span>
            <span class='badge b-green'>5일선 ≥ 20일선</span>
            <span class='badge b-green'>20일선 우상향</span>
            <span class='badge b-green'>거래량 감소 (세력 대기)</span>
            <span class='badge b-green'>최근 조정 중</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("N자형 눌림목 탐색 중... (30~60초 소요)"):
            df_n = analyze_n_pattern(df)

        if df_n.empty:
            st.info("현재 N자형 눌림목 패턴 종목 없음. 장 중 또는 변동성 구간에서 재확인하세요.")
        else:
            for i, (_, r) in enumerate(df_n.iterrows()):
                score = int(r.get('점수', 0))
                chg   = float(r.get('CHG', 0))
                dist  = float(r.get('MA20거리(%)', 0))
                chg5  = float(r.get('5일수익(%)', 0))
                vol_r = float(r.get('거래량비율', 1))
                cls   = 'c-up' if chg >= 0 else 'c-down'

                ca, cb, cc, cd, ce = st.columns([3, 1, 1, 1, 1])
                with ca:
                    stars = '⭐' * score
                    st.markdown(f"""
                    <div class='s-card'>
                      <div class='sc-row1'>
                        <div>
                          <div class='sc-name'>{r['NAME']}
                            <span class='badge b-green'>{stars}</span>
                          </div>
                          <div class='sc-code'>{r['CODE']}</div>
                        </div>
                        <div>
                          <div class='sc-price'>{float(r['PRICE']):,.0f}</div>
                          <div class='sc-chg {cls}'>{chg:+.2f}%</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with cb:
                    st.metric("20일선 거리", f"{dist:+.1f}%")
                with cc:
                    st.metric("5일 수익", f"{chg5:+.1f}%")
                with cd:
                    st.metric("거래량 비율", f"{vol_r:.1f}x")
                with ce:
                    if st.button("차트", key=f"n_{i}"):
                        st.session_state.sel_code = r['CODE']
                        st.session_state.sel_name = r['NAME']
                        st.rerun()

    # ══════════════════════════════════════════════════════════════
    # TAB 3: 거래량 폭증
    # ══════════════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown("<div class='sec-title'>💥 <b>거래량 폭증</b> — 세력의 매집 신호</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='desc-box gold'>
          <div class='db-title'>💰 세력은 거래량을 숨길 수 없다</div>
          <div class='db-body'>
            5일 평균 거래량 대비 250%+ 폭증, 고가권 마감, 짧은 윗꼬리, 양봉 마감.<br>
            이 4가지가 겹치면 대규모 매집의 증거입니다.
          </div>
          <div class='db-tags'>
            <span class='badge b-gold'>거래량 2.5배 이상</span>
            <span class='badge b-gold'>고가권 마감 65%+</span>
            <span class='badge b-gold'>윗꼬리 30% 이하</span>
            <span class='badge b-gold'>양봉 마감</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("거래량 폭증 종목 탐색 중..."):
            df_v = analyze_vol_surge(df)

        if df_v.empty:
            st.info("현재 거래량 폭증 기준에 해당하는 종목 없음.")
        else:
            for i, (_, r) in enumerate(df_v.iterrows()):
                chg   = float(r.get('CHG', 0))
                vol_r = float(r.get('거래량배율', 1))
                body  = float(r.get('고가권마감(%)', 0))
                cls   = 'c-up' if chg >= 0 else 'c-down'

                ca, cb, cc, cd, ce = st.columns([3, 1, 1, 1, 1])
                with ca:
                    st.markdown(f"""
                    <div class='s-card'>
                      <div class='sc-row1'>
                        <div>
                          <div class='sc-name'>{r['NAME']}
                            <span class='badge b-gold'>🔥 폭증</span>
                          </div>
                          <div class='sc-code'>{r['CODE']}</div>
                        </div>
                        <div>
                          <div class='sc-price'>{float(r['PRICE']):,.0f}</div>
                          <div class='sc-chg {cls}'>{chg:+.2f}%</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with cb:
                    st.metric("거래량 배율", f"{vol_r:.1f}x")
                with cc:
                    st.metric("고가권 마감", f"{body:.0f}%")
                with cd:
                    st.metric("오늘 등락", f"{chg:+.2f}%")
                with ce:
                    if st.button("차트", key=f"v_{i}"):
                        st.session_state.sel_code = r['CODE']
                        st.session_state.sel_name = r['NAME']
                        st.rerun()

    # ══════════════════════════════════════════════════════════════
    # TAB 4: 익일 급등 예측
    # ══════════════════════════════════════════════════════════════
    with tabs[3]:
        st.markdown("<div class='sec-title'>🌙 <b>익일 급등 유망주</b> — 종가 베팅 기법</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='desc-box purple'>
          <div class='db-title'>🎯 내일의 주인공을 오늘 찾는다</div>
          <div class='db-body'>
            당일 고가 마감 · 거래량 폭증 · 20일선 위 · 52주 고가 근접 · 양봉 마감.<br>
            종가 베팅 5조건을 모두 충족하는 종목이 다음날 급등할 확률이 높습니다.
          </div>
          <div class='db-tags'>
            <span class='badge b-purple'>52주 고가 85%+</span>
            <span class='badge b-purple'>고가 마감 75%+</span>
            <span class='badge b-purple'>양봉</span>
            <span class='badge b-purple'>20일선 위</span>
            <span class='badge b-purple'>거래량 1.5배+</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.spinner("익일 급등 후보 분석 중..."):
            df_t = analyze_tomorrow(df)

        if df_t.empty:
            st.info("현재 조건에 맞는 익일 급등 후보 없음.")
        else:
            # 상위 4개 하이라이트
            top4 = df_t.head(4)
            hl = st.columns(len(top4))
            ranks = ['🥇', '🥈', '🥉', '4위']
            for i, (_, r) in enumerate(top4.iterrows()):
                with hl[i]:
                    score = int(r.get('점수', 0))
                    st.markdown(f"""
                    <div class='highlight-card'>
                      <div class='hc-rank'>{ranks[i]}</div>
                      <div class='hc-name'>{r['NAME']}</div>
                      <div class='hc-price'>{float(r['PRICE']):,.0f}원</div>
                      <div class='hc-stats'>
                        <div class='hc-stat'>오늘 <b>{r['CHG오늘']:+.2f}%</b></div>
                        <div class='hc-stat'>고가마감 <b>{r['고가마감(%)']:.0f}%</b></div>
                        <div class='hc-stat'>거래량 <b>{r['거래량배율']:.1f}x</b></div>
                        <div class='hc-stat'>52주고가비 <b>{r['52주고가비(%)']:.0f}%</b></div>
                        <div class='hc-stat'>점수 <b>{'⭐'*score}</b></div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                    if st.button("📊 차트", key=f"t_hl_{i}", use_container_width=True):
                        st.session_state.sel_code = r['CODE']
                        st.session_state.sel_name = r['NAME']
                        st.rerun()

            # 전체 테이블
            st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
            display_cols = ['NAME', 'PRICE', 'CHG오늘', '고가마감(%)', '거래량배율', '52주고가비(%)', '점수']
            exist_cols   = [c for c in display_cols if c in df_t.columns]
            st.dataframe(df_t[exist_cols], use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 5: 외인/기관 수급
    # ══════════════════════════════════════════════════════════════
    with tabs[4]:
        st.markdown("<div class='sec-title'>🏦 <b>외인/기관 수급 추정</b></div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='desc-box blue'>
          <div class='db-title'>📡 시장 큰손을 추적한다</div>
          <div class='db-body'>
            시가총액 상위 500종목 기준으로 당일 등락률 + 거래량 패턴을 분석해<br>
            외인·기관의 순매수·순매도 추정 종목을 선별합니다.<br>
            <span style='color:var(--red);font-size:11px;'>※ 실제 외인 공시 데이터가 아닌 패턴 추정값입니다.</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        flow = analyze_foreign(df)
        col_b, col_s = st.columns(2)

        with col_b:
            st.markdown(
                "<div style='font-size:12px;font-weight:900;color:var(--red);"
                "margin-bottom:10px;letter-spacing:1px;'>🟢 순매수 추정 상위</div>",
                unsafe_allow_html=True
            )
            if not flow['buy'].empty:
                max_chg = float(flow['buy']['CHG_FINAL'].abs().max()) or 1
                for _, r in flow['buy'].iterrows():
                    chg = float(r.get('CHG_FINAL', 0))
                    w   = min(abs(chg) / max_chg * 100, 100)
                    st.markdown(f"""
                    <div class='flow-row'>
                      <div class='flow-name'>{r.get('NAME','')}</div>
                      <div class='flow-bar'><div class='flow-fill-up' style='width:{w:.0f}%'></div></div>
                      <div class='flow-val c-up'>{chg:+.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

        with col_s:
            st.markdown(
                "<div style='font-size:12px;font-weight:900;color:var(--blue);"
                "margin-bottom:10px;letter-spacing:1px;'>🔴 순매도 추정 상위</div>",
                unsafe_allow_html=True
            )
            if not flow['sell'].empty:
                max_chg = float(flow['sell']['CHG_FINAL'].abs().max()) or 1
                for _, r in flow['sell'].iterrows():
                    chg = float(r.get('CHG_FINAL', 0))
                    w   = min(abs(chg) / max_chg * 100, 100)
                    st.markdown(f"""
                    <div class='flow-row'>
                      <div class='flow-name'>{r.get('NAME','')}</div>
                      <div class='flow-bar'><div class='flow-fill-down' style='width:{w:.0f}%'></div></div>
                      <div class='flow-val c-down'>{chg:+.1f}%</div>
                    </div>
                    """, unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════════
    # TAB 6: 바닥매집주 족보
    # ══════════════════════════════════════════════════════════════
    with tabs[5]:
        st.markdown("<div class='sec-title'>📊 <b>바닥매집주 족보</b> — 60월선 + 박스권 매집 탐지</div>",
                    unsafe_allow_html=True)
        st.markdown("""
        <div class='desc-box' style='border-left-color:#00d46a;'>
          <div class='db-title'>🎯 세력은 바닥에서 조용히 산다</div>
          <div class='db-body'>
            <b>60월선(5년 이동평균)</b> 아래 = 역사적 저평가 구간.<br>
            세력은 이 구간에서 주가를 박스권에 가두고 물량을 모읍니다.<br>
            월봉 바닥 반복 지지 + 일봉 박스권 하단 = 매집 완료 신호.
          </div>
          <div class='db-tags'>
            <span class='badge b-green'>60월선 아래 = 저평가</span>
            <span class='badge b-green'>박스권 40% 이내</span>
            <span class='badge b-green'>박스 하단 지지 반복</span>
            <span class='badge b-green'>거래량 감소 (세력 대기)</span>
            <span class='badge b-green'>일봉 매수타점 확인</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # 종목 직접 검색
        c_inp, c_btn = st.columns([3, 1])
        with c_inp:
            search_code = st.text_input("종목코드 직접 분석",
                placeholder="예: 039610  (화성밸브)  /  006340  (대원전선)",
                label_visibility="collapsed")
        with c_btn:
            do_search = st.button("🔍 족보 분석", use_container_width=True)

        if do_search and search_code.strip():
            scode = search_code.strip().zfill(6)
            sname_row = df[df['CODE'].astype(str).str.zfill(6) == scode] if 'CODE' in df.columns else pd.DataFrame()
            sname = sname_row['NAME'].iloc[0] if not sname_row.empty else scode
            st.markdown(
                f"<div style='font-size:14px;font-weight:900;color:#00d46a;margin:12px 0;'>"
                f"🔍 {sname} ({scode}) 족보 분석</div>",
                unsafe_allow_html=True)
            render_jokbo_chart(scode, sname)

        # AI 자동 탐지
        st.markdown("<div class='sec-title' style='margin-top:24px;'>🤖 <b>AI 자동 탐지</b> — 바닥매집 패턴</div>",
                    unsafe_allow_html=True)

        with st.spinner("바닥매집주 탐색 중... (60월선 + 박스권 분석, 1~2분 소요)"):
            df_jokbo = analyze_jokbo(df)

        if df_jokbo.empty:
            st.info("현재 바닥매집 패턴 조건에 맞는 종목이 없습니다.")
        else:
            for i, (_, r) in enumerate(df_jokbo.iterrows()):
                score  = int(r.get('점수', 0))
                chg    = float(r.get('CHG', 0))
                cls    = 'c-up' if chg >= 0 else 'c-down'
                stars  = '⭐' * score
                bcls   = 'b-green' if score >= 5 else ('b-gold' if score >= 4 else 'b-muted')

                ca, cb, cc, cd, ce, cf = st.columns([3, 1, 1, 1, 1, 1])
                with ca:
                    st.markdown(f"""
                    <div class='s-card'>
                      <div class='sc-row1'>
                        <div>
                          <div class='sc-name'>{r['NAME']}
                            <span class='badge {bcls}'>{stars} 매집</span>
                          </div>
                          <div class='sc-code'>{r['CODE']}</div>
                        </div>
                        <div>
                          <div class='sc-price'>{float(r['PRICE']):,.0f}</div>
                          <div class='sc-chg {cls}'>{chg:+.2f}%</div>
                        </div>
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
                with cb: st.metric("60월선", r.get('60월선위치','-'))
                with cc: st.metric("박스범위", r.get('박스권범위','-'))
                with cd: st.metric("하단위치", r.get('하단위치','-'))
                with ce: st.metric("바닥터치", r.get('바닥터치','-'))
                with cf:
                    if st.button("차트", key=f"jb_{i}"):
                        st.session_state.sel_code = r['CODE']
                        st.session_state.sel_name = r['NAME']
                        st.rerun()

    # ── 하단 갱신 ──────────────────────────────────────────────────
    st.markdown("<hr/>", unsafe_allow_html=True)
    c_btn, c_info = st.columns([1, 5])
    with c_btn:
        if st.button("🔄 전체 데이터 갱신"):
            st.cache_data.clear()
            st.session_state.sel_code = None
            st.rerun()
    with c_info:
        st.caption(
            f"마지막 갱신: {now.strftime('%Y-%m-%d %H:%M:%S')}  |  "
            "KRX 60초 캐시  |  차트 5분 캐시  |  뉴스 30초 캐시"
        )


if __name__ == "__main__":
    main()
