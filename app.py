"""
Nassau Candy Distributor
Factory-to-Customer Shipping Route Efficiency Dashboard
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from data_loader import load_and_prepare_data
from config import FACTORY_COORDS, PRODUCT_FACTORY_MAP, US_STATE_COORDS

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nassau Candy – Route Efficiency",
    page_icon="🍬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stMetricValue"] { font-size: 2rem; font-weight: 700; }
    .block-container { padding-top: 1.5rem; }
    h1 { color: #B5360E; }
    h2, h3 { color: #7B2D8B; }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
    .stTabs [data-baseweb="tab"] {
        background-color: #F5E6FB;
        border-radius: 6px 6px 0 0;
        padding: 6px 18px;
        font-weight: 600;
    }
    .stTabs [aria-selected="true"] { background-color: #7B2D8B; color: white; }
</style>
""", unsafe_allow_html=True)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def get_data():
    return load_and_prepare_data("Nassau_Candy_Distributor.csv")

df_raw = get_data()

# ── Sidebar Filters ────────────────────────────────────────────────────────────
st.sidebar.image("https://upload.wikimedia.org/wikipedia/en/thumb/4/4f/Nassau_Candy_logo.svg/200px-Nassau_Candy_logo.svg.png",
                 use_container_width=True, caption="Nassau Candy Distributor")

st.sidebar.title("🔧 Filters")

# Date range
min_date = df_raw["Order Date"].min().date()
max_date = df_raw["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order Date Range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# Region filter
all_regions = sorted(df_raw["Region"].dropna().unique())
selected_regions = st.sidebar.multiselect("Region", all_regions, default=all_regions)

# State filter
all_states = sorted(df_raw["State/Province"].dropna().unique())
selected_states = st.sidebar.multiselect("State / Province", all_states, default=all_states)

# Ship Mode filter
all_modes = sorted(df_raw["Ship Mode"].dropna().unique())
selected_modes = st.sidebar.multiselect("Ship Mode", all_modes, default=all_modes)

# Lead-time threshold slider
lead_time_threshold = st.sidebar.slider(
    "Delay Threshold (days)", min_value=100, max_value=2000, value=1300,
    help="Orders with lead time above this value are considered delayed."
)

# Division filter
all_divisions = sorted(df_raw["Division"].dropna().unique())
selected_divisions = st.sidebar.multiselect("Product Division", all_divisions, default=all_divisions)

# ── Apply filters ──────────────────────────────────────────────────────────────
df = df_raw[
    (df_raw["Order Date"].dt.date >= start_date) &
    (df_raw["Order Date"].dt.date <= end_date) &
    (df_raw["Region"].isin(selected_regions)) &
    (df_raw["State/Province"].isin(selected_states)) &
    (df_raw["Ship Mode"].isin(selected_modes)) &
    (df_raw["Division"].isin(selected_divisions))
].copy()

df["Delayed"] = df["Lead Time (Days)"] > lead_time_threshold

if df.empty:
    st.warning("No data matches the current filters. Please broaden your selection.")
    st.stop()

# ── Header ─────────────────────────────────────────────────────────────────────
st.title("🍬 Nassau Candy Distributor")
st.subheader("Factory-to-Customer Shipping Route Efficiency Dashboard")
st.caption(f"Showing **{len(df):,}** orders  |  {start_date} → {end_date}")

# ── KPI Row ────────────────────────────────────────────────────────────────────
kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
avg_lead   = df["Lead Time (Days)"].mean()
delay_pct  = df["Delayed"].mean() * 100
total_rev  = df["Sales"].sum()
total_profit = df["Gross Profit"].sum()
unique_routes = df["Route"].nunique()

kpi1.metric("Avg Lead Time", f"{avg_lead:.1f} days")
kpi2.metric("Delay Rate", f"{delay_pct:.1f}%", delta=f">{lead_time_threshold}d threshold", delta_color="inverse")
kpi3.metric("Total Revenue", f"${total_rev:,.0f}")
kpi4.metric("Gross Profit", f"${total_profit:,.0f}")
kpi5.metric("Active Routes", f"{unique_routes}")

st.divider()

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Route Efficiency Overview",
    "🗺️ Geographic Shipping Map",
    "🚚 Ship Mode Comparison",
    "🔍 Route Drill-Down",
    "📦 Order-Level Timeline",
])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Route Efficiency Overview
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.header("Route Efficiency Overview")

    route_agg = (
        df.groupby("Route")
        .agg(
            Shipments=("Lead Time (Days)", "count"),
            Avg_Lead_Time=("Lead Time (Days)", "mean"),
            Std_Lead_Time=("Lead Time (Days)", "std"),
            Delay_Rate=("Delayed", "mean"),
            Total_Sales=("Sales", "sum"),
        )
        .reset_index()
    )
    route_agg["Delay_Rate_Pct"] = route_agg["Delay_Rate"] * 100
    route_agg["Std_Lead_Time"] = route_agg["Std_Lead_Time"].fillna(0)

    # Efficiency Score: lower avg lead time & lower delay → higher score
    max_lt = route_agg["Avg_Lead_Time"].max()
    max_dr = route_agg["Delay_Rate_Pct"].max() or 1
    route_agg["Efficiency_Score"] = (
        (1 - route_agg["Avg_Lead_Time"] / max_lt) * 0.6
        + (1 - route_agg["Delay_Rate_Pct"] / max_dr) * 0.4
    ) * 100

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("🏆 Top 10 Most Efficient Routes")
        top10 = route_agg.nlargest(10, "Efficiency_Score")
        fig_top = px.bar(
            top10, x="Efficiency_Score", y="Route", orientation="h",
            color="Efficiency_Score", color_continuous_scale="Greens",
            labels={"Efficiency_Score": "Efficiency Score (0-100)", "Route": ""},
            text=top10["Avg_Lead_Time"].map(lambda x: f"{x:.1f}d"),
        )
        fig_top.update_traces(textposition="outside")
        fig_top.update_layout(
            yaxis={"categoryorder": "total ascending"},
            coloraxis_showscale=False, height=420,
            margin=dict(l=0, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_top, use_container_width=True)

    with col_b:
        st.subheader("⚠️ Bottom 10 Least Efficient Routes")
        bot10 = route_agg.nsmallest(10, "Efficiency_Score")
        fig_bot = px.bar(
            bot10, x="Efficiency_Score", y="Route", orientation="h",
            color="Efficiency_Score", color_continuous_scale="Reds_r",
            labels={"Efficiency_Score": "Efficiency Score (0-100)", "Route": ""},
            text=bot10["Avg_Lead_Time"].map(lambda x: f"{x:.1f}d"),
        )
        fig_bot.update_traces(textposition="outside")
        fig_bot.update_layout(
            yaxis={"categoryorder": "total descending"},
            coloraxis_showscale=False, height=420,
            margin=dict(l=0, r=20, t=20, b=20),
        )
        st.plotly_chart(fig_bot, use_container_width=True)

    st.subheader("📋 Full Route Performance Leaderboard")
    display_df = route_agg.sort_values("Efficiency_Score", ascending=False).copy()
    display_df["Avg_Lead_Time"] = display_df["Avg_Lead_Time"].round(2)
    display_df["Delay_Rate_Pct"] = display_df["Delay_Rate_Pct"].round(1)
    display_df["Efficiency_Score"] = display_df["Efficiency_Score"].round(1)
    display_df["Total_Sales"] = display_df["Total_Sales"].map("${:,.0f}".format)
    display_df = display_df.rename(columns={
        "Route": "Route",
        "Shipments": "# Shipments",
        "Avg_Lead_Time": "Avg Lead Time (days)",
        "Std_Lead_Time": "Std Dev",
        "Delay_Rate_Pct": "Delay Rate (%)",
        "Efficiency_Score": "Efficiency Score",
        "Total_Sales": "Total Sales",
    })
    st.dataframe(display_df.drop(columns=["Delay_Rate"]), use_container_width=True, height=350)

    # Lead time distribution
    st.subheader("Lead Time Distribution by Factory")
    fig_box = px.box(
        df, x="Factory", y="Lead Time (Days)",
        color="Factory", points="outliers",
        labels={"Lead Time (Days)": "Lead Time (days)"},
    )
    fig_box.add_hline(y=lead_time_threshold, line_dash="dash", line_color="red",
                      annotation_text=f"Delay threshold ({lead_time_threshold}d)")
    fig_box.update_layout(showlegend=False, height=380,
                          margin=dict(l=0, r=0, t=20, b=20))
    st.plotly_chart(fig_box, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Geographic Shipping Map
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.header("Geographic Shipping Map")

    state_agg = (
        df.groupby("State/Province")
        .agg(
            Shipments=("Lead Time (Days)", "count"),
            Avg_Lead_Time=("Lead Time (Days)", "mean"),
            Delay_Rate=("Delayed", "mean"),
        )
        .reset_index()
    )
    state_agg["Delay_Rate_Pct"] = (state_agg["Delay_Rate"] * 100).round(1)
    state_agg["Avg_Lead_Time"] = state_agg["Avg_Lead_Time"].round(2)

    map_metric = st.radio(
        "Color map by:", ["Avg Lead Time (days)", "Delay Rate (%)", "Shipment Volume"],
        horizontal=True,
    )
    metric_col_map = {
        "Avg Lead Time (days)": ("Avg_Lead_Time", "YlOrRd"),
        "Delay Rate (%)": ("Delay_Rate_Pct", "Reds"),
        "Shipment Volume": ("Shipments", "Blues"),
    }
    col_name, color_scale = metric_col_map[map_metric]

    fig_map = px.choropleth(
        state_agg,
        locations="State/Province",
        locationmode="USA-states",
        color=col_name,
        color_continuous_scale=color_scale,
        scope="usa",
        hover_name="State/Province",
        hover_data={"Avg_Lead_Time": ":.2f", "Delay_Rate_Pct": ":.1f", "Shipments": True},
        labels={
            "Avg_Lead_Time": "Avg Lead Time (days)",
            "Delay_Rate_Pct": "Delay Rate (%)",
            "Shipments": "# Shipments",
            col_name: map_metric,
        },
        title=f"US Heatmap – {map_metric}",
    )

    # Overlay factory locations
    factory_df = pd.DataFrame([
        {"Factory": k, "lat": v["lat"], "lon": v["lon"]}
        for k, v in FACTORY_COORDS.items()
    ])
    fig_map.add_scattergeo(
        lat=factory_df["lat"], lon=factory_df["lon"],
        text=factory_df["Factory"],
        mode="markers+text",
        marker=dict(size=12, color="#7B2D8B", symbol="star"),
        textposition="top center",
        name="Factories",
        showlegend=True,
    )
    fig_map.update_layout(height=520, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_map, use_container_width=True)

    # Regional bottleneck table
    st.subheader("Regional Bottleneck Analysis")
    region_agg = (
        df.groupby("Region")
        .agg(
            Shipments=("Lead Time (Days)", "count"),
            Avg_Lead_Time=("Lead Time (Days)", "mean"),
            Delay_Rate=("Delayed", "mean"),
        )
        .reset_index()
        .sort_values("Avg_Lead_Time", ascending=False)
    )
    region_agg["Delay_Rate_Pct"] = (region_agg["Delay_Rate"] * 100).round(1)
    region_agg["Avg_Lead_Time"] = region_agg["Avg_Lead_Time"].round(2)

    fig_region = px.scatter(
        region_agg,
        x="Avg_Lead_Time", y="Delay_Rate_Pct",
        size="Shipments", color="Region",
        hover_name="Region",
        labels={
            "Avg_Lead_Time": "Avg Lead Time (days)",
            "Delay_Rate_Pct": "Delay Rate (%)",
            "Shipments": "# Shipments",
        },
        title="Region: Avg Lead Time vs Delay Rate (bubble size = volume)",
    )
    fig_region.add_vline(x=df["Lead Time (Days)"].mean(), line_dash="dot",
                         annotation_text="Overall Avg LT")
    fig_region.add_hline(y=df["Delayed"].mean() * 100, line_dash="dot",
                         annotation_text="Overall Delay Rate")
    fig_region.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_region, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 – Ship Mode Comparison
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.header("Ship Mode Performance Comparison")

    mode_agg = (
        df.groupby("Ship Mode")
        .agg(
            Shipments=("Lead Time (Days)", "count"),
            Avg_Lead_Time=("Lead Time (Days)", "mean"),
            Median_Lead_Time=("Lead Time (Days)", "median"),
            Std_Lead_Time=("Lead Time (Days)", "std"),
            Delay_Rate=("Delayed", "mean"),
            Avg_Sales=("Sales", "mean"),
            Total_Sales=("Sales", "sum"),
            Avg_Cost=("Cost", "mean"),
        )
        .reset_index()
    )
    mode_agg["Delay_Rate_Pct"] = (mode_agg["Delay_Rate"] * 100).round(1)

    c1, c2 = st.columns(2)

    with c1:
        fig_mode_lt = px.bar(
            mode_agg.sort_values("Avg_Lead_Time"),
            x="Ship Mode", y="Avg_Lead_Time",
            color="Ship Mode", text="Avg_Lead_Time",
            labels={"Avg_Lead_Time": "Avg Lead Time (days)"},
            title="Average Lead Time by Ship Mode",
            error_y="Std_Lead_Time",
        )
        fig_mode_lt.update_traces(texttemplate="%{text:.1f}d", textposition="outside")
        fig_mode_lt.update_layout(showlegend=False, height=380,
                                  margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_mode_lt, use_container_width=True)

    with c2:
        fig_mode_dr = px.bar(
            mode_agg.sort_values("Delay_Rate_Pct"),
            x="Ship Mode", y="Delay_Rate_Pct",
            color="Ship Mode", text="Delay_Rate_Pct",
            labels={"Delay_Rate_Pct": "Delay Rate (%)"},
            title=f"Delay Rate by Ship Mode (threshold: {lead_time_threshold}d)",
        )
        fig_mode_dr.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig_mode_dr.update_layout(showlegend=False, height=380,
                                  margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_mode_dr, use_container_width=True)

    # Violin – lead time distribution per mode
    st.subheader("Lead Time Distribution by Ship Mode")
    fig_violin = px.violin(
        df, x="Ship Mode", y="Lead Time (Days)",
        color="Ship Mode", box=True, points="outliers",
        labels={"Lead Time (Days)": "Lead Time (days)"},
    )
    fig_violin.add_hline(y=lead_time_threshold, line_dash="dash", line_color="red",
                         annotation_text=f"Delay threshold ({lead_time_threshold}d)")
    fig_violin.update_layout(showlegend=False, height=400,
                             margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig_violin, use_container_width=True)

    # Cost-time trade-off
    st.subheader("Cost vs Lead Time Trade-off by Ship Mode")
    fig_scatter = px.scatter(
        df.sample(min(3000, len(df)), random_state=42),
        x="Lead Time (Days)", y="Cost",
        color="Ship Mode", opacity=0.5,
        labels={"Cost": "Order Cost ($)", "Lead Time (Days)": "Lead Time (days)"},
        title="Individual Orders – Cost vs Lead Time",
    )
    fig_scatter.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_scatter, use_container_width=True)

    # Summary table
    st.subheader("Ship Mode Summary")
    mode_display = mode_agg.copy()
    mode_display["Avg_Sales"] = mode_display["Avg_Sales"].map("${:,.2f}".format)
    mode_display["Total_Sales"] = mode_display["Total_Sales"].map("${:,.0f}".format)
    mode_display["Avg_Cost"] = mode_display["Avg_Cost"].map("${:,.2f}".format)
    mode_display["Avg_Lead_Time"] = mode_display["Avg_Lead_Time"].round(2)
    mode_display["Median_Lead_Time"] = mode_display["Median_Lead_Time"].round(2)
    mode_display = mode_display.drop(columns=["Delay_Rate", "Std_Lead_Time"])
    mode_display.columns = ["Ship Mode", "# Shipments", "Avg LT (days)",
                             "Median LT (days)", "Delay Rate (%)",
                             "Avg Sales", "Total Sales", "Avg Cost"]
    st.dataframe(mode_display, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 4 – Route Drill-Down
# ═══════════════════════════════════════════════════════════════════════════════
with tab4:
    st.header("Route Drill-Down")

    col_sel, col_state = st.columns(2)
    with col_sel:
        factory_sel = st.selectbox(
            "Select Factory", sorted(df["Factory"].dropna().unique())
        )
    with col_state:
        states_for_factory = sorted(
            df[df["Factory"] == factory_sel]["State/Province"].dropna().unique()
        )
        state_sel = st.selectbox("Select Destination State", states_for_factory)

    route_df = df[
        (df["Factory"] == factory_sel) & (df["State/Province"] == state_sel)
    ]

    if route_df.empty:
        st.info("No orders found for this factory → state combination.")
    else:
        st.markdown(f"**Route:** {factory_sel} → {state_sel} &nbsp; | &nbsp; **{len(route_df):,} orders**")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Avg Lead Time", f"{route_df['Lead Time (Days)'].mean():.1f}d")
        m2.metric("Delay Rate", f"{route_df['Delayed'].mean()*100:.1f}%")
        m3.metric("Total Sales", f"${route_df['Sales'].sum():,.0f}")
        m4.metric("Gross Profit", f"${route_df['Gross Profit'].sum():,.0f}")

        # Monthly trend
        route_monthly = (
            route_df.set_index("Order Date")
            .resample("ME")["Lead Time (Days)"]
            .mean()
            .reset_index()
        )
        route_monthly.columns = ["Month", "Avg Lead Time"]

        fig_trend = px.line(
            route_monthly, x="Month", y="Avg Lead Time",
            markers=True, title=f"Monthly Avg Lead Time – {factory_sel} → {state_sel}",
        )
        fig_trend.add_hline(y=lead_time_threshold, line_dash="dash", line_color="red",
                            annotation_text="Delay threshold")
        fig_trend.update_layout(height=340, margin=dict(l=0, r=0, t=40, b=0))
        st.plotly_chart(fig_trend, use_container_width=True)

        # Ship mode breakdown for this route
        c_a, c_b = st.columns(2)
        with c_a:
            mode_route = route_df.groupby("Ship Mode")["Lead Time (Days)"].mean().reset_index()
            fig_rm = px.bar(mode_route, x="Ship Mode", y="Lead Time (Days)",
                            color="Ship Mode", title="Avg Lead Time by Ship Mode")
            fig_rm.update_layout(showlegend=False, height=300,
                                 margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_rm, use_container_width=True)

        with c_b:
            prod_route = route_df.groupby("Product Name")["Lead Time (Days)"].mean().nlargest(10).reset_index()
            fig_rp = px.bar(prod_route, x="Lead Time (Days)", y="Product Name",
                            orientation="h", title="Avg Lead Time by Product (Top 10)")
            fig_rp.update_layout(yaxis={"categoryorder": "total ascending"},
                                 height=300, margin=dict(l=0, r=0, t=40, b=0))
            st.plotly_chart(fig_rp, use_container_width=True)

        st.subheader("State-Level Performance – All Routes from This Factory")
        state_perf = (
            df[df["Factory"] == factory_sel]
            .groupby("State/Province")
            .agg(
                Shipments=("Lead Time (Days)", "count"),
                Avg_Lead_Time=("Lead Time (Days)", "mean"),
                Delay_Rate=("Delayed", "mean"),
            )
            .reset_index()
            .sort_values("Avg_Lead_Time")
        )
        state_perf["Delay_Rate_Pct"] = (state_perf["Delay_Rate"] * 100).round(1)
        state_perf["Avg_Lead_Time"] = state_perf["Avg_Lead_Time"].round(2)
        fig_state_bar = px.bar(
            state_perf, x="State/Province", y="Avg_Lead_Time",
            color="Delay_Rate_Pct", color_continuous_scale="YlOrRd",
            labels={"Avg_Lead_Time": "Avg Lead Time (days)", "Delay_Rate_Pct": "Delay Rate (%)"},
            title=f"All Destination States from {factory_sel}",
        )
        fig_state_bar.add_hline(y=lead_time_threshold, line_dash="dash", line_color="red")
        fig_state_bar.update_layout(height=380, margin=dict(l=0, r=0, t=40, b=0),
                                    xaxis_tickangle=-45)
        st.plotly_chart(fig_state_bar, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════════
# TAB 5 – Order-Level Timeline
# ═══════════════════════════════════════════════════════════════════════════════
with tab5:
    st.header("Order-Level Shipment Timelines")

    col_f, col_r, col_m = st.columns(3)
    with col_f:
        tl_factory = st.selectbox("Factory", ["All"] + sorted(df["Factory"].dropna().unique()), key="tl_f")
    with col_r:
        tl_region = st.selectbox("Region", ["All"] + sorted(df["Region"].dropna().unique()), key="tl_r")
    with col_m:
        tl_mode = st.selectbox("Ship Mode", ["All"] + sorted(df["Ship Mode"].dropna().unique()), key="tl_m")

    tl_df = df.copy()
    if tl_factory != "All":
        tl_df = tl_df[tl_df["Factory"] == tl_factory]
    if tl_region != "All":
        tl_df = tl_df[tl_df["Region"] == tl_region]
    if tl_mode != "All":
        tl_df = tl_df[tl_df["Ship Mode"] == tl_mode]

    # Lead time histogram
    fig_hist = px.histogram(
        tl_df, x="Lead Time (Days)", color="Ship Mode",
        nbins=30, barmode="overlay",
        labels={"Lead Time (Days)": "Lead Time (days)"},
        title="Lead Time Frequency Distribution",
    )
    fig_hist.add_vline(x=lead_time_threshold, line_dash="dash", line_color="red",
                       annotation_text=f"Threshold ({lead_time_threshold}d)")
    fig_hist.add_vline(x=tl_df["Lead Time (Days)"].mean(), line_dash="dot", line_color="blue",
                       annotation_text="Mean")
    fig_hist.update_layout(height=360, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_hist, use_container_width=True)

    # Weekly volume & avg lead time
    weekly = (
        tl_df.set_index("Order Date")
        .resample("W")
        .agg(Orders=("Lead Time (Days)", "count"), Avg_LT=("Lead Time (Days)", "mean"))
        .reset_index()
    )

    fig_dual = make_subplots(specs=[[{"secondary_y": True}]])
    fig_dual.add_trace(
        go.Bar(x=weekly["Order Date"], y=weekly["Orders"], name="# Orders",
               marker_color="#A8DADC"), secondary_y=False
    )
    fig_dual.add_trace(
        go.Scatter(x=weekly["Order Date"], y=weekly["Avg_LT"], name="Avg Lead Time",
                   line=dict(color="#E63946", width=2)), secondary_y=True
    )
    fig_dual.update_yaxes(title_text="# Orders", secondary_y=False)
    fig_dual.update_yaxes(title_text="Avg Lead Time (days)", secondary_y=True)
    fig_dual.update_layout(title="Weekly Order Volume & Avg Lead Time",
                           height=380, margin=dict(l=0, r=0, t=40, b=0))
    st.plotly_chart(fig_dual, use_container_width=True)

    # Sample orders table
    st.subheader("Sample Orders (up to 500 rows)")
    show_cols = ["Order ID", "Order Date", "Ship Date", "Lead Time (Days)",
                 "Delayed", "Ship Mode", "Factory", "State/Province",
                 "Region", "Product Name", "Sales", "Gross Profit"]
    show_cols = [c for c in show_cols if c in tl_df.columns]

    sample_df = tl_df[show_cols].sort_values("Lead Time (Days)", ascending=False).head(500)
    sample_df["Order Date"] = sample_df["Order Date"].dt.strftime("%Y-%m-%d")
    sample_df["Ship Date"] = sample_df["Ship Date"].dt.strftime("%Y-%m-%d")
    sample_df["Sales"] = sample_df["Sales"].map("${:,.2f}".format)
    sample_df["Gross Profit"] = sample_df["Gross Profit"].map("${:,.2f}".format)

    st.dataframe(
        sample_df.style.map(
            lambda v: "background-color:#FFDDC1" if v is True else "",
            subset=["Delayed"]
        ),
        use_container_width=True, height=400
    )

st.divider()
st.caption("Nassau Candy Distributor · Route Efficiency Dashboard · Built with Streamlit & Plotly")
