from datetime import datetime
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

# --- [5. 캔들스틱 차트 & 이평선 & 매수 타점 시각화] ---
st.subheader("📊 코인별 캔들 차트 & 봇 진입 타점 시각화")

timeframe = st.selectbox(
    "⏳ 차트 타임프레임 선택", ["5분봉", "15분봉", "30분봉", "1시간봉", "1일봉"]
)

tab_btc, tab_eth, tab_xrp, tab_sol, tab_ada = st.tabs(
    ["BTC", "ETH", "XRP", "SOL", "ADA"]
)


def draw_candlestick_chart(coin_name, base_price):
  # 예시용 캔들 데이터 생성 (시가, 고가, 저가, 종가)
  dates = [
      "09-21 15:00",
      "09-21 23:00",
      "09-22 07:00",
      "09-22 15:00",
      "09-22 23:00",
      "09-23 07:00",
      "09-23 15:00",
      "09-23 23:00",
      "09-24 07:00",
  ]
  n = len(dates)

  # 가격 변동 시뮬레이션
  opens = [
      base_price * (1 + (i * 0.001)) for i in range(n)
  ]  # pylint: disable=unused-variable
  closes = [p * (1 + 0.002 * (i % 2 - 0.5)) for i, p in enumerate(opens)]
  highs = [
      max(o, c) * 1.004 for o, c in zip(opens, closes)
  ]  # pylint: disable=unused-variable
  lows = [min(o, c) * 0.996 for o, c in zip(opens, closes)]  # pylint: disable=unused-variable

  # 이동평균선(오렌지색 선) 계산용 임시 데이터
  df = pd.DataFrame({"Open": opens, "High": highs, "Low": lows, "Close": closes})
  df["MA"] = df["Close"].rolling(window=3, min_periods=1).mean()

  fig = go.Figure()

  # 1. 캔들스틱 추가
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

  # 2. 단기 이평선(오렌지색) 추가
  fig.add_trace(
      go.Scatter(
          x=dates,
          y=df["MA"],
          mode="lines",
          name="단기 이평선",
          line=dict(color="orange", width=2),
      )
  )

  # 3. 매수 진입 타점 (초록색 화살표 🎯) 추가 예시
  buy_x = [dates[2], dates[5]]
  buy_y = [df["Low"][2] * 0.998, df["Low"][5] * 0.998]
  fig.add_trace(
      go.Scatter(
          x=buy_x,
          y=buy_y,
          mode="markers",
          name="봇 매수 타점",
          marker=dict(symbol="triangle-up", size=12, color="#00CC96"),
      )
  )

  fig.update_layout(
      title=f"{coin_name} 최근 {timeframe} 차트 및 봇 매수 진입 타점",
      xaxis_title="일시 (월-일 시:분)",
      yaxis_title="가격 (KRW)",
      height=450,
      margin=dict(l=10, r=10, t=40, b=10),
      xaxis_rangeslider_visible=False,  # 하단 슬라이더 숨김 (깔끔한 UI)
  )

  st.plotly_chart(fig, use_container_width=True)


with tab_btc:
  draw_candlestick_chart("BTC", 114000000)

with tab_eth:
  draw_candlestick_chart("ETH", 3650000)

with tab_xrp:
  draw_candlestick_chart("XRP", 2050)

with tab_sol:
  draw_candlestick_chart("SOL", 156000)

with tab_ada:
  draw_candlestick_chart("ADA", 328)

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
