import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

from simulator import (
    run_simulation,
    SimulationResult,
    get_inputs,
    plot_results,
    plot_3d,
    plot_compare_results,
)
from prediction import run_prediction_ai, plot_prediction

from auth_and_scenario import login, save_scenario, load_scenarios, load_scenario, signup

#자동 분석
def show_danger_warnings(sim):
    max_co2 = max(sim.co2_pct)
    min_o2 = min(sim.o2_pct)

    st.markdown("### ⚠️ 자동 분석 결과")

    # CO2 기준 예시 (0.1% 이상 위험)
    if max_co2 > 0.1:
        st.warning(f"CO₂ 농도가 최대 {max_co2:.4f}%로 위험 수준을 초과했습니다.")
    else:
        st.success(f"CO₂ 농도가 최대 {max_co2:.4f}%로 안전한 수준입니다.")

    # O2 기준 예시 (19.5% 이하 저산소 위험)
    if min_o2 < 19.5:
        st.warning(f"산소 농도가 최소 {min_o2:.2f}%로 저산소 위험이 있습니다.")
    else:
        st.success(f"산소 농도가 최소 {min_o2:.2f}%로 정상 범위입니다.")

    # 추가로 경향 분석 (예: 증가/감소 여부)
    co2_trend = np.polyfit(sim.times_min, sim.co2_pct, 1)[0]  # 1차 회귀선 기울기
    if co2_trend > 0:
        st.info("CO₂ 농도가 점차 증가하는 추세입니다.")
    else:
        st.info("CO₂ 농도가 안정적이거나 감소하는 추세입니다.")

#임시 테스트용

def analyze_trend_with_plot(df_all):
    return "트렌드 분석 결과는 여기에 표시됩니다."  # 테스트용 반환값

def analyze_ai_prediction(df_all):
    return "AI 예측 인사이트는 여기에 표시됩니다."  # 테스트용 반환값


# ===============================
# 메인 페이지 설정
# ===============================
st.set_page_config(
    page_title="산소/이산화탄소 시뮬레이터 & AI 예측",
    page_icon="🧪",
    layout="wide",
)

#메인화면+로그인

def main():
    st.title("🧪 산소/이산화탄소 농도 시뮬레이터 & AI 예측")
    st.markdown("<span style='color:gray;'>실내 환경 조건에 따른 산소/이산화탄소 변화 시뮬레이션과 AI 기반 예측을 제공합니다.</span>", unsafe_allow_html=True)
    st.markdown("---")

    if 'auth_choice' not in st.session_state:
        st.session_state['auth_choice'] = "로그인"

    if 'user' not in st.session_state:
        st.session_state['user'] = None

    choice = st.sidebar.selectbox("접속 유형", ["로그인", "회원가입"], index=0 if st.session_state['auth_choice'] == "로그인" else 1)
    st.session_state['auth_choice'] = choice

    if choice == "로그인":
        if st.session_state['user'] is None:
            user = login()
            if user:
                st.session_state['user'] = user
        else:
            user = st.session_state['user']

    elif choice == "회원가입":
        signup_user = signup()
        if signup_user:
            st.success("회원가입 성공! 로그인 화면으로 이동합니다.")
            st.session_state['auth_choice'] = "로그인"
            st.session_state['user'] = signup_user
        user = st.session_state['user']

    if not st.session_state['user']:
        st.warning("로그인 또는 회원가입 후 이용해주세요.")
        st.stop()

    user = st.session_state['user']

    # --- 시나리오 관리 ---
    st.sidebar.header("시나리오 관리")
    scenarios = load_scenarios(user)
    selected_scenario = st.sidebar.selectbox(
        "저장된 시나리오 불러오기",
        ["새 시나리오"] + list(scenarios),
        key="scenario_selectbox"
    )

    if selected_scenario != "새 시나리오":
        inputs = load_scenario(user, selected_scenario)
    else:
        inputs = get_inputs(unique_id="new_scenario")

    # --- 탭 1회 생성 ---
    tab_sim, tab_ai, tab_interpretation = st.tabs(["🖥 시뮬레이터", "🤖 AI 예측", "📖 결과 해석 가이드"])

    with tab_sim:
        sim_mode = st.radio("시뮬레이터 모드 선택", ("단일 시뮬레이션", "시나리오 비교"), horizontal=True)

        if sim_mode == "단일 시뮬레이션":
            output_choice = st.radio("결과 표시 방식 선택", ["📋 표", "📈 2D 그래프", "🌐 3D 그래프"], horizontal=True)

            col_run, col_save = st.columns([3, 1])

            with col_run:
                if st.button("🚀 시뮬레이션 실행", key="run_single_sim", use_container_width=True):
                    with st.spinner("시뮬레이션 계산 중..."):
                        sim = run_simulation(**inputs)
                        st.session_state['last_sim'] = sim

            if 'last_sim' in st.session_state:
                sim = st.session_state['last_sim']

                if output_choice == "📋 표":
                    st.subheader("📋 시뮬레이션 결과 (표)")
                    df = pd.DataFrame({
                        "시간 (분)": sim.times_min,
                        "O₂ (%)": sim.o2_pct,
                        "CO₂ (%)": sim.co2_pct
                    })
                    st.dataframe(df.style.format({"O₂ (%)": "{:.3f}", "CO₂ (%)": "{:.5f}"}))

                    with col_save:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="💾 CSV 다운로드",
                            data=csv,
                            file_name="simulation_result.csv",
                            mime="text/csv",
                            use_container_width=True,
                            key="download_csv"
                        )

                elif output_choice == "📈 2D 그래프":
                    st.subheader("📈 시뮬레이션 결과 (2D 그래프)")
                    plot_results(sim)

                elif output_choice == "🌐 3D 그래프":
                    st.subheader("🌐 시뮬레이션 결과 (3D 그래프)")
                    plot_3d(sim)

                st.markdown("### 📊 자동 분석")
                # 여기에 자동 분석 결과 출력 함수 호출
                show_danger_warnings(sim)

            with col_save:
                scenario_name = st.text_input("시나리오 이름 저장", key="scenario_name_input")
                if st.button("💾 시나리오 저장", key="save_scenario_button", use_container_width=True):
                    if scenario_name.strip():
                        save_scenario(user, scenario_name.strip(), inputs)
                        st.success(f"시나리오 '{scenario_name.strip()}' 저장 완료!")
                    else:
                        st.error("시나리오 이름을 입력하세요.")

        else:  # 시나리오 비교 모드
            st.write("두 시나리오 조건을 입력하세요.")
            inputs1 = get_inputs("시나리오 1 ", unique_id="s1")
            inputs2 = get_inputs("시나리오 2 ", unique_id="s2")

            if st.button("⚡ 두 시나리오 실행", key="run_compare_sim", use_container_width=True):
                with st.spinner("비교 시뮬레이션 실행 중..."):
                    sim1 = run_simulation(**inputs1)
                    sim2 = run_simulation(**inputs2)
                    st.session_state['last_sim1'] = sim1
                    st.session_state['last_sim2'] = sim2

            if 'last_sim1' in st.session_state and 'last_sim2' in st.session_state:
                sim1 = st.session_state['last_sim1']
                sim2 = st.session_state['last_sim2']

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("시나리오 1 결과")
                plot_results(sim1, label_prefix="시나리오 1 ")
                show_danger_warnings(sim1)
            with col2:
                st.subheader("시나리오 2 결과")
                plot_results(sim2, label_prefix="시나리오 2 ")
                show_danger_warnings(sim2)

            st.subheader("📊 시나리오 비교 그래프")
            plot_compare_results(sim1, sim2)


    with tab_ai:
        # AI 예측 탭 코드 작성
        pass

    with tab_interpretation:
        # 결과 해석 가이드 탭 코드 작성
        pass


    # ===============================
    # AI 예측 탭
    # ===============================
    with tab_ai:
        st.header("🤖 AI 예측 모드")
        st.info("AI 기반 모델이 시뮬레이션 이후의 농도 변화를 예측합니다.")

        st.markdown("""
        **📝 개념**  
        - **시뮬레이션 시간**: 초기 데이터 생성 기간  
        - **예측 시간**: AI가 미래를 예측하는 기간  
        - **환경 설정**: 조건을 변경하여 예측 결과를 비교
        """)

        col_left, col_right = st.columns(2)
        with col_left:
            sim_hours = st.number_input("⏱ 시뮬레이션 시간 (분)", min_value=10, max_value=180, value=60, step=10)
            predict_hours = st.number_input("🔮 예측 시간 (분)", min_value=5, max_value=60, value=20, step=5)
            dt_min = st.slider("📏 시간 간격 (분)", min_value=0.1, max_value=5.0, value=1.0, step=0.1)
        with col_right:
            room_volume_m3 = st.number_input("🏠 공간 부피 (m³)", value=30.0, min_value=1.0, step=1.0)
            people = st.number_input("👥 사람 수", value=2, min_value=0, step=1)
            plants = st.number_input("🌱 식물 수", value=0, min_value=0, step=1)
            ach = st.number_input("💨 환기율 (ACH, 회/h)", value=0.5, min_value=0.0, step=0.1, format="%.2f")
            light_on = st.checkbox("💡 식물 광합성(빛 있음)", value=True)

        # 예측 버튼은 여기 안에서만 사용 — 전역 버튼 제거해서 미정의 변수 문제 해결
        if st.button("🚀 예측 실행", use_container_width=True):
            with st.spinner("AI 예측 중..."):
                # run_prediction 함수가 해당 인자를 받는 것으로 가정
                df_all = run_prediction_ai(
                    sim_hours=sim_hours,
                    predict_hours=predict_hours,
                    room_volume_m3=room_volume_m3,
                    people=people,
                    plants=plants,
                    ach=ach,
                    dt_min=dt_min,
                    light_on=light_on,
                )
                st.success("✅ 예측 완료!")

                # 탭으로 결과 보기 (그래프 / 데이터 / 트렌드)
                result_tabs = st.tabs(["📊 그래프", "📋 데이터", "📈 트렌드 분석"])
                with result_tabs[0]:
                    plot_prediction(df_all)
                with result_tabs[1]:
                    st.dataframe(df_all)
                with result_tabs[2]:
                    trend_report = analyze_trend_with_plot(df_all)
                    if trend_report:
                        st.markdown(trend_report)

                st.markdown("### 🔍 AI 인사이트")
                st.info(analyze_ai_prediction(df_all))
                
    # ===============================
    # 결과 해석 가이드 탭
    # ===============================
    with tab_interpretation:
        st.header("📖 AI 예측 & 시뮬레이션 결과 해석 가이드")
        st.markdown(
            """
            이 탭에서는 시뮬레이션 및 AI 예측 결과를 보다 쉽게 이해할 수 있도록 설명을 제공합니다.

            ### 1. 산소(O₂) 농도 변화
            - 일반적으로 실내 산소 농도는 약 21%입니다.
            - 사람이 호흡하면 산소가 감소하고, 식물이 있으면 광합성으로 산소가 증가할 수 있습니다.
            - 시뮬레이션과 AI 예측 결과에서 산소 농도의 변화 추이를 살펴보세요.

            ### 2. 이산화탄소(CO₂) 농도 변화
            - 일반적인 대기 중 CO₂ 농도는 약 0.04%입니다.
            - 사람이 호흡하면서 CO₂가 증가하고, 식물이 CO₂를 흡수하면 감소할 수 있습니다.
            - 환기율(ACH)이 높으면 CO₂ 농도가 감소하는 효과가 나타납니다.

            ### 3. 불확실성(Uncertainty)
            - AI 모델이 예측한 값에 대한 신뢰도 또는 변동 가능성을 나타냅니다.
            - 불확실성이 높으면 해당 예측값이 다소 변동될 수 있음을 의미합니다.
            - 예측 결과와 함께 불확실성 값을 참고하세요.

            ### 4. 그래프 해석 팁
            - 시뮬레이션 데이터(실선)는 현재 조건에서 예상되는 실제 농도 변화입니다.
            - AI 예측 데이터(점선)는 미래 조건을 예측한 결과입니다.
            - 두 데이터를 비교하며 결과를 이해해 보세요.

            ---
            필요한 추가 질문이 있으면 언제든 문의해주세요!
            """
        )



def analyze_ai_prediction(df):
    """AI 예측 데이터에서 간단한 분석 코멘트 생성"""

    # 허용되는 컬럼명 대응: 'oxygen'/'co2' 또는 'O2 (%)'/'CO2 (%)'
    if "oxygen" in df.columns:
        o_col = "oxygen"
        c_col = "co2"
    elif "O2 (%)" in df.columns:
        o_col = "O2 (%)"
        c_col = "CO2 (%)"
    else:
        st.warning("데이터에 예상된 산소/이산화탄소 컬럼이 없습니다.")
        return "데이터 컬럼 문제로 분석 불가."

    avg_o2 = df[o_col].mean()
    avg_co2 = df[c_col].mean()
    final_o2 = df[o_col].iloc[-1]
    final_co2 = df[c_col].iloc[-1]

    comment = f"""
    - 평균 산소 농도: {avg_o2:.2f}%  
    - 평균 이산화탄소 농도: {avg_co2:.3f}%  
    - 예측 종료 시점 산소: {final_o2:.2f}%, 이산화탄소: {final_co2:.3f}%
    """

    if final_o2 < 19.5:
        comment += "\n⚠️ **경고**: 예측 종료 시점 산소 농도가 안전 기준 이하입니다."
    if final_co2 > 0.1:
        comment += "\n⚠️ **경고**: 예측 종료 시점 CO₂ 농도가 위험 기준 이상입니다."

    return comment


def show_danger_warnings(sim: SimulationResult):
    """산소/이산화탄소 위험 수준 경고 표시"""
    danger_o2_threshold = 19.5
    danger_co2_threshold = 0.1
    danger_o2_time = None
    danger_co2_time = None
    for i, (o2_val, co2_val) in enumerate(zip(sim.o2_pct, sim.co2_pct)):
        if danger_o2_time is None and o2_val < danger_o2_threshold:
            danger_o2_time = sim.times_min[i]
        if danger_co2_time is None and co2_val > danger_co2_threshold:
            danger_co2_time = sim.times_min[i]
    if danger_o2_time is not None:
        st.error(f"⚠️ 산소 농도가 {danger_o2_threshold}% 이하로 떨어진 시점: {danger_o2_time:.1f}분")
    if danger_co2_time is not None:
        st.error(f"⚠️ CO₂ 농도가 {danger_co2_threshold}% 이상으로 상승한 시점: {danger_co2_time:.1f}분")


def analyze_trend_with_plot(df: pd.DataFrame):
    """
    O₂ 및 CO₂의 변화 속도 분석 + 시각화
    입력 df 포맷 허용:
      - prediction.run_prediction 반환 (columns: time, oxygen, co2, type)
      - 또는 컬럼명이 'time_min','O2 (%)','CO2 (%)'인 경우도 처리
    반환: 텍스트 리포트 (string)
    """
    # --- 컬럼 호환성 맞추기 ---
    df = df.copy()
    if "time" in df.columns:
        df["time_min"] = df["time"]
    if "oxygen" in df.columns:
        df["O2 (%)"] = df["oxygen"]
    if "co2" in df.columns:
        df["CO2 (%)"] = df["co2"]

    if "time_min" not in df.columns:
        st.error("❌ 데이터에 'time_min' 컬럼이 없습니다. (요청: prediction.run_prediction의 반환 확인)")
        return None

    fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    fig.subplots_adjust(hspace=0.4)
    report_lines = []

    times = df["time_min"].values
    # 시간 간격 안정화
    if len(times) < 2:
        st.warning("데이터 길이가 짧아 트렌드 분석을 수행할 수 없습니다.")
        return None
    dt = np.mean(np.diff(times))

    for idx, gas in enumerate(["O2 (%)", "CO2 (%)"]):
        if gas not in df.columns:
            st.warning(f"⚠ '{gas}' 데이터 없음 — 분석 건너뜀")
            continue

        values = df[gas].values
        rate = np.gradient(values, dt)  # 변화율 (%/분)
        accel = np.gradient(rate, dt)   # 가속도 (%/분^2)

        # 텍스트 분석 지표
        avg_rate = np.mean(rate)
        avg_accel = np.mean(accel)

        if avg_rate > 0.0005:
            trend = "전반적으로 증가 추세"
        elif avg_rate < -0.0005:
            trend = "전반적으로 감소 추세"
        else:
            trend = "안정 추세"

        if avg_accel > 0.0002:
            accel_trend = "변화 속도가 점점 빨라짐"
        elif avg_accel < -0.0002:
            accel_trend = "변화 속도가 점점 느려짐"
        else:
            accel_trend = "변화 속도 일정"

        report_lines.append(f"""
**{gas} 트렌드 분석**
- 평균 변화율: {avg_rate:.4f} %/분
- 평균 가속도: {avg_accel:.5f} %/분²
- 전반적 경향: {trend}
- 변화 속도 분석: {accel_trend}
""")

        # 그래프: 농도 + 변화율
        axes[idx].plot(times, values, label=f"{gas} 농도", color="tab:blue" if "O2" in gas else "tab:green")
        axes[idx].set_ylabel(f"{gas}")
        ax2 = axes[idx].twinx()
        ax2.plot(times, rate, label="변화율", color="tab:red", linestyle="--", alpha=0.8)
        ax2.set_ylabel("변화율 (%/분)", color="tab:red")
        axes[idx].grid(True, alpha=0.3)

    axes[-1].set_xlabel("시간 (분)")
    st.pyplot(fig)

    return "\n".join(report_lines)


if __name__ == "__main__":
    main()
