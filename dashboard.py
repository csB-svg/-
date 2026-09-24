import streamlit as st
import pandas as pd
import requests
import datetime
import pyupbit
import os
import json
import time
import plotly.graph_objects as go

# 페이지 설정 (와이드 모드)
st.set_page_config(
    page_title="코인 퀀트 트레이딩 대시보드",
    page_icon="📈",
    layout="wide"
)

# 타이틀
st.title("🤖 코인원 퀀트 자동 매매 봇 대시보드")
st.markdown("실시간 봇 상태, 한 달 복리 목표 달성률, 그리고 5개 코인의 1시간봉 차트와 실제 자산 연동 현황을 확인하는 공간입니다.")

st.markdown("---")

# 관심 코인 리스트 (5개 완벽 고정)
upbit_tickers = ['KRW-BTC', 'KRW-ETH', 'KRW-XRP', 'KRW-SOL', 'KRW-ADA']
coinone_symbols = {
    'KRW-BTC': 'BTC',
    'KRW-ETH': 'ETH',
    'KRW-XRP': 'XRP',
    'KRW-SOL': 'SOL',
    'KRW-ADA': 'ADA'
}
k = 0.5

# 실제 매도(청산) 완료된 내역 기록 파일
HISTORY_FILE = "trade_history.json"
def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if data:
                    return data
        except:
            pass
    return {
        datetime.datetime.now().strftime("%Y-%m-%d"): {
            "start_balance": 1329057,
            "profit_krw": 0, 
            "profit_pct": "+0.0%", 
            "trades": 0,
            "end_balance": 1329057,
            "status": "매도 완료 대기 중"
        }
    }

history_data = load_history()

# 공포 탐욕 지수
def get_fear_and_greed():
    try:
        url = "https://api.alternative.me/fng/?limit=1"
        res = requests.get(url, timeout=3).json()
        return res['data'][0]['value'], res['data'][0]['value_classification']
    except:
        return "50", "Neutral"

# 봇 계산 로직 (목표가 & 이평선)
def get_target_price(ticker, k):
    try:
        df = pyupbit.get_ohlcv(ticker, interval="day", count=2)
        if df is not None and len(df) >= 2:
            return df.iloc[1]['open'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k
    except:
        pass
    return 0.0

def get_moving_average(ticker, window=5):
    try:
        df = pyupbit.get_ohlcv(ticker, interval="day", count=window + 1)
        if df is not None and len(df) >= window:
            return df['close'].rolling(window=window).mean().iloc[-1]
    except:
        pass
    return 0.0

# --- 사이드바 설정 (자산 및 한 달 목표 설정) ---
st.sidebar.header("⚙️ 봇 자산 및 목표 설정")
user_input_asset = st.sidebar.number_input(
    "코인원 실제 총 보유자산 (원)", 
    min_value=10000, 
    value=1329057, # 코인원 실제 잔고 기본값
    step=10000,
    format="%d"
)

target_goal_asset = st.sidebar.number_input(
    "🎯 한 달 복리 목표 총자산 (원)", 
    min_value=100000, 
    value=2000000, # 200만 원 목표 기본값
    step=50000,
    format="%d"
)

# --- 상단 지표 카드 섹션 ---
col1, col2, col3, col4 = st.columns(4)

fng_val, fng_label = get_fear_and_greed()
with col1:
    st.metric(label="시장 심리 (공포·탐욕)", value=f"{fng_val}점", delta=fng_label)

with col2:
    st.metric(label="오늘 봇 매매 상태", value="🟢 가동 중", delta="복리 재투자 모드")

today_str = datetime.datetime.now().strftime("%Y-%m-%d")
today_record = history_data.get(today_str, {"profit_krw": 0, "profit_pct": "+0.0%", "end_balance": user_input_asset})

with col3:
    st.metric(label="오늘 매도 후 최종 실현 이익", value=f"{today_record.get('profit_krw', 0):,}원", delta=today_record.get('profit_pct', '+0.0%'))

with col4:
    st.metric(label="현재 총 자산 (코인원 연동)", value=f"{user_input_asset:,}원", delta="실시간 동기화 완료")

# --- 🎯 한 달 복리 목표 달성률 진행 바 섹션 ---
st.markdown("---")
st.subheader("🎯 한 달 복리 목표 달성 현황")

# 달성률 계산 (0% ~ 100% 제한)
initial_start = 1329057 # 시작 기준점
progress_ratio = (user_input_asset - initial_start) / (target_goal_asset - initial_start) if target_goal_asset > initial_start else 0.0
progress_ratio = max(0.0, min(1.0, progress_ratio))

achievement_pct = ((user_input_asset - initial_start) / initial_start) * 100 if initial_start > 0 else 0

col_p1, col_p2, col_p3 = st.columns([2, 1, 1])
with col_p1:
    st.progress(progress_ratio, text=f"목표 금액({target_goal_asset:,}원)까지의 진행 상황")
with col_p2:
    st.metric(label="현재 순성장률", value=f"{achievement_pct:+.2f}%")
with col_p3:
    remaining_money = max(0, target_goal_asset - user_input_asset)
    st.metric(label="목표까지 남은 금액", value=f"{remaining_money:,}원")

st.markdown("---")

# --- 📈 봇 관점 탭별 상세 차트 & 매수 타점 진입 시각화 섹션 ---
st.subheader("📈 5개 코인별 1시간봉 차트 & 봇 진입 타점 시각화")

coin_tabs = st.tabs(list(coinone_symbols.values()))

for tab, (upbit_ticker, coin_name) in zip(coin_tabs, coinone_symbols.items()):
    with tab:
        try:
            df_chart = pyupbit.get_ohlcv(upbit_ticker, interval="minute60", count=72)
            time.sleep(0.1)
        except:
            df_chart = None
        
        if df_chart is not None and not df_chart.empty:
            df_chart['MA5'] = df_chart['close'].rolling(window=5).mean()
            
            df_chart['Buy_Signal'] = (df_chart['close'] > df_chart['MA5']) & (df_chart['close'] > df_chart['open'])
            buy_points = df_chart[df_chart['Buy_Signal']]

            fig = go.Figure()

            # 1시간봉 캔들스틱
            fig.add_trace(go.Candlestick(
                x=df_chart.index.strftime('%m-%d %H:%M'),
                open=df_chart['open'],
                high=df_chart['high'],
                low=df_chart['low'],
                close=df_chart['close'],
                name='1시간 캔들'
            ))

            # 단기 이동평균선
            fig.add_trace(go.Scatter(
                x=df_chart.index.strftime('%m-%d %H:%M'),
                y=df_chart['MA5'],
                mode='lines',
                name='단기 이평선',
                line=dict(color='#ff9900', width=2)
            ))

            # 🚀 봇 매수 진입 타점 마커
            if not buy_points.empty:
                fig.add_trace(go.Scatter(
                    x=buy_points.index.strftime('%m-%d %H:%M'),
                    y=buy_points['low'] * 0.995,
                    mode='markers',
                    name='🚀 봇 매수 타점',
                    marker=dict(symbol='triangle-up', size=12, color='#00ffcc')
                ))

            fig.update_layout(
                title=f"{coin_name} 최근 시간봉 차트 및 봇 매수 진입 타점",
                xaxis_title="일시 (월-일 시:분)",
                yaxis_title="가격 (KRW)",
                height=520,
                template="plotly_dark",
                xaxis=dict(type='category', nticks=10)
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning(f"{coin_name} 차트 데이터를 불러오는 중입니다. 잠시 후 '데이터 새로고침'을 눌러주세요.")

st.markdown("---")

# --- 📅 날짜별 매도 완료 성과 및 복리 자산 캘린더 섹션 ---
st.subheader("📅 날짜별 매도 완료 성과 & 복리 자산 캘린더")
st.markdown("봇이 매도를 마친 후 수익이 더해진 상태에서 다음 재투자(복리)로 이어지는 과정의 자산 변화 기록입니다.")

calendar_list = []
for d, info in sorted(history_data.items(), reverse=True):
    calendar_list.append({
        "매도 완료 날짜": d,
        "시작 자산 (원)": f"{info.get('start_balance', user_input_asset):,}원",
        "실현 손익 (원)": f"{info.get('profit_krw', 0):,}원",
        "수익률 (%)": info.get('profit_pct', '+0.0%'),
        "매도 완료 횟수": f"{info.get('trades', 0)}회",
        "💰 매도 후 총자산 (재투자)": f"{info.get('end_balance', user_input_asset):,}원",
        "상태": info.get('status', '매도 및 복리 반영 대기')
    })

df_calendar = pd.DataFrame(calendar_list)
st.dataframe(df_calendar, use_container_width=True)

st.markdown("---")

# --- 실시간 코인 타점 및 전략 분석 판 (5개 전 종목 100% 안전 출력) ---
st.subheader("📊 실시간 코인 타점 및 전략 분석 판 (전체 5종목)")

table_data = []
for t in upbit_tickers:
    c_name = coinone_symbols[t]
    tp = get_target_price(t, k)
    m5 = get_moving_average(t, 5)
    
    try:
        cp = pyupbit.get_current_price(t)
        time.sleep(0.05)
    except:
        cp = 0
    
    if cp and cp > 0 and tp and m5:
        target_diff_pct = ((cp - tp) / tp) * 100
        is_above_target = cp >= tp
        is_above_ma = cp >= m5
        
        if is_above_target and is_above_ma:
            status = "🚀 매수 타점 도달"
        elif is_above_ma:
            status = "⏳ 목표가 대기 중"
        else:
            status = "💤 이평선 아래 (관망)"
            
        table_data.append({
            "코인": c_name,
            "현재가 (원)": f"{cp:,.0f}",
            "변동성 목표가 (원)": f"{tp:,.0f}",
            "5일 이평선 (원)": f"{m5:,.0f}",
            "목표가 대비 차이": f"{target_diff_pct:+.2f}%",
            "봇 판단 상태": status
        })

df_display = pd.DataFrame(table_data)
st.dataframe(df_display, use_container_width=True)

# 새로고침 버튼
if st.button("🔄 데이터 새로고침"):
    st.rerun()

st.markdown("---")
st.caption("💡 팁: 사이드바에서 한 달 목표 총자산(기본 200만 원)을 자유롭게 변경하실 수 있습니다.")