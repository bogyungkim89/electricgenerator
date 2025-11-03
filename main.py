import streamlit as st
import numpy as np
import matplotlib.pyplot as plt

# Streamlit 앱 제목 설정
st.title("⚡️ 직류형 발전기 시뮬레이터")
st.markdown("### 코일 회전에 따른 기전력 변화 시뮬레이션")

# --- 사용자 입력 컨트롤 ---
st.sidebar.header("시뮬레이션 컨트롤")
# 회전 각도를 슬라이더로 조절하거나 자동 회전 체크박스 추가
angle_deg = st.sidebar.slider("코일 회전 각도 (도)", 0, 360, 0)
angle_rad = np.deg2rad(angle_deg)

# --- 1. 발전기 구조 시각화 영역 ---
st.header("1. 발전기 구조 및 회전")
# (여기에 자석, 코일, 정류자, 브러시를 나타내는 시각화 코드를 삽입)
# 예: 코일의 2D 평면도 시각화 (회전 각도에 따른 코일의 상대적 위치 변화)

# --- 2. 물리량 계산 ---
# 유도 기전력 공식: E = E_max * sin(omega*t) -> 교류
# 정류자 적용 시: E_DC = E_max * |sin(omega*t)| -> 직류 (맥동)

# B: 자기장 세기, A: 코일 면적, N: 코일 감은 횟수, w: 각속도 (상수로 가정)
B, A, N, w = 1.0, 1.0, 1.0, 1.0

# 시간 t 대신 각도 theta 사용
theta = np.linspace(0, 2 * np.pi, 360) 

# 자속 변화: Phi = N B A cos(theta)
flux = N * B * A * np.cos(theta) 

# 유도 기전력 (교류): E = -N * d(Phi)/dt = N B A w sin(theta) 
# 미분 근사 또는 공식 사용: E_AC = N * B * A * w * np.sin(theta)

# 유도 기전력 (직류): 정류자 적용으로 |sin(theta)|
E_max = N * B * A * w
E_DC = E_max * np.abs(np.sin(theta))

# --- 3. 그래프 분석 영역 ---
st.header("2. 자기선속 및 유도 기전력 그래프")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)

# 1. 자기선속 그래프
ax1.plot(np.rad2deg(theta), flux, label='자기선속 $\Phi$')
ax1.set_ylabel('자기선속 $\Phi$')
ax1.grid(True)
ax1.axvline(angle_deg, color='r', linestyle='--', label=f'현재 각도: {angle_deg}°')
ax1.legend()

# 2. 유도 기전력 (DC 출력) 그래프
ax2.plot(np.rad2deg(theta), E_DC, color='orange', label='유도 기전력 $E$ (DC 출력)')
ax2.set_xlabel('코일 회전 각도 (도)')
ax2.set_ylabel('유도 기전력 $E$')
ax2.grid(True)
ax2.axvline(angle_deg, color='r', linestyle='--')
ax2.legend()

# 현재 각도의 출력 전압 표시
current_E_DC = E_max * np.abs(np.sin(angle_rad))
ax2.plot(angle_deg, current_E_DC, 'ro') # 현재 위치에 점 찍기
st.markdown(f"**현재 회전 각도({angle_deg}°):** 유도 기전력 = **{current_E_DC:.2f} V**")


st.pyplot(fig)
