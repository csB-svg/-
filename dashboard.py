from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="퀀트 자동 매매 대시보드", page_icon="📈", layout="wide"
)

st.title("🚀 퀀트 자동 매매 실시간 대시보드")
st.markdown("---")

# --- [1. 사이드바 및 자산 설정] ---
st.sidebar.header("⚙️ 봇 자산 및 목표 설정")
current_total_balance = st.sidebar.number_input(
    "코인 실제 총 보유자산 (원)", value=1329057, step=10000
)
monthly_target_balance = st.sidebar.number_input(
    "한 달 복리 목표 총자산 (원)", value=2000000, step=10000
)

# --- [2. 매월 1일 자동 복리 갱신 로직] ---
now = datetime.now()
current_month = now.month

if (
    "base_month" not in st.session_state
    or st.session_state["base_month"] != current_month
):
  st.session_state["base_month"] = current_month
  st.session_state["starting_balance"] = current_total_balance
  st.session_state["start_date"] = now.date()

starting_balance = st.session_state.get(
    "starting_balance", current_total_balance
)

# --- [3. 상단 핵심 지표 (Metrics) 표시] ---
col1, col2, col3, col4 = st.columns(4)

with col1:
  st.metric(
      label="💰 현재 총 자산", value=f"{current_total_balance:,.0f} 원"
  )

with col2:
  st.metric(
      label="🎯 이달의 시작 기준", value=f"{starting_balance:,.0f} 원"
  )

with col3:
  profit_rate = (
      (current_total_balance - starting_balance) / starting_balance
  ) * 100
  st.metric(
      label="📊 이번 달 수익률",
      value=f"{profit_rate:+.2f}%",
      delta=f"{current_total_balance - starting_balance:+,.0f} 원",
  )

with col4:
  st.metric(label="🏁 한 달 목표 자산", value=f"{monthly_target_balance:,.0f} 원")

st.markdown("---")

# --- [4. 복리 목표 달성률 게이지] ---
st.subheader("📈 일 복리 및 목표 달성 현황")
progress_ratio = min(
    max(
        (current_total_balance - starting_balance)
        / (monthly_target_balance - starting_balance),
        0,
    ),
    1.0,
)
st.write(f"현재 월간 목표 달성도: **{progress_ratio * 100:.1f}%**")
st.progress(progress_ratio)

st.markdown("---")

# --- [5. 캔들스틱 차트 & 타임프레임 연동 시간 최적화] ---
st.subheader("📊 코인별 캔들 차트 & 봇 진입 타점 시각화")

timeframe = st.selectbox(
    "⏳ 차트 타임프레임 선택", ["5분봉", "15분봉", "30분봉", "1시간봉", "1일봉"]
)

tab_btc, tab_eth, tab_xrp, tab_sol, tab_ada = st.tabs(
    ["BTC", "ETH", "XRP", "SOL", "ADA"]
)


def draw_candlestick_chart(coin_name, base_price):
  now_time = datetime.now()

  if timeframe == "5분봉":
    delta = timedelta(minutes=5)
    n = 20  # 최근 20개 (약 1시간 40분 분량)
  elif timeframe == "15분봉":
    delta = timedelta(minutes=15)
    n = 20  # 최근 20개 (약 5시간 분량)
  elif timeframe == "30분봉":
    delta = timedelta(minutes=30)
    n = 20  # 최근 20개 (10시간 분량)
  elif timeframe == "1시간봉":
    delta = timedelta(hours=1)
    n = 24  # 최근 24개 (하루 분량)
  else:  # 1일봉
    delta = timedelta(days=1)
    n = 30  # 최근 30일 (한 달 분량)

  dates = [
      (now_time - delta * i).strftime("%m-%d %H:%M") for i in range(n)
  ][::-1]

  opens = [base_price * (1 + (i * 0.0005)) for i in range(n)]
  closes = [p * (1 + 0.001 * ((i % 3) - 1)) for i, p in enumerate(opens)]
  highs = [max(o, c) * 1.002 for o, c in zip(opens, closes)]
  lows = [min(o, c) * 0.998 for o, c in zip(opens, closes)]

  df = pd.DataFrame({"Open": opens, "High": highs, "Low": lows, "Close": closes})
  df["MA"] = df["Close"].rolling(window=5, min_periods=1).mean()

  fig = go.Figure()

  fig.add_trace(
      go.Candlestick(
          x=dates,
          open=df["Open"],
          high=df["High"],
          low=df["Low"],
          close=df["Close"],
          name=f"{timeframe} 캔들",
      )
  )

  fig.add_trace(
      go.Scatter(
          x=dates,
          y=df["MA"],
          mode="lines",
          name="단기 이평선",
          line=dict(color="orange", width=2),
      )
  )

  buy_x = [dates[5], dates[12]]
  buy_y = [df["Low"][5] * 0.999, df["Low"][12] * 0.999]
  fig.add_trace(
      go.Scatter(
          x=buy_x,
          y=buy_y,
          mode="markers",
          name="봇 매수 타점",
          marker=dict(symbol="triangle-up", size=10, color="#00CC96"),
      )
  )

  fig.update_layout(
      title=f"{coin_name} 최근 {timeframe} 흐름 및 진입 타점",
      xaxis_title="",
      yaxis_title="가격 (KRW)",
      height=400,
      margin=dict(l=10, r=10, t=40, b=10),
      xaxis_rangeslider_visible=False,
      xaxis=dict(tickangle=0),
  )

  st.plotly_chart(fig, use_container_width=True)


with tab_btc:
  draw_candlestick_chart("BTC", 115000000)

with tab_eth:
  draw_candlestick_chart("ETH", 3680000)

with tab_xrp:
  draw_candlestick_chart("XRP", 2070)

with tab_sol:
  draw_candlestick_chart("SOL", 158000)

with tab_ada:
  draw_candlestick_chart("ADA", 331)

st.markdown("---")

# --- [6. 매도 성과 및 실시간 상태 판] ---
st.subheader("📅 날짜별 매도 완료 성과 & 복리 자산 캘린더")
history_df = pd.DataFrame({
    "매도 완료 날짜": ["2026-09-24"],
    "시작 자산 (원)": ["1,329,057원"],
    "실현 손익 (원)": ["0원"],
    "수익률 (%)": ["+0.0%"],
    "매도 완료 횟수": ["0회"],
    "매도 후 총자산 (재투자)": ["1,329,057원"],
    "상태": ["매도 완료 대기 중"],
})
st.dataframe(history_df, use_container_width=True)

st.subheader("📋 실시간 코인 타점 및 전략 분석 판 (전체 5종목)")
status_df = pd.DataFrame({
    "코인": ["BTC", "ETH", "XRP", "SOL", "ADA"],
    "현재가 (원)": [
        "115,370,000",
        "3,686,000",
        "2,071",
        "158,000",
        "331",
    ],
    "변동성 목표가 (원)": [
        "117,374,500",
        "3,752,000",
        "2,156",
        "161,250",
        "344",
    ],
    "5일 이평선 (원)": [
        "115,041,400",
        "3,688,400",
        "2,050",
        "157,560",
        "328",
    ],
    "목표가 대비 차이": ["-1.71%", "-1.76%", "-3.94%", "-2.02%", "-3.64%"],
    "봇 판단 상태": [
        "⏳ 목표가 대기 중",
        "📉 이평선 아래 (관망)",
        "⏳ 목표가 대기 중",
        "⏳ 목표가 대기 중",
        "⏳ 목표가 대기 중",
    ],
})
st.dataframe(status_df, use_container_width=True)

if st.button("🔄 데이터 새로고침"):
  st.rerun()
