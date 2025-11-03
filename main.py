import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyBboxPatch, Circle, Wedge
import time

st.set_page_config(page_title="DC Generator Simulator", layout="wide")
st.title("🔌 직류형 발전기(DC Generator) 시뮬레이터")
st.markdown(
    """
    **설명**: 사각형 코일이 자석 사이에서 회전하면서 발생하는 자속(Φ)과 유도기전력(ε)을 계산하고,
    정류자(commutator)로 출력이 어떻게 직류(정류)되는지 시각화합니다.
    """
)

# ----- 시뮬레이션 파라미터 UI -----
col1, col2, col3 = st.columns([1, 1, 1])
with col1:
    speed = st.slider("각속도 ω (rad/s)", 0.1, 10.0, 2.0, step=0.1)
    direction = st.selectbox("회전 방향", ["반시계(CCW)", "시계(CW)"])
with col2:
    coil_width = st.slider("코일 가로 (m)", 0.02, 0.3, 0.1, step=0.01)
    coil_height = st.slider("코일 세로 (m)", 0.02, 0.3, 0.08, step=0.01)
with col3:
    B0 = st.slider("자기장 강도 (T) — 자석 사이 평균", 0.1, 2.0, 0.8, step=0.05)
    area = coil_width * coil_height
    st.write(f"코일 면적 A = {area:.4f} m²")

st.write("---")

# Controls for stepping / play
play = st.button("Play (자동, 200 프레임)")
step = st.button("Step (한 프레임 진행)")
angle_slider = st.slider("각도 θ (deg) — 직접 조정", 0, 359, 0)
# keep internal angle in session state for continuity
if "angle" not in st.session_state:
    st.session_state.angle = np.deg2rad(angle_slider)
else:
    # if user moved slider, update angle
    if angle_slider is not None:
        st.session_state.angle = np.deg2rad(angle_slider)

# Simulation functions ----------------------------------------------------
def magnetic_field_grid(X, Y, mag1_pos=(-0.3, 0.0), mag2_pos=(0.3, 0.0), mag_strength=1.0):
    """
    두 자석을 단순한 쌍극자 근사로 두고 그 합으로 Bx, By 계산.
    (간단한 시뮬레이션 목적 — 물리적 정확성보다 시각화에 중점)
    """
    # dipole-like fields centered at mag positions
    def dipole(px, py, X, Y, m=1.0):
        rx = X - px
        ry = Y - py
        r2 = rx**2 + ry**2 + 1e-6
        r5 = r2**2.5
        # 2D-ish surrogate: field ~ m*(2x^2 - y^2)/r^? (approx) but we'll use simple radial falloff
        Bx = m * rx / (r2**1.5)
        By = m * ry / (r2**1.5)
        return Bx, By

    Bx1, By1 = dipole(mag1_pos[0], mag1_pos[1], X, Y, m=mag_strength)
    Bx2, By2 = dipole(mag2_pos[0], mag2_pos[1], X, Y, m=-mag_strength)  # opposite pole
    # add a uniform background from left->right for clearer field between magnets
    Bx_uniform = np.ones_like(X) * (0.0)
    By_uniform = np.zeros_like(X)
    Bx = Bx1 + Bx2 + Bx_uniform
    By = By1 + By2 + By_uniform
    # scale to approximate desired average B0 magnitude between magnets
    mag = np.sqrt(Bx**2 + By**2)
    # avoid division by zero
    mag_mean = np.mean(mag)
    if mag_mean > 0:
        scale = B0 / mag_mean
        Bx *= scale
        By *= scale
    return Bx, By

def coil_corners(center=(0.0, 0.0), w=0.1, h=0.08, theta=0.0):
    # return rectangle corners (4x2) rotated by theta about center
    cx, cy = center
    corners = np.array([[-w/2, -h/2], [w/2, -h/2], [w/2, h/2], [-w/2, h/2]])
    R = np.array([[np.cos(theta), -np.sin(theta)], [np.sin(theta), np.cos(theta)]])
    rc = (corners @ R.T) + np.array([cx, cy])
    return rc

def flux_through_coil(B_field_mag, theta):
    """
    간단 모델: 코일의 자속 Φ = B_eff * A * cos(theta)
    B_eff은 코일 중심에서의 B (z방향을 가정) — 여기서는 B_field_mag을 사용.
    """
    # B_field_mag: scalar representing effective perpendicular B at coil center
    return B_field_mag * area * np.cos(theta)

def induced_emf(phi, dt):
    # ε = -dΦ/dt
    # phi: array of recent flux values; use last two points
    if len(phi) < 2:
        return 0.0
    return -(phi[-1] - phi[-2]) / dt

# Visualization function --------------------------------------------------
def render_frame(theta_rad, t, ax_field, ax_coil, ax_plot, Bgrid_cache=None):
    # --- field plot on ax_field ---
    ax_field.clear()
    ax_field.set_title("자석과 자기력선 (top view)")
    ax_field.set_xlim(-0.8, 0.8)
    ax_field.set_ylim(-0.6, 0.6)
    ax_field.set_aspect('equal')
    # draw two magnets as rectangles
    mag_w = 0.18
    mag_h = 0.5
    # left: North up (colorless simple)
    ax_field.add_patch(Rectangle((-0.5-mag_w/2, -mag_h/2), mag_w, mag_h, facecolor="#a83232", alpha=0.9))
    ax_field.text(-0.5, 0.55, "N", ha='center')
    ax_field.add_patch(Rectangle((0.5-mag_w/2, -mag_h/2), mag_w, mag_h, facecolor="#3273a8", alpha=0.9))
    ax_field.text(0.5, 0.55, "S", ha='center')
    # vector field
    X, Y = np.meshgrid(np.linspace(-0.8,0.8,40), np.linspace(-0.6,0.6,30))
    Bx, By = magnetic_field_grid(X, Y)
    ax_field.streamplot(X, Y, Bx, By, density=1.0, linewidth=0.6, arrowsize=1)
    # draw coil
    corners = coil_corners(center=(0.0, 0.0), w=coil_width, h=coil_height, theta=theta_rad)
    ax_field.add_patch(plt.Polygon(corners, closed=True, fill=False, edgecolor='k', linewidth=2))
    # mark coil normal (perpendicular) vector for clarity
    # coil plane is rectangle; normal (out of plane) represented by angle theta: but we'll draw arrow showing area-normal projection
    # also show a small arrow through center indicating orientation
    cx, cy = 0.0, 0.0
    # draw a line representing coil axis (wire orientation) and normal vector
    # coil normal (for flux) is along +z; in 2D we show projection direction (cosine dependence)
    axis_x = np.cos(theta_rad) * coil_height/2
    axis_y = np.sin(theta_rad) * coil_height/2
    ax_field.arrow(cx, cy, axis_x, axis_y, head_width=0.02, head_length=0.03)
    ax_field.text(-0.75, 0.5, f"t={t:.2f}s\nθ={np.rad2deg(theta_rad)%360:.1f}°")

    # --- coil close-up + commutator on ax_coil ---
    ax_coil.clear()
    ax_coil.set_title("코일 & 정류자 (commutator) 표시")
    ax_coil.set_xlim(-0.5, 0.5)
    ax_coil.set_ylim(-0.5, 0.5)
    ax_coil.set_aspect('equal')
    # coil rectangle (thicker lines)
    corners = coil_corners(center=(0.0, 0.0), w=coil_width, h=coil_height, theta=theta_rad)
    ax_coil.add_patch(plt.Polygon(corners, closed=True, fill=False, edgecolor='black', linewidth=3))
    # commutator: two semi-circular segments attached to axle at center; brushes at top
    comm_r = 0.05
    seg1 = Wedge((0,0), comm_r, 0, 180)  # top segment
    seg2 = Wedge((0,0), comm_r, 180, 360)  # bottom
    ax_coil.add_patch(seg1)
    ax_coil.add_patch(seg2)
    # brushes (stationary) at left/right (contacts)
    brush_y = 0.12
    ax_coil.add_patch(Rectangle((-0.12, brush_y), 0.08, 0.02, facecolor="gray"))
    ax_coil.add_patch(Rectangle((0.04, brush_y), 0.08, 0.02, facecolor="gray"))
    ax_coil.text(-0.08, brush_y+0.03, "Brush A", fontsize=8)
    ax_coil.text(0.08, brush_y+0.03, "Brush B", fontsize=8)

    # wires from brushes to external circuit shown schematically
    # draw simple wires as lines
    ax_coil.plot([-0.08, -0.5], [brush_y+0.01, brush_y+0.01], linestyle='-', linewidth=2)
    ax_coil.plot([0.12, 0.5], [brush_y+0.01, brush_y+0.01], linestyle='-', linewidth=2)
    ax_coil.text(-0.5, brush_y+0.03, "외부 회로 (부하)", fontsize=9)

    ax_coil.axis('off')

    # --- time-series plot (flux and emf) on ax_plot ---
    # ax_plot will be drawn by outer code with data arrays
    return

# Main simulation loop / stepping logic ----------------------------------
# storage for time series
if "t_series" not in st.session_state:
    st.session_state.t_series = []
if "phi_series" not in st.session_state:
    st.session_state.phi_series = []
if "emf_series" not in st.session_state:
    st.session_state.emf_series = []
if "time" not in st.session_state:
    st.session_state.time = 0.0

dt = 0.05  # time step for numerical derivative and stepping (s)
omega = speed if direction == "반시계(CCW)" else -speed

def single_step():
    # advance angle and compute flux/emf
    st.session_state.angle += omega * dt
    st.session_state.time += dt
    # estimate effective B at coil center (we use magnitude of B field at center)
    Bx_c, By_c = magnetic_field_grid(np.array([[0.0]]), np.array([[0.0]]))
    B_eff = np.sqrt(Bx_c[0,0]**2 + By_c[0,0]**2)
    phi_new = flux_through_coil(B_eff, st.session_state.angle)
    st.session_state.phi_series.append(phi_new)
    st.session_state.t_series.append(st.session_state.time)
    emf_new = induced_emf(st.session_state.phi_series, dt)
    # commutator: rectify sign every half turn -> output = sign-flip equivalent -> model by absolute value
    emf_rectified = abs(emf_new)
    st.session_state.emf_series.append(emf_rectified)
    return

# If user clicked Step or Play, advance accordingly
if step:
    single_step()

if play:
    frames = 200
    # run a limited number of frames to avoid indefinite blocking
    for i in range(frames):
        single_step()
        # render each frame
        fig = plt.figure(figsize=(12,4))
        gs = fig.add_gridspec(1,3, width_ratios=[1.2,1,1])
        ax_field = fig.add_subplot(gs[0,0])
        ax_coil = fig.add_subplot(gs[0,1])
        ax_plot = fig.add_subplot(gs[0,2])
        render_frame(st.session_state.angle, st.session_state.time, ax_field, ax_coil, ax_plot)
        # time-series plot: top shows raw Φ and instantaneous (AC) emf estimated, bottom shows rectified output
        ax_plot.clear()
        ax_plot.set_title("자속 Φ(t)와 정류된 유도기전력 출력(모형)")
        if len(st.session_state.t_series) > 0:
            ax_plot.plot(st.session_state.t_series, st.session_state.phi_series, label="Φ (Wb)")
            # approximate AC emf from derivative: compute central differences for smoother display
            emf_ac = []
            pts = st.session_state.phi_series
            for k in range(len(pts)):
                if k==0:
                    emf_ac.append(0)
                else:
                    emf_ac.append(-(pts[k]-pts[k-1])/dt)
            ax_plot.plot(st.session_state.t_series, emf_ac, label="AC ε (V)", linestyle='--')
            ax_plot.plot(st.session_state.t_series, st.session_state.emf_series, label="정류 후 출력 (모형)", linewidth=2)
            ax_plot.legend()
        ax_plot.set_xlabel("time (s)")
        plt.tight_layout()
        st.pyplot(fig)
        time.sleep(0.03)  # small pause for animation feel

# Always render current state frame + time-series chart (non-blocking)
fig = plt.figure(figsize=(12,4))
gs = fig.add_gridspec(1,3, width_ratios=[1.2,1,1])
ax_field = fig.add_subplot(gs[0,0])
ax_coil = fig.add_subplot(gs[0,1])
ax_plot = fig.add_subplot(gs[0,2])
render_frame(st.session_state.angle, st.session_state.time, ax_field, ax_coil, ax_plot)

# draw time-series
ax_plot.clear()
ax_plot.set_title("자속 Φ(t)와 정류된 유도기전력 출력(모형)")
if len(st.session_state.t_series) > 0:
    ax_plot.plot(st.session_state.t_series, st.session_state.phi_series, label="Φ (Wb)")
    emf_ac = []
    pts = st.session_state.phi_series
    for k in range(len(pts)):
        if k==0:
            emf_ac.append(0)
        else:
            emf_ac.append(-(pts[k]-pts[k-1])/dt)
    ax_plot.plot(st.session_state.t_series, emf_ac, label="AC ε (V)", linestyle='--')
    ax_plot.plot(st.session_state.t_series, st.session_state.emf_series, label="정류 후 출력 (모형)", linewidth=2)
    ax_plot.legend()
ax_plot.set_xlabel("time (s)")
plt.tight_layout()
st.pyplot(fig)

st.write("설명:")
st.markdown(
    """
- **자력선**: 두 자석을 단순 쌍극자 근사로 표현한 벡터장에서 `streamplot`으로 그렸습니다.
- **코일 자속 Φ**: 단일 값 근사로 `Φ = B_eff * A * cos(θ)` 를 사용했습니다 (B_eff은 코일 중심에서의 자장 크기).
- **유도기전력 ε**: 수치미분으로 계산 `ε = -dΦ/dt` (그래프의 AC 곡선).
- **정류자(Commutator)**: 물리적 접촉을 모사하기 위해 간단히 `|ε|` (절댓값)으로 정류된 출력을 표시했습니다.
"""
)

st.write("---")
st.caption("이 시뮬레이터는 교육용 및 시각화 목적의 모형입니다. 물리적으로 완전한 3D 전자기 해석을 대체하지 않습니다.")
