import json
import os

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import IsolationForest, RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import accuracy_score, r2_score, silhouette_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, StandardScaler


# 1. CONSTANTS

CURRENCY = "BWP"

# Estimated revenue contribution per page visit (BWP)
PAGE_VALUE: dict[str, int] = {
    "/portal/dashboard.html":         68,
    "/services/realtime_threat_map":  135,
    "/tools/automated_risk_score":    270,
    "/ai/advisory_chat_start":        473,
    "/expansion/sadc_promo_june":     675,
    "/api/submit_system_maintenance": 1_080,
}

# Human-readable labels for each URI stem
PAGE_LABELS: dict[str, str] = {
    "/portal/dashboard.html":         "Dashboard Portal",
    "/ai/advisory_chat_start":        "AI Virtual Assistant",
    "/services/realtime_threat_map":  "Threat Map Service",
    "/tools/automated_risk_score":    "Risk Score Tool",
    "/expansion/sadc_promo_june":     "SADC Promo / Demo",
    "/api/submit_system_maintenance": "Jobs / Maintenance API",
}


# 2. DATA LOADING & PREPARATION

def load_and_prepare(path: str = "CyberNova_Web_Logs.csv") -> pd.DataFrame:
    """
    Load the raw web-server log CSV and engineer the columns required by both the ML models and the Streamlit dashboard.

    Returns an empty DataFrame if the file does not exist.
    """
    if not os.path.exists(path):
        return pd.DataFrame()

    df = pd.read_csv(path)
    df["DateTime"] = pd.to_datetime(df["DateTime"])

    # Time features
    df["Hour"] = df["DateTime"].dt.hour
    df["Date"] = df["DateTime"].dt.date

    # Business features
    df["Converted"] = df["URI_Stem"].str.contains("api|promo|expansion").astype(int)
    df["Revenue"]   = df["URI_Stem"].map(PAGE_VALUE).fillna(50)
    df["Page"]      = df["URI_Stem"].map(PAGE_LABELS).fillna(df["URI_Stem"])

    return df


# 3. MACHINE LEARNING MODELS

def _run_traffic_forecast(df: pd.DataFrame) -> dict:
    """
    Model 1 — Traffic Forecasting.
    Trains a RandomForest regressor on a single lag feature (previous day's request count) to predict daily traffic volume.
    """
    daily        = df.groupby("Date").size().reset_index(name="Requests")
    daily["Lag1"] = daily["Requests"].shift(1)
    daily.dropna(inplace=True)

    X, y = daily[["Lag1"]], daily["Requests"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, shuffle=False,
    )

    model  = RandomForestRegressor(n_estimators=50, random_state=42).fit(X_train, y_train)
    preds  = model.predict(X_test)
    errors = np.abs((y_test - preds) / y_test)
    acc    = max(0.0, (1 - np.mean(errors)) * 100)

    return {
        "name":         "Traffic Forecasting",
        "accuracy_pct": round(acc, 1),
        "description":  (
            f"Predicting daily volume using historical lags. "
            f"Model reliability: {round(acc, 1)}%"
        ),
    }


def _run_anomaly_detection(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Model 2 — Security Anomaly Detection.
    Fits an IsolationForest on bytes transferred and HTTP status code to flag suspicious requests. Adds an 'Anomaly' column to the DataFrame in-place.
    """
    iso            = IsolationForest(contamination=0.05, random_state=42)
    df["Anomaly"]  = iso.fit_predict(df[["Bytes", "Status"]])
    normal_rate    = (df["Anomaly"] == 1).mean() * 100
    anomaly_rate   = round(100 - normal_rate, 1)

    result = {
        "name":         "Security Anomaly",
        "accuracy_pct": round(normal_rate, 1),
        "description":  (
            f"Isolation Forest identified {anomaly_rate}% of traffic as anomalous."
        ),
    }
    return df, result


def _run_market_clustering(df: pd.DataFrame) -> dict:
    """
    Model 3 — Market Segmentation.
    Groups SADC countries into three tiers using KMeans on mean bytes transferred and total conversions per country.
    """
    country_data = (
        df.groupby("Country")
        .agg({"Bytes": "mean", "Converted": "sum"})
        .reset_index()
    )

    scaler      = StandardScaler()
    scaled_data = scaler.fit_transform(country_data[["Bytes", "Converted"]])

    km  = KMeans(n_clusters=3, random_state=42, n_init=10).fit(scaled_data)
    sil = silhouette_score(scaled_data, km.labels_)

    return {
        "name":         "Market Segmentation",
        "accuracy_pct": round(sil * 100, 1),
        "description":  (
            "K-Means grouped SADC countries into 3 tiers "
            "based on revenue and activity."
        ),
    }


def _run_conversion_prediction(df: pd.DataFrame) -> dict:
    """
    Model 4 — Conversion Prediction.
    Trains a balanced RandomForest classifier to predict which sessions are likely to convert, using country, hour, and session payload as features.
    """
    le             = LabelEncoder()
    df["Country_Enc"] = le.fit_transform(df["Country"])

    X = df[["Country_Enc", "Hour", "Bytes"]]
    y = df["Converted"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, stratify=y,
    )

    clf = RandomForestClassifier(
        n_estimators=100, class_weight="balanced", random_state=42,
    ).fit(X_train, y_train)
    acc = accuracy_score(y_test, clf.predict(X_test))

    return {
        "name":         "Conversion Prediction",
        "accuracy_pct": round(acc * 100, 1),
        "description":  (
            f"Predicts likely customers with {round(acc * 100, 1)}% accuracy."
        ),
    }


# 4. PUBLIC API

def run_all_models(path: str = "CyberNova_Web_Logs.csv") -> dict:
    """
    Run the full ML pipeline and return a results dictionary containing:

    Returns an empty dict if the data file cannot be found.
    """
    df = load_and_prepare(path)
    if df.empty:
        return {}

    df, anomaly_result = _run_anomaly_detection(df)

    return {
        "df":         df,
        "forecast":   _run_traffic_forecast(df),
        "anomaly":    anomaly_result,
        "clustering": _run_market_clustering(df),
        "conversion": _run_conversion_prediction(df),
    }


# 5. STANDALONE ENTRY POINT

if __name__ == "__main__":
    print(" Starting Machine Learning Analysis ")

    results = run_all_models()

    printable = {k: v for k, v in results.items() if k != "df"}
    print(json.dumps(printable, indent=4))

    print("\n Analysis Complete ")