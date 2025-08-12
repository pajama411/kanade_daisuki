# models.py
from sklearn.ensemble import RandomForestRegressor
import numpy as np
import tensorflow as tf

def train_random_forest(X_train, y_train):
    rf = RandomForestRegressor(n_estimators=100)
    rf.fit(X_train, y_train)
    return rf

def predict_random_forest_with_uncertainty(model, X_test):
    preds = model.predict(X_test)
    # 단순하게 여러 트리 예측 분산 사용(간단 신뢰구간 예시)
    all_tree_preds = np.array([tree.predict(X_test) for tree in model.estimators_])
    std = np.std(all_tree_preds, axis=0)
    return preds, std

def build_lstm_model(input_shape):
    model = tf.keras.Sequential([
        tf.keras.layers.LSTM(64, return_sequences=True, input_shape=input_shape),
        tf.keras.layers.LSTM(32),
        tf.keras.layers.Dense(1)
    ])
    model.compile(optimizer='adam', loss='mse')
    return model

def train_lstm_model(model, X_train, y_train, epochs=10):
    model.fit(X_train, y_train, epochs=epochs)
    return model

def predict_lstm_with_uncertainty(model, X_test, n_samples=20):
    # MC Dropout 등으로 불확실성 계산 가능 (간단화)
    preds = model.predict(X_test)
    # 신뢰구간 계산 코드 추가 가능
    std = np.zeros_like(preds)  # placeholder
    return preds, std
