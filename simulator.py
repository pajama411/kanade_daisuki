import matplotlib.pyplot as plt
import plotly.graph_objects as go
import streamlit as st

class SimulationResult:
    def __init__(self, times_min, o2_pct, co2_pct):
        self.times_min = times_min
        self.o2_pct = o2_pct
        self.co2_pct = co2_pct

def run_simulation(room_volume_m3, people, plants, ach, duration_min, dt_min, light_on):
    """
    단순 시뮬레이션 예제:
    시간 경과에 따라 O2는 점점 줄고 CO2는 증가하는 간단 모델.
    식물 있으면 광합성으로 O2 증가, CO2 감소 효과 포함.
    """
    times_min = [i for i in range(0, int(duration_min)+1, int(dt_min))]
    o2_pct = []
    co2_pct = []

    base_o2 = 21.0  # 초기 산소 %
    base_co2 = 0.04  # 초기 CO2 %

    for t in times_min:
        # 사람 호흡에 의한 산소 소비, CO2 증가 (단순 비례)
        o2_drop = people * 0.01 * t / duration_min
        co2_rise = people * 0.005 * t / duration_min

        # 환기에 따른 희석 (ACH 고려, 단순 비례 감소)
        ventilation_factor = (1 - ach * t / (duration_min*60))
        ventilation_factor = max(ventilation_factor, 0.5)  # 최소 50% 유지

        # 식물 광합성 효과
        if light_on and plants > 0:
            o2_increase = plants * 0.005 * t / duration_min
            co2_decrease = plants * 0.003 * t / duration_min
        else:
            o2_increase = 0
            co2_decrease = 0

        current_o2 = (base_o2 - o2_drop + o2_increase) * ventilation_factor
        current_co2 = (base_co2 + co2_rise - co2_decrease) * ventilation_factor

        o2_pct.append(max(current_o2, 10))  # 10% 이상으로 제한
        co2_pct.append(max(current_co2, 0))

    return SimulationResult(times_min, o2_pct, co2_pct)


def get_inputs(prefix="", unique_id=""):
    st.header(f"{prefix} 환경 설정")
    
    # 고유 key를 만들기 위해 unique_id를 모든 key에 붙임
    key_prefix = f"{prefix}_{unique_id}_" if unique_id else f"{prefix}_"
    
    room_volume_m3 = st.number_input(f"{prefix}공간 부피 (m³)", value=30.0, min_value=1.0, step=1.0, key=key_prefix + "volume")
    people = st.number_input(f"{prefix}사람 수", value=2, min_value=0, step=1, key=key_prefix + "people")
    plants = st.number_input(f"{prefix}식물 수", value=0, min_value=0, step=1, key=key_prefix + "plants")
    ach = st.number_input(f"{prefix}환기율 (ACH, 회/h)", value=0.5, min_value=0.0, step=0.1, format="%.2f", key=key_prefix + "ach")
    duration_min = st.number_input(f"{prefix}시뮬레이션 시간 (분)", value=180, min_value=1, step=1, key=key_prefix + "duration")
    dt_min = st.slider(f"{prefix}시간 간격 (분)", min_value=0.1, max_value=5.0, value=1.0, step=0.1, key=key_prefix + "dt")
    light_on = st.checkbox(f"{prefix}식물 광합성(빛 있음)", value=True, key=key_prefix + "light")
    
    return dict(
        room_volume_m3=room_volume_m3,
        people=people,
        plants=plants,
        ach=ach,
        duration_min=duration_min,
        dt_min=dt_min,
        light_on=light_on,
    )


def plot_results(sim: SimulationResult, label_prefix=""):
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax2 = ax1.twinx()

    ax1.plot(sim.times_min, sim.o2_pct, label=label_prefix + 'O₂ (%)', color='blue', linewidth=2)
    ax2.plot(sim.times_min, sim.co2_pct, label=label_prefix + 'CO₂ (%)', color='orange', linewidth=2)

    ax1.set_xlabel("시간 (분)")
    ax1.set_ylabel("O₂ (%)")
    ax2.set_ylabel("CO₂ (%)")

    ax1.grid(True, linestyle='--', alpha=0.4)

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

    st.pyplot(fig)


def plot_3d(sim: SimulationResult):
    fig = go.Figure()
    fig.add_trace(go.Scatter3d(
        x=sim.times_min,
        y=sim.o2_pct,
        z=sim.co2_pct,
        mode='lines+markers',
        line=dict(color='blue'),
        name='O₂ vs CO₂ vs 시간'
    ))
    fig.update_layout(scene=dict(
        xaxis_title='시간 (분)',
        yaxis_title='O₂ (%)',
        zaxis_title='CO₂ (%)'
    ), height=600)
    st.plotly_chart(fig)


def plot_compare_results(sim1: SimulationResult, sim2: SimulationResult):
    fig, ax1 = plt.subplots(figsize=(8, 4))
    ax2 = ax1.twinx()

    ax1.plot(sim1.times_min, sim1.o2_pct, label='시나리오 1 O₂', color='blue', linestyle='-')
    ax1.plot(sim2.times_min, sim2.o2_pct, label='시나리오 2 O₂', color='blue', linestyle='--')
    ax2.plot(sim1.times_min, sim1.co2_pct, label='시나리오 1 CO₂', color='orange', linestyle='-')
    ax2.plot(sim2.times_min, sim2.co2_pct, label='시나리오 2 CO₂', color='orange', linestyle='--')

    ax1.set_xlabel("시간 (분)")
    ax1.set_ylabel("O₂ (%)")
    ax2.set_ylabel("CO₂ (%)")

    ax1.grid(True, linestyle='--', alpha=0.4)

    lines_1, labels_1 = ax1.get_legend_handles_labels()
    lines_2, labels_2 = ax2.get_legend_handles_labels()
    ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

    st.pyplot(fig)
