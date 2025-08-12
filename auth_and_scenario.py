import streamlit as st
import json
import os

USER_DB = "users.json"

def load_users():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    else:
        return {}

def save_users(users):
    with open(USER_DB, "w") as f:
        json.dump(users, f, indent=2)

def signup():
    st.subheader("회원가입")
    new_user = st.text_input("아이디를 입력하세요", key="signup_user")
    new_pw = st.text_input("비밀번호를 입력하세요", type="password", key="signup_pw")
    new_pw2 = st.text_input("비밀번호를 다시 입력하세요", type="password", key="signup_pw2")

    if st.button("회원가입 완료"):
        if not new_user or not new_pw:
            st.error("아이디와 비밀번호를 모두 입력하세요.")
            return None
        if new_pw != new_pw2:
            st.error("비밀번호가 일치하지 않습니다.")
            return None

        users = load_users()
        if new_user in users:
            st.error("이미 존재하는 아이디입니다.")
            return None

        users[new_user] = {"password": new_pw}
        save_users(users)
        st.success("회원가입이 완료되었습니다! 로그인 탭에서 로그인하세요.")
        return new_user
    return None

def login():
    st.subheader("로그인")
    user = st.text_input("아이디", key="login_user")
    pw = st.text_input("비밀번호", type="password", key="login_pw")

    if st.button("로그인"):
        users = load_users()
        if user in users and users[user]["password"] == pw:
            st.success(f"{user}님 환영합니다!")
            return user
        else:
            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
            return None
    return None

# --- 시나리오 저장 및 불러오기 함수 ---
SCENARIO_DIR = "user_scenarios"

def save_scenario(user, scenario_name, inputs, favorite=False):
    user_dir = os.path.join(SCENARIO_DIR, user)
    os.makedirs(user_dir, exist_ok=True)
    filepath = os.path.join(user_dir, f"{scenario_name}.json")

    data = {
        "inputs": inputs,
        "favorite": favorite
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def load_scenarios(user):
    """사용자 시나리오 목록과 즐겨찾기 목록 반환"""
    user_dir = os.path.join(SCENARIO_DIR, user)
    if not os.path.exists(user_dir):
        return [], []

    scenario_files = [f for f in os.listdir(user_dir) if f.endswith(".json")]
    all_scenarios = []
    favorite_scenarios = []
    for f in scenario_files:
        filepath = os.path.join(user_dir, f)
        with open(filepath, "r", encoding="utf-8") as file:
            data = json.load(file)
            name = f[:-5]  # .json 제거
            all_scenarios.append(name)
            if data.get("favorite", False):
                favorite_scenarios.append(name)
    return all_scenarios, favorite_scenarios

def load_scenario(user, scenario_name):
    user_dir = os.path.join(SCENARIO_DIR, user)
    filepath = os.path.join(user_dir, f"{scenario_name}.json")
    if not os.path.exists(filepath):
        return None
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("inputs", None)

# --- 시뮬레이터 입력 받는 함수 예시 ---
def get_inputs():
    room_volume_m3 = st.number_input("방 부피 (m³)", min_value=1.0, value=30.0)
    people = st.number_input("사람 수", min_value=0, value=2)
    plants = st.number_input("식물 수", min_value=0, value=0)
    ach = st.number_input("환기율 (회/h)", min_value=0.0, value=0.5)
    dt_min = st.number_input("시간 간격 (분)", min_value=0.1, value=1.0)
    light_on = st.checkbox("광합성 활성화", value=True)
    sim_hours = st.number_input("시뮬레이션 시간 (분)", min_value=1, value=60)
    predict_hours = st.number_input("예측 시간 (분)", min_value=1, value=20)

    return {
        "room_volume_m3": room_volume_m3,
        "people": people,
        "plants": plants,
        "ach": ach,
        "dt_min": dt_min,
        "light_on": light_on,
        "sim_hours": sim_hours,
        "predict_hours": predict_hours,
    }