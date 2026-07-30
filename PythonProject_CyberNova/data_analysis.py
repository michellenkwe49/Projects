import os

os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["OMP_NUM_THREADS"]      = "1"

import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec
from matplotlib.patches import FancyBboxPatch


# 1. CONSTANTS & BRAND IDENTITY

BRAND: dict[str, str] = {
    "primary":   "#0D47A1",
    "secondary": "#1565C0",
    "accent":    "#00BCD4",
    "success":   "#2E7D32",
    "warning":   "#F57F17",
    "danger":    "#C62828",
    "light":     "#E3F2FD",
    "text":      "#212121",
    "muted":     "#757575",
    "bg":        "#F8FAFC",
}

CURRENCY = "BWP"

COUNTRY_PALETTE: list[str] = [
    "#1565C0", "#00ACC1", "#2E7D32", "#F57F17",
    "#7B1FA2", "#C62828", "#37474F", "#00695C",
    "#4527A0", "#558B2F",
]

PAGE_LABELS: dict[str, str] = {
    "/portal/dashboard.html":         "Dashboard Portal",
    "/ai/advisory_chat_start":        "AI Virtual Assistant",
    "/services/realtime_threat_map":  "Threat Map Service",
    "/tools/automated_risk_score":    "Risk Score Tool",
    "/expansion/sadc_promo_june":     "SADC Promo / Demo",
    "/api/submit_system_maintenance": "Jobs / Maintenance API",
}

# Estimated revenue contribution per page visit
PAGE_VALUE: dict[str, int] = {
    "/portal/dashboard.html":         5,
    "/ai/advisory_chat_start":        25,
    "/services/realtime_threat_map":  15,
    "/tools/automated_risk_score":    20,
    "/expansion/sadc_promo_june":     30,
    "/api/submit_system_maintenance": 50,
}

CHARTS_DIR = "charts"
os.makedirs(CHARTS_DIR, exist_ok=True)


# 2. SHARED HELPERS

def save(fig: plt.Figure, name: str) -> None:
    """Save a figure to the charts directory and close it."""
    path = os.path.join(CHARTS_DIR, name)
    fig.savefig(path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"  ✓ Saved  {path}")


def branded_fig(figsize: tuple = (10, 6), title: str = "") -> tuple[plt.Figure, plt.Axes]:
    """
    Create a pre-styled figure and axes using the CyberNova brand palette.
    Removes top/right spines and applies brand colours to ticks and labels.
    """
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BRAND["bg"])
    ax.set_facecolor(BRAND["light"])
    ax.spines[["top", "right"]].set_visible(False)
    ax.tick_params(colors=BRAND["text"])
    ax.xaxis.label.set_color(BRAND["text"])
    ax.yaxis.label.set_color(BRAND["text"])
    if title:
        ax.set_title(
            title, fontsize=13, fontweight="bold",
            color=BRAND["primary"], pad=12,
        )
    return fig, ax


def branded_pie_fig(figsize: tuple = (9, 7)) -> tuple[plt.Figure, plt.Axes]:
    """Create a pre-styled figure for pie charts (no axes spine logic needed)."""
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor(BRAND["bg"])
    return fig, ax


def add_value_labels(
    ax: plt.Axes,
    bars,
    fmt: str = "{:.0f}",
    color: str = "white",
    fontsize: int = 9,
) -> None:
    """Overlay centred value labels on a set of bar patches."""
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            h * 0.5,
            fmt.format(h),
            ha="center", va="center",
            color=color, fontsize=fontsize, fontweight="bold",
        )


def style_autotexts(autotexts, fontsize: int = 9) -> None:
    """Apply consistent white bold styling to pie-chart percentage labels."""
    for at in autotexts:
        at.set_fontsize(fontsize)
        at.set_fontweight("bold")
        at.set_color("white")


# 3. DATA LOADING & CLEANING

def load_and_clean(path: str = "CyberNova_Web_Logs.csv") -> pd.DataFrame:
    """
    Load the raw web-server log CSV, parse timestamps, drop invalid/duplicate
    rows, and derive useful time and business columns.

    Returns a clean DataFrame ready for analysis and charting.
    """
    print("\n Loading & Cleaning")
    df = pd.read_csv(path)

    # Parse and validate timestamps
    df["DateTime"] = pd.to_datetime(df["DateTime"], errors="coerce")
    before = len(df)
    df.dropna(subset=["DateTime"], inplace=True)
    df.drop_duplicates(inplace=True)
    after = len(df)
    print(f"  Rows loaded : {before:,}")
    print(f"  Rows cleaned: {after:,}  ({before - after} removed)")

    # Derived time columns
    df["Date"]      = df["DateTime"].dt.date
    df["Hour"]      = df["DateTime"].dt.hour
    df["DayOfWeek"] = df["DateTime"].dt.day_name()
    df["Week"]      = df["DateTime"].dt.isocalendar().week.astype(int)
    df["Month"]     = df["DateTime"].dt.month_name()

    # Business-context columns
    df["Page"]    = df["URI_Stem"].map(PAGE_LABELS).fillna(df["URI_Stem"])
    df["Revenue"] = df["URI_Stem"].map(PAGE_VALUE).fillna(5)
    df["Success"] = df["Status"].isin([200, 201])

    return df


# 4. SUMMARY STATISTICS

def print_statistics(df: pd.DataFrame) -> None:
    """Print a structured summary of traffic, bytes, revenue, and ROI metrics."""
    print("\n Summary Statistics")

    total      = len(df)
    success    = df["Success"].sum()
    error_rate = (1 - success / total) * 100

    print(f"\n  Total requests       : {total:,}")
    print(f"  Successful (2xx)     : {success:,}  ({success / total * 100:.1f}%)")
    print(f"  Error rate           : {error_rate:.1f}%")

    print(f"\n  Bytes transferred")
    print(f"    Mean               : {df['Bytes'].mean():,.0f} bytes")
    print(f"    Std Dev            : {df['Bytes'].std():,.0f} bytes")
    print(f"    Min / Max          : {df['Bytes'].min():,} / {df['Bytes'].max():,}")

    print(f"\n  Estimated engagement value")
    print(f"    Total              : ${df['Revenue'].sum():,.0f}")
    print(f"    Mean per visit     : ${df['Revenue'].mean():.2f}")
    print(f"    Std Dev            : ${df['Revenue'].std():.2f}")

    jobs    = (df["URI_Stem"] == "/api/submit_system_maintenance").sum()
    ai_req  = (df["URI_Stem"] == "/ai/advisory_chat_start").sum()
    demos   = (df["URI_Stem"] == "/expansion/sadc_promo_june").sum()
    threats = (df["URI_Stem"] == "/services/realtime_threat_map").sum()

    print(f"\n  Key interactions")
    print(f"    Jobs placed              : {jobs:,}")
    print(f"    AI assistant sessions    : {ai_req:,}")
    print(f"    Demo/promo requests      : {demos:,}")
    print(f"    Threat map views         : {threats:,}")

    print(f"\n  Top countries by traffic")
    for country, cnt in df["Country"].value_counts().head(5).items():
        print(f"    {country:<20} {cnt:>5,} ({cnt / total * 100:.1f}%)")

    peak_hour = df["Hour"].value_counts().idxmax()
    print(f"\n  Peak traffic hour   : {peak_hour:02d}:00")

    ad_cost_estimate = 3_000   # assumed monthly ad spend (BWP)
    monthly_revenue  = df["Revenue"].sum()
    roi = (monthly_revenue - ad_cost_estimate) / ad_cost_estimate * 100
    print(f"\n  ROI estimate (proxy)")
    print(f"    Assumed ad spend   : ${ad_cost_estimate:,}")
    print(f"    Engagement value   : ${monthly_revenue:,.0f}")
    print(f"    ROI                : {roi:.1f}%")


# 5. CHARTS

def chart_roi_summary(df: pd.DataFrame) -> None:
    """00 — KPI summary card: eight headline metrics in a 4×2 tile grid."""
    ad_spend    = 3_000
    total_value = df["Revenue"].sum()
    roi         = (total_value - ad_spend) / ad_spend * 100
    ai_sessions = (df["URI_Stem"] == "/ai/advisory_chat_start").sum()
    demo_req    = (df["URI_Stem"] == "/expansion/sadc_promo_june").sum()
    jobs_placed = (df["URI_Stem"] == "/api/submit_system_maintenance").sum()
    error_rate  = (1 - df["Success"].mean()) * 100

    metrics = [
        ("Total Visits",    f"{len(df):,}",         BRAND["primary"]),
        ("Estimated Value", f"${total_value:,.0f}",  BRAND["success"]),
        ("Ad Spend (est.)", f"${ad_spend:,}",        BRAND["warning"]),
        ("ROI",             f"{roi:.1f}%",            BRAND["accent"]),
        ("AI Sessions",     f"{ai_sessions:,}",      BRAND["secondary"]),
        ("Demo Requests",   f"{demo_req:,}",          BRAND["primary"]),
        ("Jobs Placed",     f"{jobs_placed:,}",      BRAND["success"]),
        ("Error Rate",      f"{error_rate:.1f}%",    BRAND["danger"]),
    ]

    fig = plt.figure(figsize=(14, 5))
    fig.patch.set_facecolor(BRAND["bg"])
    fig.suptitle(
        "CyberNova Analytics — Sales Performance KPI Dashboard",
        fontsize=14, fontweight="bold", color=BRAND["primary"], y=1.01,
    )

    for idx, (label, value, color) in enumerate(metrics):
        ax = fig.add_subplot(2, 4, idx + 1)
        ax.set_facecolor(color)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis("off")
        ax.text(0.5, 0.62, value, ha="center", va="center",
                fontsize=18, fontweight="bold", color="white",
                transform=ax.transAxes)
        ax.text(0.5, 0.25, label, ha="center", va="center",
                fontsize=9, color="white", alpha=0.9,
                transform=ax.transAxes)

    fig.tight_layout()
    save(fig, "00_kpi_summary.png")


def chart_country_traffic(df: pd.DataFrame) -> None:
    """01 — Horizontal bar: web traffic volume by SADC country."""
    counts  = df["Country"].value_counts()
    fig, ax = branded_fig((10, 6), "Web Traffic by Country (SADC Region)")

    bars = ax.barh(
        counts.index[::-1], counts.values[::-1],
        color=COUNTRY_PALETTE[:len(counts)],
        edgecolor="white", linewidth=0.5, height=0.65,
    )
    for bar in bars:
        w = bar.get_width()
        ax.text(
            w + 20, bar.get_y() + bar.get_height() / 2,
            f"{w:,}", va="center", fontsize=9,
            color=BRAND["text"], fontweight="bold",
        )

    ax.set_xlabel("Number of Requests", color=BRAND["text"])
    fig.tight_layout()
    save(fig, "01_traffic_by_country.png")


def chart_page_requests(df: pd.DataFrame) -> None:
    """02 — Bar chart: total requests per service/page."""
    counts  = df["Page"].value_counts()
    fig, ax = branded_fig((10, 6), "Requests per Service / Page")

    bars = ax.bar(
        counts.index, counts.values,
        color=COUNTRY_PALETTE[:len(counts)],
        edgecolor="white", linewidth=0.5, width=0.6,
    )
    add_value_labels(ax, bars, color=BRAND["bg"])
    ax.set_xlabel("Service / Page")
    ax.set_ylabel("Number of Requests")
    ax.set_xticklabels(counts.index, rotation=30, ha="right", fontsize=9)
    fig.tight_layout()
    save(fig, "02_page_requests.png")


def chart_key_interactions(df: pd.DataFrame) -> None:
    """03 — Grouped bar: volume of key business interaction types."""
    interaction_map = {
        "Jobs Placed\n(Maintenance API)": "/api/submit_system_maintenance",
        "AI Virtual\nAssistant":          "/ai/advisory_chat_start",
        "Demo / Promo\nRequests":         "/expansion/sadc_promo_june",
        "Threat Map\nViews":              "/services/realtime_threat_map",
        "Risk Score\nTool":               "/tools/automated_risk_score",
    }
    labels = list(interaction_map.keys())
    counts = [df[df["URI_Stem"] == uri].shape[0] for uri in interaction_map.values()]
    colors = [
        BRAND["primary"], BRAND["accent"], BRAND["warning"],
        BRAND["danger"],  BRAND["success"],
    ]

    fig, ax = branded_fig((10, 6), "Key Business Interactions")
    bars = ax.bar(
        labels, counts, color=colors,
        edgecolor="white", linewidth=0.5, width=0.55,
    )
    add_value_labels(ax, bars, color="white")
    ax.set_ylabel("Number of Requests")
    ax.set_xlabel("Interaction Type")
    fig.tight_layout()
    save(fig, "03_key_interactions.png")


def chart_status_pie(df: pd.DataFrame) -> None:
    """04 — Pie chart: HTTP status code distribution with error slice explode."""
    status_map = {
        200: "200 OK",
        201: "201 Created",
        400: "400 Bad Request",
        401: "401 Unauthorised",
        403: "403 Forbidden",
        404: "404 Not Found",
        500: "500 Server Error",
    }
    counts  = df["Status"].value_counts()
    labels  = [status_map.get(s, str(s)) for s in counts.index]
    explode = [0.05 if s >= 400 else 0 for s in counts.index]
    colors  = [
        BRAND["success"] if s < 300 else
        BRAND["warning"] if s < 500 else
        BRAND["danger"]
        for s in counts.index
    ]

    fig, ax = branded_pie_fig((9, 7))
    _, _, autotexts = ax.pie(
        counts.values, labels=labels, autopct="%1.1f%%",
        colors=colors, explode=explode,
        startangle=140, pctdistance=0.75,
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
    )
    style_autotexts(autotexts)
    ax.set_title(
        "HTTP Status Code Distribution",
        fontsize=13, fontweight="bold", color=BRAND["primary"], pad=12,
    )
    save(fig, "04_status_code_pie.png")


def chart_method_pie(df: pd.DataFrame) -> None:
    """05 — Pie chart: HTTP method distribution (GET, POST, etc.)."""
    counts = df["Method"].value_counts()
    colors = [BRAND["primary"], BRAND["accent"], BRAND["warning"], BRAND["danger"]]

    fig, ax = branded_pie_fig((7, 6))
    _, _, autotexts = ax.pie(
        counts.values, labels=counts.index, autopct="%1.1f%%",
        colors=colors[:len(counts)], startangle=90,
        wedgeprops={"linewidth": 1.5, "edgecolor": "white"},
        pctdistance=0.78,
    )
    style_autotexts(autotexts, fontsize=10)
    ax.set_title(
        "HTTP Method Distribution",
        fontsize=13, fontweight="bold", color=BRAND["primary"], pad=12,
    )
    save(fig, "05_method_pie.png")


def chart_hourly_traffic(df: pd.DataFrame) -> None:
    """06 — Area/line chart: hourly traffic with labelled peak windows."""
    hourly  = df.groupby("Hour").size().reindex(range(24), fill_value=0)
    fig, ax = branded_fig((12, 5), "Hourly Traffic Pattern (Peak Hours Analysis)")

    ax.fill_between(hourly.index, hourly.values, color=BRAND["primary"], alpha=0.15)
    ax.plot(
        hourly.index, hourly.values,
        color=BRAND["primary"], linewidth=2.5,
        marker="o", markersize=5, markerfacecolor=BRAND["accent"],
    )

    peak_windows = [
        (8,  11, "Morning Peak"),
        (12, 15, "Lunch Peak"),
        (18, 23, "Evening Peak"),
    ]
    for i, (start, end, label) in enumerate(peak_windows):
        ax.axvspan(start, end, alpha=0.08, color=BRAND["warning"],
                   label=label if i == 0 else "")
        ax.text(
            (start + end) / 2, hourly.max() * 0.92, label,
            ha="center", fontsize=8, color=BRAND["warning"], style="italic",
        )

    ax.set_xticks(range(24))
    ax.set_xticklabels(
        [f"{h:02d}:00" for h in range(24)],
        rotation=45, ha="right", fontsize=8,
    )
    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Number of Requests")
    fig.tight_layout()
    save(fig, "06_hourly_traffic.png")


def chart_daily_trend(df: pd.DataFrame) -> None:
    """07 — Bar + line: daily request volume with a 7-day rolling average."""
    daily         = df.groupby("Date").size().reset_index(name="Requests")
    daily["Date"] = pd.to_datetime(daily["Date"])
    rolling       = daily["Requests"].rolling(7, center=True).mean()

    fig, ax = branded_fig((13, 5), "Daily Traffic Trend with 7-Day Rolling Average")
    ax.bar(daily["Date"], daily["Requests"],
           color=BRAND["primary"], alpha=0.35, width=0.8, label="Daily")
    ax.plot(daily["Date"], rolling,
            color=BRAND["accent"], linewidth=2.5, label="7-Day Average")
    ax.set_xlabel("Date")
    ax.set_ylabel("Requests")
    ax.legend(fontsize=10)
    fig.autofmt_xdate()
    fig.tight_layout()
    save(fig, "07_daily_trend.png")


def chart_dow_heatmap(df: pd.DataFrame) -> None:
    """08 — Heatmap: request volume by day-of-week × service."""
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday",
                 "Friday", "Saturday", "Sunday"]
    pivot = (
        df.groupby(["DayOfWeek", "Page"])
        .size()
        .unstack(fill_value=0)
        .reindex(day_order)
    )

    fig, ax = branded_pie_fig((12, 5))   # no spines needed for heatmap
    im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels(pivot.columns, rotation=30, ha="right", fontsize=8)
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index, fontsize=9)
    plt.colorbar(im, ax=ax, label="Requests")

    threshold = pivot.values.max() * 0.5
    for i in range(len(pivot.index)):
        for j in range(len(pivot.columns)):
            cell_color = "white" if pivot.values[i, j] > threshold else BRAND["text"]
            ax.text(j, i, str(pivot.values[i, j]),
                    ha="center", va="center", fontsize=7, color=cell_color)

    ax.set_title(
        "Day-of-Week × Service Heatmap",
        fontsize=13, fontweight="bold", color=BRAND["primary"], pad=12,
    )
    fig.tight_layout()
    save(fig, "08_dow_heatmap.png")


def chart_bytes_scatter(df: pd.DataFrame) -> None:
    """09 — Scatter plot: bytes transferred vs hour of day, coloured by country."""
    sample = df.sample(min(800, len(df)), random_state=42).copy()
    sample["HourJitter"] = sample["Hour"] + np.random.uniform(-0.3, 0.3, len(sample))

    countries = sample["Country"].unique()
    palette   = {c: COUNTRY_PALETTE[i % len(COUNTRY_PALETTE)] for i, c in enumerate(countries)}

    fig, ax = branded_fig((12, 6), "Bytes Transferred vs Hour of Day (by Country)")
    for country in countries:
        sub = sample[sample["Country"] == country]
        ax.scatter(
            sub["HourJitter"], sub["Bytes"],
            c=palette[country], label=country,
            alpha=0.55, s=22, edgecolors="white", linewidths=0.3,
        )

    # Overall trend line
    z = np.polyfit(sample["Hour"], sample["Bytes"], 1)
    xr = np.linspace(0, 23, 100)
    ax.plot(xr, np.poly1d(z)(xr), "--",
            color=BRAND["danger"], linewidth=1.5, label="Trend")

    ax.set_xlabel("Hour of Day")
    ax.set_ylabel("Bytes Transferred")
    ax.set_xticks(range(0, 24, 2))
    ax.legend(fontsize=8, ncol=2, loc="upper right",
              facecolor=BRAND["bg"], edgecolor=BRAND["muted"])
    fig.tight_layout()
    save(fig, "09_bytes_scatter.png")


def chart_country_service(df: pd.DataFrame) -> None:
    """10 — 100 % stacked bar: service distribution per country."""
    pivot     = df.groupby(["Country", "Page"]).size().unstack(fill_value=0)
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    fig, ax = branded_fig((13, 6), "Service Distribution per Country (%)")

    pages  = pivot_pct.columns.tolist()
    bottom = np.zeros(len(pivot_pct))
    for i, page in enumerate(pages):
        ax.bar(
            pivot_pct.index, pivot_pct[page].values,
            bottom=bottom,
            color=COUNTRY_PALETTE[i % len(COUNTRY_PALETTE)],
            label=page, edgecolor="white", linewidth=0.5,
        )
        bottom += pivot_pct[page].values

    ax.set_xlabel("Country")
    ax.set_ylabel("Percentage of Requests (%)")
    ax.set_xticklabels(pivot_pct.index, rotation=30, ha="right", fontsize=9)
    ax.legend(fontsize=8, bbox_to_anchor=(1.02, 1), loc="upper left",
              facecolor=BRAND["bg"])
    ax.set_ylim(0, 100)
    fig.tight_layout()
    save(fig, "10_country_service_stacked.png")


def chart_weekly_revenue(df: pd.DataFrame) -> None:
    """11 — Bar chart: estimated engagement value (BWP) per ISO week."""
    weekly  = df.groupby("Week")["Revenue"].sum()
    fig, ax = branded_fig((10, 5), "Weekly Estimated Engagement Value (BWP)")

    bars = ax.bar(weekly.index, weekly.values,
                  color=BRAND["success"], edgecolor="white", linewidth=0.5)
    for bar in bars:
        h = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2, h + 50,
            f"${h:,.0f}", ha="center", fontsize=7,
            color=BRAND["success"], fontweight="bold",
        )

    ax.set_xlabel("Week Number")
    ax.set_ylabel("Engagement Value (USD)")
    ax.yaxis.set_major_formatter(
        mticker.FuncFormatter(lambda x, _: f"${x:,.0f}")
    )
    fig.tight_layout()
    save(fig, "11_weekly_revenue.png")


# 6. ENTRY POINT

def main() -> None:
    """Run the full analysis pipeline: load → clean → statistics → charts."""
    print("╔══════════════════════════════════════════════════════════╗")
    print("║   CyberNova Analytics Ltd — Web Server Log Analysis     ║")
    print("╚══════════════════════════════════════════════════════════╝")

    df = load_and_clean("CyberNova_Web_Logs.csv")
    print_statistics(df)

    print("\n Generating Charts ")
    chart_roi_summary(df)        # 00 — KPI summary card
    chart_country_traffic(df)    # 01 — horizontal bar:  traffic by country
    chart_page_requests(df)      # 02 — bar:             requests per page
    chart_key_interactions(df)   # 03 — bar:             jobs, AI, demos
    chart_status_pie(df)         # 04 — pie:             HTTP status codes
    chart_method_pie(df)         # 05 — pie:             HTTP methods
    chart_hourly_traffic(df)     # 06 — area/line:       peak hours
    chart_daily_trend(df)        # 07 — bar + line:      daily trend
    chart_dow_heatmap(df)        # 08 — heatmap:         day × service
    chart_bytes_scatter(df)      # 09 — scatter:         bytes vs hour
    chart_country_service(df)    # 10 — stacked bar:     service per country
    chart_weekly_revenue(df)     # 11 — bar:             weekly revenue proxy

    print(f"\n  All charts saved to  ./{CHARTS_DIR}/")
    print("   Next step → run  streamlit run dashboard.py  to open the dashboard.")


if __name__ == "__main__":
    main()