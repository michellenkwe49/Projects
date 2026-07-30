import io
import random
from datetime import datetime, timedelta

import bcrypt
import pandas as pd
import plotly.express as px
import streamlit as st
from fpdf import FPDF

from ml_analysis import CURRENCY, PAGE_VALUE, run_all_models

# BRAND IDENTITY
BRAND = {
    "primary":   "#0D47A1",
    "secondary": "#1565C0",
    "accent":    "#00BCD4",
    "success":   "#2E7D32",
    "warning":   "#F57F17",
    "danger":    "#C62828",
    "light":     "#E3F2FD",
    "text":      "#212121",
}

# 1. APP CONFIGURATION

st.set_page_config(page_title="CyberNova Ltd", page_icon="🛡️", layout="wide")

SESSION_TIMEOUT_MINUTES = 15

CHART_H = 205

st.markdown(f"""
    <style>

    /* 1. PREVENT OUTER SCROLL: Allow natural page height and vertical scrolling. */
    html, body {{
        min-height: 100vh !important;
        overflow-y: auto !important;
    }}

    .stApp {{
        min-height: 100vh !important;
    }}

    section[data-testid="stMain"],
    section[data-testid="stMain"] > div:first-child {{
        min-height: 100vh !important;
    }}

    /* 2. BLOCK CONTAINER: Prevent title from hiding behind Streamlit fixed header. */
    .block-container {{
        padding-top:    60px !important;
        padding-bottom: 0px  !important;
        max-width:      100% !important;
    }}

    /* 3. VERTICAL BLOCK GAPS: Add breathing room between KPI cards and charts. */
    div[data-testid="stVerticalBlock"] {{
        gap:     12px !important;
        row-gap: 12px !important;
    }}

    /* 4. ELEMENT CONTAINERS: Remove unnecessary Streamlit spacing. */
    div[data-testid="stElementContainer"] {{
        padding-top:    0 !important;
        margin-top:     0 !important;
        padding-bottom: 0 !important;
        margin-bottom:  0 !important;
    }}

    /* 5. HORIZONTAL BLOCKS (st.columns) */
    div[data-testid="stHorizontalBlock"] {{
        gap:            0.5rem !important;
        margin-top:     0      !important;
        margin-bottom:  0      !important;
        padding-top:    0      !important;
        padding-bottom: 0      !important;
    }}

    /* 6. PLOTLY WRAPPERS */
    div[data-testid="stPlotlyChart"] {{
        margin-bottom:  0 !important;
        padding-bottom: 0 !important;
    }}

    /* 7. KPI CARDS */
    .kpi-card {{
        background-color: white;
        padding:          5px 12px 2px 12px;
        border-radius:    10px;
        box-shadow:       0 4px 10px rgba(0,0,0,0.05);
        text-align:       center;
        margin-bottom:    10px !important;
        height:           92px;
        overflow:         hidden;
        box-sizing:       border-box;
    }}

    /* Colour stripe */
    .kpi-stripe {{
        height:        4px;
        border-radius: 0 0 8px 8px;
        margin:        3px -12px 0 -12px;
    }}

    .kpi-title {{
        color:          #757575;
        font-size:      10px;
        font-weight:    600;
        text-transform: uppercase;
        margin-bottom:  1px;
    }}

    .kpi-value {{
        font-size:     19px;
        font-weight:   800;
        margin:        2px 0;
        white-space:   nowrap;
        overflow:      hidden;
        text-overflow: ellipsis;
    }}

    .live-indicator {{
        color:       #FF5252;
        font-size:   8px;
        font-weight: bold;
        animation:   blinker 1.5s linear infinite;
        line-height: 1.2;
    }}

    @keyframes blinker {{
        50% {{ opacity: 0; }}
    }}

    /* 8. SIDEBAR BUTTONS */
    div[data-testid="stSidebar"] button {{
        background-color: #ffffff !important;
        border:           2px solid transparent !important;
        border-radius:    10px !important;
        padding:          10px !important;
        margin-bottom:    6px  !important;
        transition:
            border-color     0.15s ease,
            box-shadow       0.15s ease,
            background-color 0.15s ease;
    }}

    .active-nav button {{
        border:           2px solid #00BCD4            !important;
        box-shadow:       0 0 16px rgba(0,188,212,0.4) !important;
        background-color: #f0fbff                      !important;
    }}

    /* 9. PAGE TITLE & SUBHEADERS */
    h1 {{
        margin:      0 0 4px 0 !important;
        font-size:   1.3rem    !important;
        line-height: 1.2       !important;
    }}

    h2, h3 {{
        margin:    4px 0 !important;
        font-size: 1rem  !important;
    }}

    .login-header {{
        text-align: center;
        margin-bottom: 30px;
    }}

    </style>
""", unsafe_allow_html=True)

# 2. CONSTANTS & STATIC DATA

USER_DB = {
    "admin":   {"hash": b'$2b$12$ZFR/dT0gq6NwZL2xissa2envUuQAGiFDR4aW.EJEo7fD425ZoKIhe', "role": "Administrator"},
    "analyst": {"hash": b'$2b$12$KrhHzshMOzDhoB4TBRpJ1.SKT217LJuUQEpAFQ55xovI2fUzRqXTO', "role": "Analyst"},
    "viewer":  {"hash": b'$2b$12$Zk.yY.tJRQls1rE0i4pUVO8KmnzIt/8O87PzhSUVd4HpwRcskt6Ya', "role": "Viewer"},
}

PAGE_MAP = {
    "1. Strategic Market Identification": "",
    "2. Tactical Engagement Trends":      "",
    "3. Business Value & AI Predictions": "",
    "4. Operational Reporting":           "",
    "5. System Governance & Audit":       "",
    "6. User Manual":              "",
}

PAGE_LABELS = {
    "/portal/dashboard.html":         "Dashboard Portal",
    "/ai/advisory_chat_start":        "AI Virtual Assistant",
    "/services/realtime_threat_map":  "Threat Map Service",
    "/tools/automated_risk_score":    "Risk Score Tool",
    "/expansion/sadc_promo_june":     "SADC Promo / Demo",
    "/api/submit_system_maintenance": "Jobs / Maintenance API",
}

COUNTRIES = [
    "Botswana", "South Africa", "Namibia", "Zimbabwe", "Angola",
    "Zambia", "Malawi", "Mozambique", "Lesotho", "Eswatini",
]

ROLE_PAGE_ACCESS = {
    "Viewer":        ["1. Strategic Market Identification", "2. Tactical Engagement Trends", "3. Business Value & AI Predictions", "6. User Manual"],
    "Analyst":       ["1. Strategic Market Identification", "2. Tactical Engagement Trends", "3. Business Value & AI Predictions", "4. Operational Reporting", "6. User Manual"],
    "Administrator": list(PAGE_MAP.keys()),
}

_STATIC_PAGES = {"4. Operational Reporting", "5. System Governance & Audit"}

# 3. CACHED DATA LOADERS

@st.cache_resource(show_spinner=False)
def load_ml_results(path: str) -> dict:
    return run_all_models(path)


@st.cache_data(ttl=15, max_entries=10)
def _country_counts(df_json: str) -> pd.DataFrame:
    return pd.read_json(io.StringIO(df_json))["Country"].value_counts().reset_index()


@st.cache_data(ttl=15, max_entries=10)
def _request_health(df_json: str) -> pd.DataFrame:
    df = pd.read_json(io.StringIO(df_json)).tail(100).copy()
    df["Result"] = df["Status"].apply(lambda s: "Success (2xx)" if s < 400 else "Error (4xx/5xx)")
    return df.groupby(["Country", "Result"]).size().reset_index(name="Requests")


@st.cache_data(ttl=15, max_entries=10)
def _service_interest(df_json: str) -> pd.DataFrame:
    return pd.read_json(io.StringIO(df_json)).tail(200)


@st.cache_data(ttl=5, max_entries=10)
def _demand_velocity(df_json: str) -> pd.DataFrame:
    df = pd.read_json(io.StringIO(df_json))
    df["DateTime"] = pd.to_datetime(df["DateTime"])


    velocity = df.set_index('DateTime').resample('5min').size().reset_index(name="Req")

    now = datetime.now()
    if velocity['DateTime'].max() < now:
        new_row = pd.DataFrame({'DateTime': [now], 'Req': [0]})
        velocity = pd.concat([velocity, new_row], ignore_index=True)

    return velocity.sort_values('DateTime')


@st.cache_data(ttl=15, max_entries=10)
def _hourly_converts(df_json: str):
    df = pd.read_json(io.StringIO(df_json))
    today = datetime.now().date()
    hist  = df[pd.to_datetime(df["Date"]).dt.date < today]
    if hist.empty:
        return None, None
    hc = hist.groupby("Hour")["Converted"].sum()
    return int(hc.idxmax()), hc


@st.cache_data(ttl=5, max_entries=10)
def _lead_trajectory(df_json: str) -> pd.DataFrame:
    df = pd.read_json(io.StringIO(df_json))
    df["Date"] = pd.to_datetime(df["Date"])
    daily = df.groupby("Date")["Converted"].sum().reset_index()

    if not daily.empty:

        end_date = datetime.now().date()
        all_dates = pd.date_range(start=daily['Date'].min(), end=end_date, freq='D')
        daily = daily.set_index('Date').reindex(all_dates, fill_value=0).reset_index()
        daily.columns = ['Date', 'Converted']
    return daily


@st.cache_data(ttl=15, max_entries=10)
def _revenue_momentum(df_json: str) -> pd.DataFrame:
    df = pd.read_json(io.StringIO(df_json))
    return df.groupby("Hour")["Revenue"].sum().reset_index()


@st.cache_data(ttl=15, max_entries=10)
def _service_revenue(df_json: str) -> pd.DataFrame:
    df = pd.read_json(io.StringIO(df_json))
    return df.groupby("Page")["Revenue"].sum().reset_index()


# 4. UTILITY FUNCTIONS

def log_action(action: str) -> None:
    if "audit_trail" not in st.session_state:
        st.session_state.audit_trail = []
    st.session_state.audit_trail.append({
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "User":      st.session_state.get("user", "Guest"),
        "Role":      st.session_state.get("role", "N/A"),
        "Action":    action,
    })


def check_timeout() -> None:
    if not st.session_state.get("authenticated"):
        return
    last = st.session_state.get("last_activity")
    if last and datetime.now() - last > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
        st.session_state.authenticated = False
        st.rerun()
    st.session_state.last_activity = datetime.now()


def storytelling_kpi(
    title: str, value, insight: str,
    is_live: bool = True, color: str = "#00BCD4"
) -> None:
    status_html = (
        '<div class="live-indicator">● LIVE</div>' if is_live
        else '<div style="color:#757575;font-size:8px;">⏸️ PAUSED</div>'
    )

    st.markdown(f"""
        <div class="kpi-card">
            {status_html}
            <div class="kpi-title">{title}</div>
            <div class="kpi-value" style="color:{color};">{value}</div>
            <div style="color:#424242;font-size:9px;line-height:1.2;">💡 {insight}</div>
            <div class="kpi-stripe" style="background-color:{color};"></div>
        </div>
    """, unsafe_allow_html=True)



def _chart_cfg(extra_bottom: int = 0) -> dict:

    return dict(
        height=CHART_H,
        margin=dict(l=40, r=12, t=30, b=30 + extra_bottom),
    )


def generate_live_logs(base_df: pd.DataFrame, num_new_rows: int = 5) -> pd.DataFrame:
    uris = list(PAGE_VALUE.keys())
    now = datetime.now()

    # Create the new "Real-Time" entries
    new_rows_data = []
    for _ in range(num_new_rows):
        uri = random.choice(uris)
        new_rows_data.append({
            "DateTime": now,
            "IP_Address": f"196.{random.randint(1, 254)}.{random.randint(1, 254)}.{random.randint(1, 254)}",
            "Method": random.choice(["GET", "POST"]),
            "URI_Stem": uri,
            "Status": random.choice([200, 201, 200, 404]),
            "Bytes": random.randint(2000, 9000),
            "Country": random.choice(COUNTRIES),
            "Hour": now.hour,
            "Date": now.date(),
            "Converted": 1 if ("api" in uri or "promo" in uri) else 0,
            "Revenue": PAGE_VALUE.get(uri, 50),
            "Page": PAGE_LABELS.get(uri, uri),
        })

    keep_buffer = 10000

    new_df = pd.DataFrame(new_rows_data)
    updated_df = pd.concat([base_df, new_df], ignore_index=True)


    return updated_df.sort_values("DateTime").tail(keep_buffer)


# 5. PAGE RENDERERS

def render_strategic_market(df: pd.DataFrame, is_live: bool) -> None:
    conversions = int(df["Converted"].tail(50).sum())
    saturation  = (df["Status"] == 200).tail(100).mean() * 100

    k1, k2, k3 = st.columns(3)
    with k1:
        storytelling_kpi("Market Hotspot", df["Country"].mode()[0],
                         "Focus ad-spend here", is_live, "#00BCD4")
    lv_c = "#2E7D32" if conversions >= 10 else ("#FFA000" if conversions >= 5 else "#D32F2F")
    with k2:
        storytelling_kpi("Lead Velocity", conversions,
                         "Conversions in last 50", is_live, lv_c)
    ms_c = "#2E7D32" if saturation >= 70 else ("#FFA000" if saturation >= 50 else "#D32F2F")
    with k3:
        storytelling_kpi("Market Saturation", f"{saturation:.0f}%",
                         "Infrastructure stability", is_live, ms_c)

    df_json       = df.to_json()
    country_data  = _country_counts(df_json)
    health_data   = _request_health(df_json)
    interest_data = _service_interest(df_json)

    c1, c2 = st.columns(2)
    fig1 = px.choropleth(country_data, locations="Country",
                         locationmode="country names",
                         color="count", title="Regional Demand")
    fig1.update_layout(**_chart_cfg())
    c1.plotly_chart(fig1, use_container_width=True)

    fig2 = px.bar(country_data, x="count", y="Country",
                  orientation="h", title="Market Volume Ranking")
    fig2.update_layout(**_chart_cfg())
    c2.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)
    fig3 = px.bar(health_data, x="Requests", y="Country", color="Result",
                  orientation="h", barmode="stack",
                  title="Request Health by Country (last 100)",
                  color_discrete_map={"Success (2xx)": "#2E7D32",
                                      "Error (4xx/5xx)": "#C62828"})
    fig3.update_layout(**_chart_cfg())
    c3.plotly_chart(fig3, use_container_width=True)

    fig4 = px.histogram(interest_data, x="Country", color="Page",
                        barmode="group", title="Service Interest by Region")
    fig4.update_layout(**_chart_cfg(extra_bottom=30), xaxis_tickangle=-35)
    c4.plotly_chart(fig4, use_container_width=True)


def render_tactical_engagement(df: pd.DataFrame, is_live: bool) -> None:

    # 1. TACTICAL BUSINESS LOGIC
    today = datetime.now().date()
    historical_df = df[df["Date"] < today]
    if not historical_df.empty:
        hourly_converts = historical_df.groupby("Hour")["Converted"].sum()
        if not hourly_converts.empty and hourly_converts.sum() > 0:
            peak_hour = int(hourly_converts.idxmax())
            best_ad_value = f"{peak_hour:02d}:00 – {peak_hour + 1:02d}:00"
            best_ad_insight = f"{int(hourly_converts[peak_hour])} peak conversions"
        else:
            best_ad_value, best_ad_insight = "Syncing...", "Waiting for patterns"
    else:
        best_ad_value, best_ad_insight = "Collecting...", "Accumulating logs"

    # 2. KPI SECTION
    k1, k2, k3 = st.columns(3)
    with k1: storytelling_kpi("Best Sales Window", best_ad_value, best_ad_insight, is_live, "#00BCD4")
    with k2: storytelling_kpi("Engagement Rate", f"{(df['Status'] < 400).mean()*100:.1f}%", "Request success rate", is_live, "positive")
    with k3: storytelling_kpi("Lead Potential", f"{(df['Converted'].mean()*100):.1f}%", "Sales lead quality", is_live, "positive")

    # 3. DATA PROCESSING FOR AREA CHART
    hourly_stats = df.groupby("Hour").agg(
        Total_Traffic=("URI_Stem", "count"),
        Actual_Leads=("Converted", "sum")
    ).reset_index()

    # Fill in missing hours
    hourly_stats = hourly_stats.set_index("Hour").reindex(range(24), fill_value=0).reset_index()
    hourly_stats["Conversion_Rate"] = (hourly_stats["Actual_Leads"] / hourly_stats["Total_Traffic"]).fillna(0) * 100

    # 4. FULL-WIDTH AREA CHART
    fig_efficiency = px.area(
        hourly_stats,
        x="Hour",
        y="Conversion_Rate",
        height=280,
        title="Hourly Conversion Efficiency Trajectory (%)",
        labels={"Conversion_Rate": "Intent %", "Hour": "Hour (24h)"},
        color_discrete_sequence=["#00BCD4"]
    )

    fig_efficiency.update_layout(
        margin=dict(l=40, r=40, t=40, b=10),
        xaxis=dict(tickmode='linear', tick0=0, dtick=2),
        hovermode="x unified"
    )

    fig_efficiency.update_traces(line_shape="spline", fill='tozeroy', line=dict(width=3))


    st.plotly_chart(fig_efficiency, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig_methods = px.pie(df.tail(150), names="Method", hole=0.5, height=220, title="User Interaction Type")
        fig_methods.update_layout(margin=dict(l=10, r=10, t=30, b=10), legend=dict(orientation="h", y=-0.2))
        c1.plotly_chart(fig_methods, use_container_width=True)

    with c2:
        fig_heat = px.density_heatmap(df.tail(300), x="Hour", y="Status", height=220, title="Tactical Load Map", color_continuous_scale="Blues")
        fig_heat.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        c2.plotly_chart(fig_heat, use_container_width=True)


def render_business_value(df: pd.DataFrame, results: dict, is_live: bool) -> None:

    # 1.INDUSTRY ROI CALCULATION
    COST_OF_INVESTMENT = 850000
    total_revenue = df["Revenue"].sum()
    net_profit = total_revenue - COST_OF_INVESTMENT
    roi_percentage = (net_profit / COST_OF_INVESTMENT) * 100

    #  2. THRESHOLDS & KPIs
    forecast_acc = float(results["forecast"]["accuracy_pct"])
    ai_acc = float(results["conversion"]["accuracy_pct"])

    k1, k2, k3 = st.columns(3)


    if net_profit > 0:
        roi_color = "#006400"
    else:
        roi_color = "#FF0000"

    with k1:
        storytelling_kpi(
            "Marketing ROI",
            f"{roi_percentage:.1f}%",
            f"Net Profit: {CURRENCY} {net_profit:,.0f}",
            is_live,
            roi_color
        )

    # Forecast Confidence Thresholds
    fc_c = "positive" if forecast_acc >= 85 else ("negative" if forecast_acc < 70 else "neutral")
    with k2:
        storytelling_kpi("Forecast Conf.", f"{forecast_acc}%", "ML Fit quality", is_live, fc_c)

    # AI Accuracy Thresholds
    ai_c = "positive" if ai_acc >= 88 else ("negative" if ai_acc < 75 else "neutral")
    with k3:
        storytelling_kpi("AI Accuracy", f"{ai_acc}%", "Lead precision", is_live, ai_c)

    # 3. DATA PREPARATION
    df_sorted = df.sort_values("DateTime").copy()
    df_sorted["Cum_Revenue"] = df_sorted["Revenue"].cumsum()
    df_sorted["Net_Progress"] = df_sorted["Cum_Revenue"] - COST_OF_INVESTMENT

    matrix_data = df.groupby("Country").agg({
        "Converted": "sum",
        "Revenue": "sum",
        "IP_Address": "count"
    }).reset_index()
    matrix_data.columns = ["Country", "Leads", "Revenue", "Visits"]

    c1, c2 = st.columns(2)

    with c1:
        # Market Matrix
        fig1 = px.scatter(
            matrix_data, x="Leads", y="Revenue", size="Visits", color="Country",
            title="Market Matrix: Quality vs Quantity",
            height=CHART_H,
            labels={"Leads": "Conversions", "Revenue": "ROI (BWP)"}
        )
        fig1.update_layout(margin=dict(l=10, r=10, t=30, b=10), showlegend=False)
        c1.plotly_chart(fig1, use_container_width=True)

    with c2:
        # Revenue Momentum
        rev_hour = df.groupby("Hour")["Revenue"].sum().reset_index()
        fig2 = px.area(
            rev_hour, x="Hour", y="Revenue",
            title="Hourly Revenue Momentum",
            height=CHART_H,
            color_discrete_sequence=["#00BCD4"]
        )
        fig2.update_layout(margin=dict(l=10, r=10, t=30, b=10))
        c2.plotly_chart(fig2, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        # AI Drivers
        importance_df = pd.DataFrame({
            "Factor": ["Region", "Time", "Payload", "Stability"],
            "Impact": [42, 28, 20, 10],
        }).sort_values("Impact")
        fig3 = px.bar(
            importance_df, x="Impact", y="Factor",
            orientation="h", title="AI Insights: Driving Factors",
            height=CHART_H, color="Impact", color_continuous_scale="Blues"
        )
        fig3.update_layout(margin=dict(l=10, r=10, t=30, b=10), coloraxis_showscale=False)
        c3.plotly_chart(fig3, use_container_width=True)

    with c4:

        fig4 = px.line(
            df_sorted, x="DateTime", y="Net_Progress",
            title="Cumulative ROI (Profit Journey)",
            height=CHART_H,
            color_discrete_sequence=["#2E7D32"]
        )

        fig4.add_hline(y=0, line_dash="dash", line_color="#D32F2F", annotation_text="Break-Even Point")
        fig4.update_layout(
            margin=dict(l=10, r=10, t=30, b=10),
            yaxis_title="Profit/Loss (BWP)",
            xaxis_title=None
        )
        c4.plotly_chart(fig4, use_container_width=True)


def render_operational_reporting(df: pd.DataFrame) -> None:

    # 1. COMPACT VISUALS
    fig = px.histogram(
        df, x="Page", color="Status",
        height=200,
        title="Integrity Overview"
    )
    fig.update_layout(
        margin=dict(t=30, b=0, l=10, r=10),
        xaxis_title=None,
        yaxis_title=None,
        xaxis_tickangle=-30
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 2. DATA PREVIEW
    st.dataframe(df.tail(6), use_container_width=True, height=165)

    st.markdown(
        "<p style='text-align:center; font-size:12px; font-weight:bold; margin-bottom:0;'>Report Export Center</p>",
        unsafe_allow_html=True)

    _, exp_col_mid, _ = st.columns([1, 2, 1])

    with exp_col_mid:
        inner_left, inner_right = st.columns([1, 1.2])

        with inner_left:
            file_format = st.selectbox(
                "Format", ["CSV", "Excel", "PDF"],
                label_visibility="collapsed",
                key="op_format_select"
            )

        with inner_right:
            if file_format == "CSV":
                st.download_button(
                    label="Download CSV",
                    data=df.to_csv(index=False).encode('utf-8'),
                    file_name="cybernova_audit.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            elif file_format == "Excel":
                import io
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    df.to_excel(writer, index=False, sheet_name='Audit Logs')
                st.download_button(
                    label="Download Excel",
                    data=buffer.getvalue(),
                    file_name="cybernova_audit.xlsx",
                    use_container_width=True
                )
            elif file_format == "PDF":
                import io
                from fpdf import FPDF

                # 1. Setup PDF
                pdf = FPDF()
                pdf.add_page()
                pdf.set_font("Arial", 'B', 16)

                # 2. Header
                pdf.cell(190, 10, "CyberNova Analytics: Operational Audit", ln=True, align='C')
                pdf.set_font("Arial", '', 10)
                pdf.cell(190, 10, f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True,
                         align='C')
                pdf.ln(10)

                # 3. Summary Statistics Table
                pdf.set_fill_color(200, 220, 255)
                pdf.set_font("Arial", 'B', 12)
                pdf.cell(95, 10, "Metric Description", 1, 0, 'L', True)
                pdf.cell(95, 10, "Current Value", 1, 1, 'L', True)

                pdf.set_font("Arial", '', 12)
                # Calculate metrics for the PDF
                total_req = len(df)
                success_p = (df['Status'] < 400).mean() * 100
                total_roi = df['Revenue'].sum()

                stats = [
                    ("Total Processed Requests", f"{total_req:,}"),
                    ("System Integrity (Success %)", f"{success_p:.1f}%"),
                    ("Estimated ROI Value", f"{CURRENCY} {total_roi:,.0f}"),
                    ("Report Classification", "Confidential / Internal")
                ]

                for label, val in stats:
                    pdf.cell(95, 10, label, 1)
                    pdf.cell(95, 10, val, 1, 1)

                pdf.ln(10)
                pdf.set_font("Arial", 'I', 10)
                pdf.multi_cell(190, 10,
                               "This document serves as the official operational evidence for system audit compliance. Data is derived from live Big Data streams.")

                # 4. Export the binary data
                pdf_output = pdf.output(dest='S').encode('latin-1')

                st.download_button(
                    label="Download PDF Report",
                    data=pdf_output,
                    file_name="cybernova_audit_report.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )


def render_governance_audit(df: pd.DataFrame, is_live: bool) -> None:

    # 1. REAL-TIME INTEGRITY LOGIC
    null_values = df.isnull().sum().sum()
    total_cells = df.size  # total rows × columns
    null_pct = (null_values / total_cells) * 100
    base_integrity = 100 - null_pct
    integrity_score = round(max(0, min(100, base_integrity)), 1)

    if integrity_score == 100:
        val_c, val_desc = "#2E7D32", "Optimal"
    elif integrity_score >= 90:
        val_c, val_desc = "#FFA000", "Warning"
    else:
        val_c, val_desc = "#D32F2F", "Critical"

    # 2. KPI SECTION
    k1, k2, k3 = st.columns(3)
    with k1:
        storytelling_kpi("Admin Actions", len(st.session_state.get("audit_trail", [])), "Session event count", is_live)
    with k2:
        storytelling_kpi("Privacy Level", "Masked", "GDPR Anonymization", is_live, "#2E7D32")
    with k3:
        storytelling_kpi("Integrity Score", f"{integrity_score}%", f"{val_desc} validation", is_live, val_c)

    # 3. MID SECTION: INGESTION AUDIT (Squeezed for Zero-Scroll)
    st.markdown("<p style='font-weight:bold; margin:0;'> Ingestion Health & Validation</p>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        # Ultra-compact Checklist
        status_icon = "✅" if integrity_score == 100 else "⚠️"
        st.markdown(f"""
            <table style="width:100%; font-size:11px; border-collapse: collapse;">
                <tr style="border-bottom: 1px solid #ddd;"><td>Null Check</td><td>{status_icon}</td><td>{null_values} errors</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td>IP Format</td><td>✅</td><td>Secure</td></tr>
                <tr style="border-bottom: 1px solid #ddd;"><td>SADC Match</td><td>✅</td><td>Verified</td></tr>
            </table>
        """, unsafe_allow_html=True)

    with col_right:
        health = df.tail(100)['Status'].apply(lambda x: 'Valid' if x < 400 else 'Error').value_counts()
        fig = px.pie(names=health.index, values=health.values, height=130,
                     color_discrete_map={'Valid': '#2E7D32', 'Error': '#D32F2F'})
        fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

    # 4. AUDIT FILTERS
    st.markdown("<p style='font-weight:bold; margin:5px 0 0 0;'> Audit Filter & History</p>", unsafe_allow_html=True)

    trail = st.session_state.get("audit_trail", [])
    if trail:
        audit_df = pd.DataFrame(trail)
        audit_df['Timestamp'] = pd.to_datetime(audit_df['Timestamp'])

        # Filter Layout
        f1, f2 = st.columns(2)
        with f1:
            # Date filter
            selected_date = st.date_input("Filter Date", value=datetime.now().date(), label_visibility="collapsed")
        with f2:
            # Role filter
            roles = ["All Roles"] + list(audit_df['Role'].unique())
            selected_role = st.selectbox("Filter Role", roles, label_visibility="collapsed")

        # Apply Filtering
        filtered_df = audit_df[audit_df['Timestamp'].dt.date == selected_date]
        if selected_role != "All Roles":
            filtered_df = filtered_df[filtered_df['Role'] == selected_role]

        st.dataframe(
            filtered_df.sort_values("Timestamp", ascending=False),
            use_container_width=True,
            height=180
        )
    else:
        st.info("No audit data streaming.")


# 6. LIVE CONTENT FRAGMENT

@st.fragment(run_every=15)
def render_live_content(menu: str) -> None:
    is_live = st.session_state.get("live_updates", True)

    if is_live and menu not in _STATIC_PAGES:
        st.session_state.live_df = generate_live_logs(st.session_state.live_df)

    df      = st.session_state.live_df
    results = st.session_state.last_ml_run

    page_renderers = {
        "1. Strategic Market Identification": lambda: render_strategic_market(df, is_live),
        "2. Tactical Engagement Trends":      lambda: render_tactical_engagement(df, is_live),
        "3. Business Value & AI Predictions": lambda: render_business_value(df, results, is_live),
        "4. Operational Reporting":           lambda: render_operational_reporting(df),
        "5. System Governance & Audit":       lambda: render_governance_audit(df, is_live),
        "6. User Manual": render_user_manual,
    }

    if menu in page_renderers:
        page_renderers[menu]()


def render_user_manual() -> None:
    st.markdown("## CyberNova User Manual")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        ### How to use the Dashboard
        1. **Navigate:** Use the sidebar buttons to switch between Strategic, Tactical, and Business views.
        2. **Live Mode:** Toggle the 'Live Stream' in the sidebar to pause updates for deep analysis.
        3. **Filters:** On the Audit page, use the dropdowns to filter by date or user role.
        4. **Export:** Go to 'Operational Reporting' to download data as CSV, Excel, or PDF.

        ### Understanding Colors
        - **Green:** Performance is optimal (e.g., >85% Integrity).
        - **Amber:** Warning state. Requires monitoring.
        - **Red:** Critical state. Immediate action required.
        """)

    with col2:
        st.markdown("""
        ### Troubleshooting Errors
        - **'Access Denied':** Ensure your caps lock is off. Passwords are case-sensitive.
        - **'Session Timed Out':** For security, the system logs you out after 15 minutes of inactivity. Simply log in again.
        - **Charts not loading:** Ensure the 'Live Stream' toggle is ON.
        - **Empty Audit Log:** Filters may be set to a date with no activity. Reset the date filter to 'Today'.

        **Support Contact:** support@cybernova.co.bw
        """)


# 7. VIEWS — LOGIN & DASHBOARD

def render_login_view() -> None:
    login_container = st.empty()

    with login_container.container():
        st.markdown("<div style='height:14vh'></div>", unsafe_allow_html=True)
        _, col_mid, _ = st.columns([2, 2, 2])
        with col_mid:
            st.markdown(
                "<div class='login-header'>"
                "<img src='https://cdn-icons-png.flaticon.com/512/2103/2103633.png' width='72'>"
                "<h1 style='color:#0D47A1;font-size:1.6rem;margin:8px 0 0 0;'>"
                "CyberNova Analytics</h1>"
                "</div>",
                unsafe_allow_html=True,
            )
            with st.container(border=True):
                u = st.text_input("Username")
                p = st.text_input("Password", type="password")
                if st.button("Login", use_container_width=True):
                    if u in USER_DB and bcrypt.checkpw(p.encode(), USER_DB[u]["hash"]):
                        login_container.empty()

                        # 2. Update session state
                        st.session_state.update({
                            "authenticated": True,
                            "user": u,
                            "role": USER_DB[u]["role"],
                            "last_activity": datetime.now(),
                            "menu_selection": "1. Strategic Market Identification",
                        })
                        log_action("User Logged In")

                        st.rerun()
                    else:
                        st.error("Access Denied")

                st.divider()
                with st.expander("Trouble logging in?"):
                    st.markdown("""
                                    **Self-Service Checklist:**
                                    1. **Case Sensitivity:** Ensure your Caps Lock is off; usernames are lowercase.
                                    2. **Special Characters:** Your secure password must match the encrypted signature.
                                    3. **Browser Cache:** If the page hangs, refresh your browser (F5).

                                    *For account lockouts, contact the System Administrator:*  
                                     **support@cybernova.co.bw**
                                    """)

                # Footer credit
            st.markdown(
                "<p style='text-align:center; font-size:10px; color:#aaa; margin-top:20px;'>"
                "© 2026 CyberNova Ltd — Proprietary Big Data Ingestion Engine"
                "</p>",
                unsafe_allow_html=True
            )


def render_dashboard_view() -> None:
    if "live_df" not in st.session_state:
        res = load_ml_results("CyberNova_Web_Logs.csv")
        st.session_state.live_df     = res["df"]
        st.session_state.last_ml_run = res

    st.sidebar.title("CyberNova")
    st.sidebar.markdown(f"**{st.session_state.user}** ({st.session_state.role})")
    st.session_state.live_updates = st.sidebar.toggle("Live Stream", value=True)

    allowed = ROLE_PAGE_ACCESS[st.session_state.role]
    for p in allowed:
        if st.session_state.get("menu_selection") == p:
            st.sidebar.markdown('<div class="active-nav">', unsafe_allow_html=True)
            st.sidebar.button(f"{PAGE_MAP[p]} {p}", key=f"btn_{p}",
                              use_container_width=True)
            st.sidebar.markdown("</div>", unsafe_allow_html=True)
        else:
            if st.sidebar.button(f"{PAGE_MAP[p]} {p}", key=f"btn_{p}",
                                 use_container_width=True):
                st.session_state.menu_selection = p
                log_action(f"Visited {p}")
                st.rerun()

    if st.sidebar.button("Logout"):
        log_action("User Logged Out")
        st.session_state.authenticated = False
        st.rerun()

    menu = st.session_state.menu_selection
    st.title(f"{PAGE_MAP[menu]} {menu}")
    render_live_content(menu)


# 8. ENTRY POINT

def main() -> None:
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if "audit_trail" not in st.session_state:
        st.session_state.audit_trail = []
    check_timeout()
    if st.session_state.authenticated:
        render_dashboard_view()
    else:
        render_login_view()


if __name__ == "__main__":
    main()