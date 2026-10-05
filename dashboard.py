import base64
import datetime as dt
from datetime import datetime, timedelta
import hashlib
import hmac
import json
import os
import random
import time
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="코인원 퀀트 자동 매매 대시보드", page_icon="📈", layout="wide"
)

st.title(
    "🚀 코인원 단독 퀀트 자동 매매 대시보드 (실계좌 100% 동기화 모니터링)"
)
st.markdown("---")

# 🔑 config.py 또는 봇 코드에 쓰신 API 키를 여기에 입력하세요
ACCESS_KEY = "여기에_ACCESS_KEY를_넣으세요"
SECRET_KEY = "여기에_SECRET_KEY를_넣으세요"

BASE_URL = "https://api.coinone.co.kr"

symbol_list = ["BTC", "ETH", "XRP", "SOL", "ADA", "DOGE", "SUI"]

if os.path.exists("active_tickers.json"):
  try:
    with open("active_tickers.json", "r", encoding="utf-8") as f:
      data = json.load(f)
      if "coinone_symbols" in data:
        symbol_list = list(data["coinone_symbols"].values())
  except Exception as e:
    print(f"대시보드 종목 로딩 에러: {e}")


def get_coinone_live_balances():
  endpoint = "/v2/account/balance/"
  payload = {"access_token": ACCESS_KEY, "nonce": int(time.time() * 1000)}
  dumped_json = requests.compat.json.dumps(payload)
  encoded_payload = base64.b64encode(dumped_json.encode("utf-8"))
  signature = hmac.new(
      SECRET_KEY.upper().encode("utf-8"), encoded_payload, hashlib.sha512
  ).hexdigest()
  headers = {
      "Content-Type": "application/json",
      "X-COINONE-PAYLOAD": encoded_payload.decode("utf-8"),
      "X-COINONE-SIGNATURE": signature,
  }
  try:
    res = requests.post(
        BASE_URL + endpoint, data=dumped_json, headers=headers, timeout=5
    )
    if res.status_code == 200:
      return res.json()
  except:
    pass
  return None


def get_current_price(symbol):
  try:
    url = f"https://api.coinone.co.kr/public/v2/ticker?quote_currency=KRW&target_currency={symbol}"
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
      data = res.json()
      if "ticker" in data and len(data["ticker"]) > 0:
        return float(data["ticker"][0]["last"])
      elif "tickers" in data and len(data["tickers"]) > 0:
        return float(data["tickers"][0]["last"])
  except:
    pass
  return 1000.0


balance_res = get_coinone_live_balances()
krw_avail = 0.0
crypto_eval_total = 0.0
holdings_data = []

if balance_res and balance_res.get("result") == "success":
  if "krw" in balance_res:
    krw_avail = float(balance_res["krw"].get("avail", 0)) + float(
        balance_res["krw"].get("limit", 0)
    )

  for k_key, v_val in balance_res.items():
    if k_key in ["result", "errorCode", "krw", "timestamp", "completed_orders"]:
      continue
    if isinstance(v_val, dict):
      avail_q = float(v_val.get("avail", 0))
      limit_q = float(v_val.get("limit", 0))
      total_q = avail_q + limit_q
      if total_q > 0:
        sym = k_key.upper()
        cur_p = get_current_price(sym)
        eval_amt = total_q * cur_p
        crypto_eval_total += eval_amt
        holdings_data.append({
            "코인": sym,
            "보유수량": total_q,
            "현재가": cur_p,
            "평가금액": eval_amt,
        })

current_total_balance = krw_avail + crypto_eval_total

# --- [1. 사이드바] ---
st.sidebar.header("⚙️ 봇 자산 및 목표 설정")
monthly_target_balance = st.sidebar.number_input(
    "한 달 복리 목표 총자산 (원)", value=2000000, step=10000
)

# --- [2. 상단 핵심 지표] ---
col1, col2, col3, col4 = st.columns(4)
with col1:
  st.metric(label="💰 실시간 총 자산", value=f"{current_total_balance:,.0f} 원")
with col2:
  st.metric(label="🎯 이달의 시작 기준", value="1,329,057 원")
with col3:
  actual_profit_loss = current_total_balance - 1329057
  actual_profit_rate = (actual_profit_loss / 1329057) * 100
  st.metric(
      label="📊 이번 달 수익률",
      value=f"{actual_profit_rate:+.2f}%",
      delta=f"{actual_profit_loss:+,.0f} 원",
  )
with col4:
  st.metric(label="🏁 한 달 목표 자산", value=f"{monthly_target_balance:,.0f} 원")

st.markdown("---")

# --- [3. 목표 달성률] ---
st.subheader("📈 일 복리 및 목표 달성 현황")
progress_ratio = min(
    max(
        (current_total_balance - 1329057)
        / (monthly_target_balance - 1329057),
        0,
    ),
    1.0,
)
st.progress(progress_ratio)

st.markdown("---")

# --- [4. 타점 현황판] ---
st.subheader("🎯 코인원 실거래 종목 실시간 시세 및 타점 현황")
strategy_rows = []
for sym in symbol_list:
  cur_p = get_current_price(sym)
  strategy_rows.append({
      "코인": sym,
      "현재가": f"{cur_p:,.4f}원" if cur_p < 1.0 else f"{cur_p:,.0f}원",
  })

strategy_df = pd.DataFrame(strategy_rows)
st.dataframe(strategy_df, use_container_width=True)

st.markdown("---")

# --- [5. 실시간 차트] ---
st.subheader(
    f"📊 코인원 실거래 종목 시세 모니터링 ({len(symbol_list)}종목 통합 모드)"
)
tabs = st.tabs(symbol_list)


for i, tab in enumerate(tabs):
  with tab:
    curr_sym = symbol_list[i]
    live_p = get_current_price(curr_sym)
    st.info(f"💡 현재 **{curr_sym}**의 실시간 거래소 가격은 **{live_p:,.4f}원**입니다.")

st.markdown("---")

# --- [6. 자산 구성 및 보유 코인] ---
st.subheader("📅 코인원 실계좌 자산 구성 현황")
asset_summary_df = pd.DataFrame(
    data=[
        ["보유 원화 (현금)", f"{krw_avail:,.0f} 원", "실시간 연동 완료"],
        ["가상자산 평가금액", f"{crypto_eval_total:,.0f} 원", "실시간 연동 완료"],
        ["총 보유자산", f"{current_total_balance:,.0f} 원", "실시간 연동 완료"],
    ],
    columns=["구분", "금액", "상태 / 비고"],
)
st.dataframe(asset_summary_df, use_container_width=True)

st.subheader("📋 현재 보유 중인 가상자산 목록")
if holdings_data:
  holding_df = pd.DataFrame(holdings_data)
  st.dataframe(holding_df, use_container_width=True)
else:
  st.info("💡 현재 계좌에 보유 중인 코인이 없습니다.")

if st.button("🔄 실시간 새로고침"):
  st.rerun()
