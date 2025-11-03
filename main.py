import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Wedge
import time

# ---------------------------------------------
# 기본 설정
# ---------------------------------------------
st.set_page_config(page_title="직류형 발전기 시뮬레이터", layout="wide")
st.title("🔌 직류형 발전기 (DC Generator) 시뮬레이터")

st.markdown("""
코일이 자석 사이에서 회전하면서, 코일을 수직으로 통과하는 자기장의 세기 변화와 그 변화율을 확인할 수 있습니다.  
**[시작]** 버튼을 누르면 코일이 회전하며, 그래프가 시간에 따라 변화합니다.
""")

# ---------------------------------------------
# 고정된 물리 상수
# ---------------------------------------------
omega = 2.0             # 각속도 (rad/s)
B0 = 0.8                # 자기장 세기 (T)
coil_width = 0.1        # m
coil_height = 0.08      # m
dt = 0.05               # 시간 간격 (s)
max_time = 10.0         # 시뮬레이션 최대 시간

# ---------------------------------------------
# 세션 상태 초기화
# ---------------------------------------------
if "running" not in st.session_state:
    st.session_state.running = False
if "time_series" not in st.session_state:
    st.session_state.time_series = []
if "B_series" not in st.session_state:
    st.session_state.B_series = []
if "dBdt_series" not in st.session_state:
    st.session_state.dBdt_series = []
if "angle" not in st.session_state:
    st.session_state.angle = 0.0
if "time" not in st.session_state:
    st.session_state.time = 0.0

# ---------------------------------------------
# 회전 토글 버튼
# ---------------------------------------------
col_btn = st.columns([1,1,5])
with col_btn[0]:
    if st.button("▶ 시작 / ⏸ 정지"):
        st.session_state.running = not st.session_state.running

# ---------------------------------------------
# 시각화용 함수
# ---------------------------------------------
def draw_scene(angle):
    fig, ax = plt.subplots(figsize=(5,5))
    ax.set_xlim(-0.6, 0.6)
    ax.set_ylim(-0.5, 0.5)
    ax.set_aspect('equal')
    ax.axis("off")

    # 자석 표시
    mag_w, mag_h = 0.18, 0.5
    ax.add_patch(Rectangle((-0.5-mag_w/2, -mag_h/2), mag_w, mag_h, facecolor="#a83232"))
    ax.text(-0.5, 0.55, "N", fontsize=14, ha="center")
    ax.add_patch(Rectangle((0.5-mag_w/2, -mag_h/2), mag_w, mag_h, facecolor="#3273a8"))
    ax.text(0.5, 0.55, "S", fontsize=14, ha="center")

    # 코일 회전
    corners = np.array([
        [-coil_width/2, -coil_height/2],
        [coil_width/2, -coil_height/2],
        [coil_width/2, coil_height/2],
        [-coil_width/2, coil_height/2],
    ])
    R = np.array([[np.cos(angle), -np.sin(angle)], [np.sin(angle), np.cos(angle)]])
    rc = corners @ R.T
    ax.add_patch(plt.Polygon(rc, fill=False, edgecolor="black", linewidth=2))

    # 코일 축 방향 벡터 (normal)
    nx, ny = np.cos(angle) * 0.2, np.sin(angle) * 0.2
    ax.arrow(0, 0, nx, ny, head_width=0.03, head_length=0.04, color="k")
    ax.text(-0.55, 0.45, f"θ = {np.rad2deg(angle)%360:.1f}°", fontsize=10)

    # 정류자
    comm_r = 0.05
    seg1 = Wedge((0,0), comm_r, 0, 180, color="orange")
    seg2 = Wedge((0,0), comm_r, 180, 360, color="brown")
    ax.add_patch(seg1)
    ax.add_patch(seg2)
    ax.text(0, -0.25, "정류자", ha="center")

    return fig

# ---------------------------------------------
# 데이터 갱신 함수
# ---------------------------------------------
def update_simulation():
    st.session_state.angle += omega * dt
    st.session_state.time += dt
    t = st.session_state.time
    angle = st.session_state.angle

    # 코일을 수직으로 통과하는 자기장 성분: B_perp = B0 * cos(theta)
    B_perp = B0 * np.cos(angle)
    dBdt = -B0 * omega * np.sin(angle)

    st.session_state.time_series.append(t)
    st.session_state.B_series.append(B_perp)
    st.session_state.dBdt_series.append(dBdt)

# ---------------------------------------------
# 실행 루프
# ---------------------------------------------
if st.session_state.running:
    for _ in range(5):  # 한 번 실행할 때 5프레임씩 갱신
        update_simulation()
        if st.session_state.time > max_time:
            st.session_state.running = False
            break
    time.sleep(0.05)

# ---------------------------------------------
# 시각화 표시
# ---------------------------------------------
col1, col2, col3 = st.columns([1.2, 1, 1])
with col1:
    st.pyplot(draw_scene(st.session_state.angle))
with col2:
    fig1, ax1 = plt.subplots()
    ax1.plot(st.session_state.time_series, st.session_state.B_series, color="blue")
    ax1.set_title("시간에 따른 코일 수직 자기장 성분 (B⊥)")
    ax1.set_xlabel("시간 (s)")
    ax1.set_ylabel("B⊥ (T)")
    st.pyplot(fig1)
with col3:
    fig2, ax2 = plt.subplots()
    ax2.plot(st.session_state.time_series, st.session_state.dBdt_series, color="red")
    ax2.set_title("시간에 따른 자기장 변화율 (dB⊥/dt)")
    ax2.set_xlabel("시간 (s)")
    ax2.set_ylabel("dB⊥/dt (T/s)")
    st.pyplot(fig2)

st.markdown("""
---
### ⚙️ 시뮬레이션 설명
- 코일은 반시계 방향으로 일정한 각속도 ω=2 rad/s로 회전합니다.  
- 코일의 면에 수직인 자기장 성분은 \( B_⊥ = B_0 \cos(θ) \) 로 변합니다.  
- 이에 따른 자기장 변화율은 \( \frac{dB_⊥}{dt} = -B_0 ω \sin(θ) \) 입니다.  
- 정류자(commutator)는 코일의 방향이 바뀔 때 전류 방향을 반대로 바꿔, 전체 출력이 **직류처럼 보이도록** 합니다.
""")
