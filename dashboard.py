from datetime import datetime, timedelta
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# (상단 설정 및 자산/목표 코드는 그대로 유지하시고, 아래 차트 함수 부분만 교체하세요)

# --- [5. 캔들스틱 차트 & 타임프레임 연동 시간 최적화] ---
st.subheader("📊 코인별 캔들 차트 & 봇 진입 타점 시각화")

timeframe = st.selectbox(
    "⏳ 차트 타임프레임 선택", ["5분봉", "15분봉", "30분봉", "1시간봉", "1일봉"]
)

tab_btc, tab_eth, tab_xrp, tab_sol, tab_ada = st.tabs(
    ["BTC", "ETH", "XRP", "SOL", "ADA"]
)


def draw_candlestick_chart(coin_name, base_price):
  now = datetime.now()

  # 타임프레임에 따라 적절한 과거 시간 간격과 개수 설정
  if timeframe == "5분봉":
    delta = timedelta(minutes=5)
    n = 20   최근 20개 (약 1시간 40분 분량)
  elif timeframe == "15분봉":
    delta = timedelta(minutes=15)
    n = 20  # 최근 20개 (구간 5시간 분량)
  elif timeframe == "30분봉":
    delta = timedelta(minutes=30)
    n = 20  # 최근 20개 (10시간 분량)
  elif timeframe == "1시간봉":
    delta = timedelta(hours=1)
    n = 24  # 최근 24개 (하루 분량)
  else:  # 1일봉
    delta = timedelta(days=1)
    n = 30  # 최근 30일 (한 달 분량)

  # 현재 시각부터 역산하여 자연스러운 캔들 시간대 생성
  dates = [(now - delta * i).strftime("%m-%d %H:%M") for i in range(n)][::-1]

  # 가격 변동 시뮬레이션
  opens = [base_price * (1 + (i * 0.0005)) for i in range(n)]
  closes = [
      p * (1 + 0.001 * ((i % 3) - 1)) for i, p in enumerate(opens)
  ]  # pylint: disable=unused-variable
  highs = [
      max(o, c) * 1.002 for o, c in zip(opens, closes)
  ]  # pylint: disable=unused-variable
  lows = [min(o, c) * 0.998 for o, c in zip(opens, closes)]  # pylint: disable=unused-variable

  df = pd.DataFrame({"Open": opens, "High": highs, "Low": lows, "Close": closes})
  df["MA"] = df["Close"].rolling(window=5, min_periods=1).mean()

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

  # 2. 이동평균선(오렌지색) 추가
  fig.add_trace(
      go.Scatter(
          x=dates,
          y=df["MA"],
          mode="lines",
          name="단기 이평선",
          line=dict(color="orange", width=2),
      )
  )

  # 3. 매수 진입 타점 (초록색 화살표) 예시
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
      xaxis=dict(
          tickangle=0
      ),  # 날짜 글자가 꺾이지 않고 가로로 깔끔하게 나오도록 설정
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
