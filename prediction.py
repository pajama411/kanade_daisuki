import numpy as np
import pandas as pd
from models import (
    train_random_forest,
    predict_random_forest_with_uncertainty,
    build_lstm_model,
    train_lstm_model,
    predict_lstm_with_uncertainty,
)

import matplotlib.pyplot as plt

def plot_prediction(df_all):
    plt.figure(figsize=(10,5))
    for col in ['oxygen', 'co2']:
        sim_data = df_all[df_all['type'] == 'simulated']
        pred_data = df_all[df_all['type'] == 'predicted']

        plt.plot(sim_data['time'], sim_data[col], label=f"{col.upper()} (Simulated)")
        plt.plot(pred_data['time'], pred_data[col], '--', label=f"{col.upper()} (Predicted)")

    plt.xlabel("Time (min)")
    plt.ylabel("Concentration (%)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()


def run_prediction_ai(
    sim_hours,
    predict_hours,
    room_volume_m3,
    people,
    plants,
    ach,
    dt_min,
    light_on,
    model_type="rf",
):
    """
    AI 예측 함수 (랜덤포레스트, LSTM 선택 가능)
    
    (실제 데이터 전처리 및 feature 생성 코드는 구현 필요)
    """

    # === 데이터 준비 (더미 데이터 예시) ===
    n_train = 100
    n_test = int(predict_hours / dt_min)
    n_features = 5

    X_train = np.random.rand(n_train, n_features)
    y_train = np.random.rand(n_train, 2)  # 산소, 이산화탄소 농도
    X_test = np.random.rand(n_test, n_features)

    # LSTM 입력 형태 (예시)
    input_shape = (X_train.shape[1],)

    # === 모델 학습 및 예측 ===
    if model_type == "rf":
        model = train_random_forest(X_train, y_train)
        preds, uncertainty = predict_random_forest_with_uncertainty(model, X_test)
    elif model_type == "lstm":
        model = build_lstm_model(input_shape)
        model = train_lstm_model(model, X_train, y_train)
        preds, uncertainty = predict_lstm_with_uncertainty(model, X_test)
    else:
        raise ValueError(f"알 수 없는 model_type: {model_type}")

    preds = np.array(preds)           # shape (N, 2)
    uncertainty = np.array(uncertainty)  # 예상 shape (M,) or (M,1) or (N,2)

    print(f"Before adjustment: preds.shape={preds.shape}, uncertainty.shape={uncertainty.shape}")

    # 1) 만약 uncertainty가 (N, 2)라면 각 변수별 평균 또는 최대값 등으로 1차원으로 변환
    if uncertainty.ndim == 2 and uncertainty.shape[1] == 2:
        uncertainty = uncertainty.mean(axis=1)
        print(f"Uncertainty reduced to 1D: {uncertainty.shape}")

    # 2) uncertainty가 (M, 1)이라면 1차원으로 평탄화
    elif uncertainty.ndim == 2 and uncertainty.shape[1] == 1:
        uncertainty = uncertainty.ravel()
        print(f"Uncertainty flattened: {uncertainty.shape}")

    # 3) 길이 맞추기 (자르거나 채우기)
    if len(uncertainty) > len(preds):
        uncertainty = uncertainty[:len(preds)]
        print(f"Uncertainty truncated to match preds: {uncertainty.shape}")
    elif len(uncertainty) < len(preds):
        fill_len = len(preds) - len(uncertainty)
        uncertainty = np.concatenate([uncertainty, np.full(fill_len, uncertainty[-1])])
        print(f"Uncertainty padded to match preds: {uncertainty.shape}")

    if len(preds) != len(uncertainty):
        raise ValueError(f"예측값 개수({len(preds)})와 불확실성 개수({len(uncertainty)})가 다릅니다.")

    # === 시뮬레이션 더미 데이터 생성 ===
    time_sim = np.arange(0, sim_hours + dt_min, dt_min)
    oxygen_sim = np.random.rand(len(time_sim)) * 20 + 1  # 예시값, 실제 시뮬레이션으로 대체 가능
    co2_sim = np.random.rand(len(time_sim)) * 0.05       # 예시값
    uncertainty_sim = np.zeros(len(time_sim))            # 시뮬레이션 데이터는 불확실성 0 또는 NaN 가능

    df_sim = pd.DataFrame({
        "time": time_sim,
        "oxygen": oxygen_sim,
        "co2": co2_sim,
        "uncertainty": uncertainty_sim,
        "type": "simulated"
    })

    # === 예측 데이터 시간 생성 ===
    time_pred_start = time_sim[-1] + dt_min
    time_pred = np.arange(time_pred_start, time_pred_start + len(preds)*dt_min, dt_min)

    df_pred = pd.DataFrame({
        "time": time_pred,
        "oxygen": preds[:, 0],
        "co2": preds[:, 1],
        "uncertainty": uncertainty,
        "type": "predicted"
    })

    # === 시뮬레이션 + 예측 합치기 ===
    df_all = pd.concat([df_sim, df_pred], ignore_index=True)

    return df_all


