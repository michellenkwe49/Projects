import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# 1. CONSTANTS

OUTPUT_PATH  = "CyberNova_Web_Logs.csv"
DEFAULT_ROWS = 5_000
START_DATE   = datetime(2026, 1, 1)

# Realistic IP prefixes per SADC country
SADC_IP_RANGES: dict[str, list[str]] = {
    "Botswana":    ["168.167.", "196.216."],
    "South Africa":["102.129.", "197.242."],
    "Namibia":     ["196.44.",  "197.188."],
    "Zimbabwe":    ["41.220.",  "154.250."],
    "Angola":      ["41.223.",  "197.94." ],
    "Zambia":      ["41.222.",  "197.215."],
    "Malawi":      ["41.190.",  "105.234."],
    "Mozambique":  ["41.221.",  "197.218."],
    "Lesotho":     ["196.202.", "41.203." ],
    "Eswatini":    ["168.253.", "105.232."],
}

# Shows real SADC internet penetration
COUNTRIES       = list(SADC_IP_RANGES.keys())
MARKET_WEIGHTS  = [40, 30, 5, 5, 5, 5, 2, 4, 2, 2]

# High-value endpoints targeted by business/API users
HIGH_VALUE_URIS = [
    "/api/submit_system_maintenance",
    "/expansion/sadc_promo_june",
]

# Standard browsing endpoints with realistic visit weights
BROWSE_URIS = [
    "/portal/dashboard.html",
    "/ai/advisory_chat_start",
    "/services/realtime_threat_map",
    "/tools/automated_risk_score",
]
BROWSE_WEIGHTS = [0.4, 0.3, 0.2, 0.1]

# Status codes for browsing traffic
BROWSE_STATUSES = [200, 200, 200, 404, 500]

# CSV column order
COLUMNS = ["DateTime", "IP_Address", "Method", "URI_Stem", "Status", "Bytes", "Country"]


# 2. HELPERS

def generate_ip(country: str) -> str:
    """Return a plausible IP address for the given SADC country."""
    prefix = random.choice(SADC_IP_RANGES[country])
    return f"{prefix}{random.randint(1, 254)}.{random.randint(1, 254)}"


def is_business_user(country: str, hour: int) -> bool:

    return country in {"South Africa", "Botswana"} and 9 <= hour <= 17


def generate_row(country: str) -> list:
    now = datetime.now()

    days_back = int(np.random.power(1) * 120)

    timestamp = now - timedelta(days=days_back, hours=random.randint(0, 23), minutes=random.randint(0, 59))

    hour = timestamp.hour
    ip = generate_ip(country)

    if is_business_user(country, hour) and random.random() < 0.7:
        uri, status = random.choice(HIGH_VALUE_URIS), 201
    else:
        uri = random.choices(BROWSE_URIS, weights=BROWSE_WEIGHTS)[0]
        status = random.choice(BROWSE_STATUSES)

    return [timestamp.strftime("%Y-%m-%d %H:%M:%S"), ip, "GET", uri, status, random.randint(2000, 10000), country]


# 3. LOG GENERATION

def create_cybernova_custom_logs(rows: int = 5000) -> None:
    data = [generate_row(random.choices(COUNTRIES, weights=MARKET_WEIGHTS)[0]) for _ in range(rows)]
    df = pd.DataFrame(data, columns=COLUMNS)

    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df = df.sort_values('DateTime')

    df.to_csv(OUTPUT_PATH, index=False)
    print(f"Success: Created chronological log file.")


# 4. ENTRY POINT

if __name__ == "__main__":
    create_cybernova_custom_logs()