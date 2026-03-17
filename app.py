"""
Content Freshness Dashboard
A Streamlit app to visualize content freshness across a Contentstack stack.
Styled with Contentstack's dark theme design system.
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta

from contentstack_client import (
    get_content_types,
    get_entries,
    get_environments,
    get_locales,
    get_taxonomies,
    extract_tags_from_entries
)
from utils import (
    calculate_freshness,
    calculate_freshness_stats,
    calculate_freshness_by_content_type,
    entries_to_dataframe,
    filter_by_date_range,
    filter_by_publish_state,
    filter_by_environment,
    filter_by_locale,
    filter_by_tags,
    filter_by_content_types,
    get_time_period_dates,
    get_publish_state
)

st.set_page_config(
    page_title="Content Freshness Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

:root {
    --brand-amethyst: #AC75FF;
    --brand-amethyst-light: #D2B7F9;
    --brand-amethyst-accent: #AC75FF;
    --brand-amethyst-shade: #654A8C;
    --brand-amethyst-dark: #30283C;
    --brand-amethyst-darker: rgba(172, 117, 255, 0.2);
    --color-surface-1: #151515;
    --color-surface-2: #1A1919;
    --color-surface-3: #212121;
    --color-surface-4: #292928;
    --color-text-strong: #F5F5F4;
    --color-text-medium: #EBEBEA;
    --color-text-light: #E1E0E0;
    --color-text-subtle: rgba(255, 255, 255, 0.45);
    --color-border-light: #292928;
    --color-border-medium: #654A8C;
    --color-green-accent: #B0F7BA;
    --color-red-accent: #f87171;
    --color-yellow-accent: #fbbf24;
    --radius: 0.625rem;
}

/* Main app background */
.stApp {
    background: linear-gradient(180deg, #151515 0%, #1A1919 100%);
}

/* Hide default Streamlit elements */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Sidebar styling */
[data-testid="stSidebar"] {
    background: #212121 !important;
    border-right: 1px solid #292928;
}

[data-testid="stSidebar"] .stMarkdown h1,
[data-testid="stSidebar"] .stMarkdown h2,
[data-testid="stSidebar"] .stMarkdown h3 {
    color: #D2B7F9 !important;
}

[data-testid="stSidebar"] label {
    color: #E1E0E0 !important;
}

/* Main title styling */
h1 {
    font-family: 'Inter', sans-serif !important;
    font-weight: 700 !important;
    background: linear-gradient(135deg, #D2B7F9 0%, #AC75FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.5rem !important;
}

h2, h3 {
    font-family: 'Inter', sans-serif !important;
    color: #D2B7F9 !important;
    font-weight: 600 !important;
}

/* Metric cards styling - ensure consistent sizing */
[data-testid="stMetricValue"] {
    min-height: 40px !important;
}

[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid #654A8C !important;
    border-radius: 10px !important;
    padding: 20px !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 30px rgba(124, 77, 255, 0.1);
    transition: all 0.3s ease;
    min-height: 120px !important;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 40px rgba(90, 32, 185, 0.5), 0 0 40px rgba(124, 77, 255, 0.2);
    border-color: #AC75FF !important;
    background: rgba(255, 255, 255, 0.07) !important;
}

[data-testid="stMetric"] label {
    color: rgba(255, 255, 255, 0.45) !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-weight: 600 !important;
}

[data-testid="stMetric"] [data-testid="stMetricValue"] {
    color: #F5F5F4 !important;
    font-size: 1.75rem !important;
    font-weight: 600 !important;
}

[data-testid="stMetric"] [data-testid="stMetricDelta"] {
    min-height: 24px !important;
}

/* Expander styling */
.streamlit-expanderHeader {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid #292928 !important;
    border-radius: 8px !important;
    color: #D2B7F9 !important;
    font-weight: 500 !important;
}

.streamlit-expanderHeader:hover {
    border-color: #654A8C !important;
    background: rgba(255, 255, 255, 0.05) !important;
}

/* Select boxes and multiselects */
[data-testid="stSelectbox"] > div > div,
[data-testid="stMultiSelect"] > div > div {
    background: rgba(172, 117, 255, 0.1) !important;
    border: 1px solid rgba(172, 117, 255, 0.3) !important;
    border-radius: 8px !important;
    color: #F5F5F4 !important;
}

[data-testid="stSelectbox"] > div > div:hover,
[data-testid="stMultiSelect"] > div > div:hover {
    border-color: rgba(172, 117, 255, 0.5) !important;
    background: rgba(172, 117, 255, 0.15) !important;
}

/* Checkbox styling */
[data-testid="stCheckbox"] label span {
    color: #E1E0E0 !important;
}

/* Button styling */
.stButton > button {
    background: linear-gradient(135deg, #654A8C 0%, #AC75FF 100%) !important;
    color: #F5F5F4 !important;
    border: none !important;
    border-radius: 8px !important;
    padding: 10px 24px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px rgba(172, 117, 255, 0.3) !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(172, 117, 255, 0.5) !important;
}

/* Download button */
.stDownloadButton > button {
    background: rgba(172, 117, 255, 0.2) !important;
    color: #AC75FF !important;
    border: 1px solid #654A8C !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    transition: all 0.3s ease !important;
}

.stDownloadButton > button:hover {
    background: rgba(172, 117, 255, 0.3) !important;
    border-color: #AC75FF !important;
}

/* Info box styling */
.stAlert {
    background: rgba(172, 117, 255, 0.1) !important;
    border: 1px solid #654A8C !important;
    border-radius: 10px !important;
    color: #D2B7F9 !important;
}

/* Warning box styling */
[data-testid="stAlert"][data-baseweb="notification"] {
    background: rgba(251, 191, 36, 0.1) !important;
    border: 1px solid rgba(251, 191, 36, 0.3) !important;
}

/* Spinner styling */
.stSpinner > div {
    border-top-color: #AC75FF !important;
}

/* Dataframe styling */
[data-testid="stDataFrame"] {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid #654A8C !important;
    border-radius: 10px !important;
    overflow: hidden;
}

[data-testid="stDataFrame"] table {
    color: #F5F5F4 !important;
}

[data-testid="stDataFrame"] th {
    background: #654A8C !important;
    color: #F5F5F4 !important;
    font-weight: 600 !important;
    text-transform: uppercase;
    font-size: 0.75rem;
    letter-spacing: 0.05em;
}

[data-testid="stDataFrame"] td {
    border-bottom: 1px solid #292928 !important;
}

[data-testid="stDataFrame"] tr:hover td {
    background: rgba(172, 117, 255, 0.1) !important;
}

/* Plotly chart styling - no scrollbars, no overflow */
[data-testid="stPlotlyChart"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid #654A8C;
    border-radius: 12px;
    padding: 15px 15px 25px 15px;
    overflow: hidden !important;
}

[data-testid="stPlotlyChart"] > div,
[data-testid="stPlotlyChart"] iframe {
    overflow: hidden !important;
}

[data-testid="stPlotlyChart"]:hover {
    border-color: #AC75FF;
}

/* Chart column - prevent nested scroll */
[data-testid="column"] [data-testid="stPlotlyChart"] {
    overflow: hidden !important;
}

/* Horizontal rule styling */
hr {
    border: none !important;
    border-top: 1px solid #292928 !important;
    margin: 2rem 0 !important;
}

/* Caption styling */
.stCaption {
    color: rgba(255, 255, 255, 0.45) !important;
}

/* Date input styling */
[data-testid="stDateInput"] > div > div {
    background: rgba(172, 117, 255, 0.1) !important;
    border: 1px solid rgba(172, 117, 255, 0.3) !important;
    border-radius: 8px !important;
}

/* Custom header banner */
.header-banner {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid #654A8C;
    border-radius: 12px;
    padding: 20px 30px;
    margin-bottom: 30px;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.header-banner h1 {
    margin-bottom: 8px !important;
}

.header-meta {
    display: flex;
    gap: 20px;
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.875rem;
}

.header-meta-item {
    display: flex;
    align-items: center;
    gap: 6px;
}

/* Summary cards custom styling */
.summary-card {
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid #654A8C;
    border-radius: 10px;
    padding: 24px;
    text-align: center;
    transition: all 0.3s ease;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 30px rgba(124, 77, 255, 0.1);
}

.summary-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 40px rgba(90, 32, 185, 0.5), 0 0 40px rgba(124, 77, 255, 0.2);
    border-color: #AC75FF;
}

.summary-card .label {
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.75rem;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 8px;
}

.summary-card .value {
    color: #F5F5F4;
    font-size: 2rem;
    font-weight: 600;
}

.summary-card .detail {
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.8rem;
    margin-top: 8px;
}

/* Fresh badge */
.badge-fresh {
    background: rgba(176, 247, 186, 0.15);
    color: #B0F7BA;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Aging badge */
.badge-aging {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Stale badge */
.badge-stale {
    background: rgba(248, 113, 113, 0.15);
    color: #f87171;
    padding: 4px 10px;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
}

/* Footer styling - minimal bottom space */
.footer {
    margin-top: 8px;
    padding: 12px;
    border-top: 1px solid #292928;
    text-align: center;
    color: rgba(255, 255, 255, 0.45);
    font-size: 0.875rem;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 8px;
    height: 8px;
}

::-webkit-scrollbar-track {
    background: #1A1919;
}

::-webkit-scrollbar-thumb {
    background: #654A8C;
    border-radius: 4px;
}

::-webkit-scrollbar-thumb:hover {
    background: #AC75FF;
}

/* Hide the sidebar completely */
[data-testid="stSidebar"] {
    display: none !important;
}

/* Main content area */
.main .block-container {
    padding-left: 2rem !important;
    padding-right: 2rem !important;
    padding-bottom: 1rem !important;
    max-width: 100% !important;
}

/* Compact filter dropdowns */
[data-testid="stSelectbox"] > div > div {
    background: rgba(33, 33, 33, 0.9) !important;
    border: 1px solid #654A8C !important;
    border-radius: 8px !important;
    color: #F5F5F4 !important;
    min-height: 42px !important;
}

[data-testid="stSelectbox"] > div > div:hover {
    border-color: #AC75FF !important;
    background: rgba(45, 45, 45, 0.9) !important;
}

/* Filter row container */
[data-testid="stHorizontalBlock"] {
    gap: 12px !important;
}
</style>
"""

FRESHNESS_COLORS = {
    "Fresh": "#B0F7BA",
    "Aging": "#fbbf24", 
    "Stale": "#f87171",
    "Unknown": "#6c757d"
}

PLOTLY_LAYOUT = {
    "paper_bgcolor": "rgba(0,0,0,0)",
    "plot_bgcolor": "rgba(0,0,0,0)",
    "font": {"color": "#F5F5F4", "family": "Inter, sans-serif"},
    "title_font": {"color": "#D2B7F9", "size": 16},
    "xaxis": {
        "gridcolor": "rgba(101, 74, 140, 0.3)",
        "linecolor": "#654A8C",
        "tickfont": {"color": "#E1E0E0"}
    },
    "yaxis": {
        "gridcolor": "rgba(101, 74, 140, 0.3)",
        "linecolor": "#654A8C",
        "tickfont": {"color": "#E1E0E0"}
    }
}


@st.cache_data(ttl=300)
def load_content_types():
    """Load and cache content types."""
    return get_content_types()


@st.cache_data(ttl=300)
def load_environments():
    """Load and cache environments."""
    return get_environments()


@st.cache_data(ttl=300)
def load_locales():
    """Load and cache locales."""
    return get_locales()


@st.cache_data(ttl=300)
def load_taxonomies():
    """Load and cache taxonomies."""
    return get_taxonomies()


@st.cache_data(ttl=300)
def load_all_entries():
    """Load ALL entries once and cache for 5 minutes. Filtering happens client-side."""
    content_types = get_content_types()
    all_entries = []
    for ct in content_types:
        entries = get_entries(ct["uid"])
        all_entries.extend(entries)
    return all_entries


def render_inline_filters():
    """Render compact inline filters below the header."""
    
    # Load filter options
    content_types = load_content_types()
    environments = load_environments()
    locales = load_locales()
    taxonomies = load_taxonomies()
    
    ct_options = {ct["title"]: ct["uid"] for ct in content_types}
    env_options = ["All Environments"] + [env["name"] for env in environments]
    locale_options_list = ["All Locales"] + [f"{loc['name']} ({loc['code']})" for loc in locales]
    locale_code_map = {f"{loc['name']} ({loc['code']})": loc["code"] for loc in locales}
    publish_options = ["All States", "Published", "Draft", "Unpublished"]
    
    # Single row with 5 compact filters (with visible labels)
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        time_options = [
            "All time",
            "Over 7 days",
            "Over 30 days",
            "Over 90 days",
            "Over 180 days",
            "Over 1 year"
        ]
        selected_period = st.selectbox(
            "Time Period",
            options=time_options,
            index=5,
            key="time_period_select"
        )
        date_range = get_time_period_dates(selected_period)
    
    with col2:
        ct_names = ["All Content Types"] + list(ct_options.keys())
        selected_ct = st.selectbox(
            "Content Type",
            options=ct_names,
            index=0,
            key="content_type_select"
        )
        if selected_ct == "All Content Types":
            selected_ct_uids = list(ct_options.values())
        else:
            selected_ct_uids = [ct_options[selected_ct]]
    
    with col3:
        selected_env = st.selectbox(
            "Environment",
            options=env_options,
            index=0,
            key="environment_select"
        )
        selected_environments = [] if selected_env == "All Environments" else [selected_env]
    
    with col4:
        selected_locale_label = st.selectbox(
            "Locale",
            options=locale_options_list,
            index=0,
            key="locale_select"
        )
        if selected_locale_label == "All Locales":
            selected_locales = []
        else:
            selected_locales = [locale_code_map[selected_locale_label]]
    
    with col5:
        selected_publish = st.selectbox(
            "Publish State",
            options=publish_options,
            index=0,
            key="publish_state_select"
        )
        publish_states = [] if selected_publish == "All States" else [selected_publish]
    
    return {
        "date_range": date_range,
        "content_type_uids": selected_ct_uids,
        "environments": selected_environments,
        "locales": selected_locales,
        "publish_states": publish_states,
        "tag_filter_enabled": False,
        "taxonomies": [],
        "content_types": content_types
    }


def render_metrics(stats: dict):
    """Render summary metrics with custom styling."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="TOTAL ENTRIES",
            value=f"{stats['total']:,}",
            delta="100%"
        )
    
    with col2:
        st.metric(
            label="FRESH (<30 DAYS)",
            value=f"{stats['fresh']:,}",
            delta=f"{stats['fresh_pct']}%"
        )
    
    with col3:
        st.metric(
            label="AGING (30-90 DAYS)",
            value=f"{stats['aging']:,}",
            delta=f"{stats['aging_pct']}%"
        )
    
    with col4:
        st.metric(
            label="STALE (90+ DAYS)",
            value=f"{stats['stale']:,}",
            delta=f"{stats['stale_pct']}%"
        )


def render_pie_chart(stats: dict):
    """Render freshness distribution pie chart with dark theme."""
    labels = ["Fresh", "Aging", "Stale"]
    values = [stats["fresh"], stats["aging"], stats["stale"]]
    colors = [FRESHNESS_COLORS["Fresh"], FRESHNESS_COLORS["Aging"], FRESHNESS_COLORS["Stale"]]
    
    if stats.get("unknown", 0) > 0:
        labels.append("Unknown")
        values.append(stats["unknown"])
        colors.append(FRESHNESS_COLORS["Unknown"])
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.5,
        marker_colors=colors,
        textinfo="label+percent",
        textposition="inside",
        textfont={"color": "#1A1919", "size": 16, "family": "Inter, sans-serif"},
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>",
        insidetextorientation="horizontal",
        domain=dict(x=[0.05, 0.95], y=[0.05, 0.95])
    )])
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F5F5F4", family="Inter, sans-serif", size=13),
        showlegend=False,
        height=525,
        margin=dict(t=10, b=10, l=10, r=10)
    )
    
    return fig


def render_bar_chart(df_by_ct: pd.DataFrame):
    """Render stacked bar chart by content type with dark theme."""
    if df_by_ct.empty:
        return None
    
    df_melted = df_by_ct.melt(
        id_vars=["Content Type"],
        value_vars=["Fresh", "Aging", "Stale"],
        var_name="Freshness",
        value_name="Count"
    )
    
    fig = px.bar(
        df_melted,
        x="Content Type",
        y="Count",
        color="Freshness",
        color_discrete_map=FRESHNESS_COLORS,
        barmode="stack"
    )
    
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#F5F5F4", family="Inter, sans-serif", size=13),
        xaxis=dict(
            tickangle=-45,
            tickfont=dict(size=12, color="#E1E0E0"),
            title_font=dict(size=14),
            gridcolor="rgba(101, 74, 140, 0.3)",
            linecolor="#654A8C"
        ),
        yaxis=dict(
            tickfont=dict(size=12, color="#E1E0E0"),
            title_font=dict(size=14),
            gridcolor="rgba(101, 74, 140, 0.3)",
            linecolor="#654A8C"
        ),
        height=525,
        showlegend=False,
        margin=dict(t=10, b=120, l=50, r=10),
        bargap=0.15
    )
    
    fig.update_traces(
        hovertemplate="<b>%{x}</b><br>%{data.name}: %{y}<extra></extra>"
    )
    
    return fig


def render_data_table(df: pd.DataFrame):
    """Render sortable data table with dark theme styling."""
    if df.empty:
        st.info("No entries to display")
        return
    
    st.dataframe(
        df,
        use_container_width=True,
        height=400,
        column_config={
            "Title": st.column_config.TextColumn("Title", width="medium"),
            "UID": st.column_config.TextColumn("UID", width="small"),
            "Content Type": st.column_config.TextColumn("Content Type", width="medium"),
            "Status": st.column_config.TextColumn("Status", width="small"),
            "Freshness": st.column_config.TextColumn("Freshness", width="small"),
            "Days Since Update": st.column_config.NumberColumn("Days Since Update", format="%d"),
            "Last Updated": st.column_config.TextColumn("Last Updated", width="medium"),
            "Created": st.column_config.TextColumn("Created", width="medium"),
            "Tags": st.column_config.TextColumn("Tags", width="medium"),
            "Locale": st.column_config.TextColumn("Locale", width="small"),
        }
    )


def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
    
    # Header
    st.markdown("""
        <div class="header-banner">
            <h1>
                <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#AC75FF" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="vertical-align: middle; margin-right: 10px;">
                    <line x1="18" y1="20" x2="18" y2="10"></line>
                    <line x1="12" y1="20" x2="12" y2="4"></line>
                    <line x1="6" y1="20" x2="6" y2="14"></line>
                </svg>
                Content Freshness Dashboard
            </h1>
            <div class="header-meta">
                <div class="header-meta-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <polyline points="23 4 23 10 17 10"></polyline>
                        <polyline points="1 20 1 14 7 14"></polyline>
                        <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                    </svg>
                    <span>Real-time content freshness monitoring</span>
                </div>
                <div class="header-meta-item">
                    <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="2" width="20" height="8" rx="2" ry="2"></rect>
                        <rect x="2" y="14" width="20" height="8" rx="2" ry="2"></rect>
                        <line x1="6" y1="6" x2="6.01" y2="6"></line>
                        <line x1="6" y1="18" x2="6.01" y2="18"></line>
                    </svg>
                    <span>Powered by Contentstack</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Inline filters below header
    filters = render_inline_filters()
    
    if not filters["content_type_uids"]:
        st.warning("⚠️ Please select at least one content type")
        return
    
    # Load ALL entries once (cached for 5 minutes) - no API calls on filter changes
    with st.spinner("Loading entries..."):
        all_entries = load_all_entries()
    
    if not all_entries:
        st.warning("⚠️ No entries found")
        return
    
    # All filtering happens client-side (fast, no API calls)
    filtered_entries = all_entries.copy()
    
    # Apply content type filter (client-side)
    filtered_entries = filter_by_content_types(filtered_entries, filters["content_type_uids"])
    
    # Apply time period filter
    start_date, end_date = filters["date_range"]
    if start_date:
        filtered_entries = filter_by_date_range(
            filtered_entries,
            start_date=start_date,
            end_date=end_date
        )
    
    # Apply environment filter
    if filters["environments"]:
        filtered_entries = filter_by_environment(
            filtered_entries,
            filters["environments"]
        )
    
    # Apply locale filter
    if filters["locales"]:
        filtered_entries = filter_by_locale(
            filtered_entries,
            filters["locales"]
        )
    
    # Apply publish state filter
    if filters["publish_states"]:
        filtered_entries = filter_by_publish_state(
            filtered_entries,
            filters["publish_states"]
        )
    
    ct_map = {ct["uid"]: ct["title"] for ct in filters["content_types"]}
    
    stats = calculate_freshness_stats(filtered_entries)
    
    st.markdown("### 📈 Summary Overview")
    render_metrics(stats)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("<h4 style='text-align: center; color: #D2B7F9; margin-bottom: 0; font-size: 1.15rem;'>Freshness Distribution</h4>", unsafe_allow_html=True)
        if stats["total"] > 0:
            pie_fig = render_pie_chart(stats)
            st.plotly_chart(pie_fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
        else:
            st.info("No data to display")
    
    with col2:
        st.markdown("<h4 style='text-align: center; color: #D2B7F9; margin-bottom: 0; font-size: 1.15rem;'>Entries by Content Type</h4>", unsafe_allow_html=True)
        df_by_ct = calculate_freshness_by_content_type(filtered_entries, ct_map)
        if not df_by_ct.empty:
            bar_fig = render_bar_chart(df_by_ct)
            if bar_fig:
                st.plotly_chart(bar_fig, use_container_width=True, config={'displayModeBar': False, 'scrollZoom': False})
        else:
            st.info("No data to display")
    
    # Shared legend below both charts
    st.markdown("""
        <div style="display: flex; justify-content: center; gap: 28px; margin-top: 24px; margin-bottom: 8px; padding-top: 16px; border-top: 1px solid rgba(101, 74, 140, 0.3);">
            <span style="display: flex; align-items: center; gap: 8px; color: #E1E0E0; font-size: 1rem;">
                <span style="width: 14px; height: 14px; border-radius: 2px; background: #B0F7BA; display: inline-block;"></span> Fresh (&lt;30 days)
            </span>
            <span style="display: flex; align-items: center; gap: 8px; color: #E1E0E0; font-size: 1rem;">
                <span style="width: 14px; height: 14px; border-radius: 2px; background: #fbbf24; display: inline-block;"></span> Aging (30-90 days)
            </span>
            <span style="display: flex; align-items: center; gap: 8px; color: #E1E0E0; font-size: 1rem;">
                <span style="width: 14px; height: 14px; border-radius: 2px; background: #f87171; display: inline-block;"></span> Stale (90+ days)
            </span>
        </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📋 Entry Details")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        sort_by = st.selectbox(
            "Sort by",
            options=["Days Since Update", "Title", "Content Type", "Last Updated"],
            index=0
        )
    with col2:
        sort_order = st.selectbox(
            "Order",
            options=["Descending", "Ascending"],
            index=0
        )
    with col3:
        freshness_filter = st.multiselect(
            "Filter by freshness",
            options=["Fresh", "Aging", "Stale", "Unknown"],
            default=[]
        )
    
    df = entries_to_dataframe(filtered_entries, ct_map)
    
    if freshness_filter:
        df = df[df["Freshness"].isin(freshness_filter)]
    
    if not df.empty:
        ascending = sort_order == "Ascending"
        df = df.sort_values(sort_by, ascending=ascending, na_position="last")
    
    render_data_table(df)
    
    st.markdown("---")
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 Download as CSV",
            data=df.to_csv(index=False),
            file_name=f"content_freshness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    with col2:
        st.caption(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    st.markdown("""
        <div class="footer">
            <p>Content Freshness Dashboard • Powered by Contentstack</p>
            <p style="margin-top: 8px; font-size: 0.75rem;">© 2024 Contentstack. All rights reserved.</p>
        </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
