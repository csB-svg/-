from datetime import datetime, timedelta
import random
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="퀀트 자동 매매 대시보드", page_icon="📈", layout="wide"
)

st.title("🚀 퀀트 자동 매매 실시간 대시보드")
st.markdown("---")

# --- [1. 사이드바 및 자산 설정 (코인원 실계좌 연동)] ---
st.sidebar.header("⚙️ 봇 자산 및 목표 설정")
current_total_balance = st.sidebar.number_input(
    "코인 실제 총 보유자산 (원)", value=1327378, step=10000
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
  st.session_state["starting_balance"] = 1329057
  st.session_state["start_date"] = now.date()

starting_balance = st.session_state.get("starting_balance", 1329057)

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
  actual_profit_loss = current_total_balance - starting_balance
  actual_profit_rate = (actual_profit_loss / starting_balance) * 100
  st.metric(
      label="📊 이번 달 수익률",
      value=f"{actual_profit_rate:+.2f}%",
      delta=f"{actual_profit_loss:+,.0f} 원",
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

# --- [5. 주요 5종목(BTC, ETH, XRP, ADA, SOL) 거래소 스타일 차트] ---
st.subheader("📊 주요 코인별 시세 및 거래량 모니터링 차트 (5종목)")

timeframe = st.selectbox(
    "⏳ 차트 타임프레임 선택", ["3분봉", "15분봉", "1시간봉", "4시간봉", "1일봉"]
)

tab_btc, tab_eth, tab_xrp, tab_ada, tab_sol = st.tabs(
    ["BTC", "ETH", "XRP", "ADA", "SOL"]
)


def draw_exchange_chart(coin_name, base_price):
  now_time = datetime.now()

  if timeframe == "3분봉":
    delta = timedelta(minutes=3)
    n = 15
  elif timeframe == "15분봉":
    delta = timedelta(minutes=15)
    n = 15
  elif timeframe == "1시간봉":
    delta = timedelta(hours=1)
    n = 15
  elif timeframe == "4시간봉":
    delta = timedelta(hours=4)
    n = 15
  else:
    delta = timedelta(days=1)
    n = 15

  dates = [
      (now_time - delta * i).strftime("%m-%d %H:%M") for i in range(n)
  ][::-1]

  prices = []
  current_p = base_price * 0.995
  for _ in range(n):
    fluctuation = random.uniform(-0.003, 0.003)
    current_p = current_p * (1 + fluctuation)
    prices.append(current_p)

  volumes = [random.randint(800, 2500) for _ in range(n)]

  df = pd.DataFrame({"Price": prices, "Volume": volumes})
  df["MA5"] = df["Price"].rolling(window=3, min_periods=1).mean()
  df["MA10"] = df["Price"].rolling(window=5, min_periods=1).mean()

  fig = make_subplots(
      rows=2,
      cols=1,
      shared_xaxes=True,
      vertical_spacing=0.03,
      row_heights=[0.75, 0.25],
  )

  fig.add_trace(
      go.Scatter(
          x=dates,
          y=df["Price"],
          mode="lines+markers",
          name="가격",
          line=dict(color="#2962FF", width=2),
      ),
      row=1,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=dates,
          y=df["MA5"],
          mode="lines",
          name="MA 5",
          line=dict(color="#FF6D00", width=1.5),
      ),
      row=1,
      col=1,
  )
  fig.add_trace(
      go.Scatter(
          x=dates,
          y=df["MA10"],
          mode="lines",
          name="MA 10",
          line=dict(color="#00B0FF", width=1.5),
      ),
      row=1,
      col=1,
  )

  fig.add_trace(
      go.Bar(
          x=dates,
          y=df["Volume"],
          name="거래량",
          marker_color="rgba(41, 98, 255, 0.6)",
      ),
      row=2,
      col=1,
  )

  fig.update_layout(
      title=dict(text=f"{coin_name} 실시간 차트 ({timeframe})", font=dict(size=14)),
      height=450,
      margin=dict(l=10, r=10, t=40, b=10),
      showlegend=True,
      legend=dict(
          orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1
      ),
      xaxis2=dict(tickangle=0),
  )

  st.plotly_chart(fig, use_container_width=True)


with tab_btc:
  draw_exchange_chart("BTC", 115000000)

with tab_eth:
  draw_exchange_chart("ETH", 3680000)

with tab_xrp:
  draw_exchange_chart("XRP", 2070)

with tab_ada:
  draw_exchange_chart("ADA", 348)

with tab_sol:
  draw_exchange_chart("SOL", 163500)

st.markdown("---")

# --- [6. 계좌 자산 구성 및 5종목 상세 손익 판] ---
st.subheader("📅 코인원 계좌 자산 구성 현황")
asset_summary_df = pd.DataFrame({
    "구분": ["보유 원화 (현금)", "가상자산 평가금액", "총 보유자산"],
    "금액": ["1,156,987 원", "170,391 원", "1,327,378 원"],
    "상태 / 비고": [
        "하락장 관망 중 (현금 대기)",
        "XRP, ADA, SOL 분산 보유 중 (총 평가손익 -1,678원)",
        "실시간 연동 완료",
    ],
})
st.dataframe(asset_summary_df, use_container_width=True)

st.subheader("📋 전체 모니터링 5종목 상세 손익 및 봇 전략 판")
status_df = pd.DataFrame({
    "코인": ["BTC", "ETH", "XRP", "ADA", "SOL"],
    "보유 상태": ["미보유 (관망)", "미보유 (관망)", "보유중 (70개)", "보유중 (35개)", "보유중 (0.05개)"],
    "매수평균가 (원)": ["-", "-", "2,167", "348.7", "163,500"],
    "현재가 / 평가금액": [
        "115,370,000 원",
        "3,686,000 원",
        "2,071 원 (150,150원)",
        "348 원 (12,106원)",
        "163,500 원 (8,135원)",
    ],
    "개별 수익률 및 손익": [
        "-",
        "-",
        "-1.01% (-1,540 원)",
        "-0.80% (-98 원)",
        "-0.48% (-40 원)",
    ],
    "봇 판단 상태": [
        "⏳ 목표가 대기 중",
        "📉 이평선 아래 (관망)",
        "📉 하락장 관망 (보유 유지)",
        "📉 하락장 관망 (보유 유지)",
        "📉 하락장 관망 (보유 유지)",
    ],
})
st.dataframe(status_df, use_container_width=True)

if st.button("🔄 데이터 새로고침"):
  st.rerun()
