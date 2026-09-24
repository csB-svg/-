from datetime import datetime
import pandas as pd
import streamlit as st  # 필요에 따라 업비트 연동 라이브러리 (pyupbit 등) 추가 가능

# 페이지 기본 설정 (모바일에서도 보기 좋게 넓은 레이아웃 사용)
st.set_page_config(
    page_title="퀀트 자동 매매 대시보드", page_icon="📈", layout="wide"
)

st.title("🚀 퀀트 자동 매매 실시간 대시보드")
st.markdown("---")

# --- [1. 임시 데이터 및 변수 설정 (실제 봇 환경에 맞게 연동하세요)] ---
# 현재 총 자산 (예시: 현재 1,329,057원)
current_total_balance = 1329057
# 한 달 목표 자산 (예시: 2,000,000원)
monthly_target_balance = 2000000

# --- [2. 매월 1일 자동 복리 갱신 로직 (Session State 활용)] ---
now = datetime.now()
current_month = now.month

if (
    "base_month" not in st.session_state
    or st.session_state["base_month"] != current_month
):
  # 매월 1일이 되었거나 앱 최초 실행 시, 현재 자산을 이번 달의 새로운 시작 기준금액으로 자동 설정
  st.session_state["base_month"] = current_month
  st.session_state["starting_balance"] = current_total_balance
  st.session_state["start_date"] = now.date()

# 이번 달 기준 시작 자산 가져오기
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
  # 이번 달 시작 금액 대비 현재 수익률 계산
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

# --- [4. 복리 목표 달성률 게이지 및 시각화] ---
st.subheader("📈 일 복리 및 목표 달성 현황")

# 목표 진행도 계산 (시작 기준금액 대비 현재 자산 / 목표 자산)
# 0 ~ 100% 사이로 고정
progress_ratio = min(
    max(
        (current_total_balance - starting_balance)
        / (monthly_target_balance - starting_balance),
        0,
    ),
    1.0,
)

st.write(
    f"현재 월간 목표 달성도: **{progress_ratio * 100:.1f}%** (기준일: 조절된"
    f" 월초)"
)
st.progress(progress_ratio)

# --- [5. 하단 세부 정보 영역] ---
st.markdown("---")
st.info(
    f"💡 **안내**: 매월 1일이 되면 전월 말일의 최종 자산이 새로운 시작 기준으로"
    f" 자동 갱신되며 일 복리(1~1.5%) 목표 계산이 산뜻하게 재시작됩니다. (현재"
    f" 접속 환경: 클라우드 실시간 모니터링 중)"
)
