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
    filter_by_tags,
    filter_by_content_types,
    get_time_period_dates,
    get_publish_state
)

st.set_page_config(
    page_title="Content Freshness Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
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

/* Metric cards styling */
[data-testid="stMetric"] {
    background: rgba(255, 255, 255, 0.03);
    border: 1px solid #654A8C;
    border-radius: 10px;
    padding: 20px;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 30px rgba(124, 77, 255, 0.1);
    transition: all 0.3s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 40px rgba(90, 32, 185, 0.5), 0 0 40px rgba(124, 77, 255, 0.2);
    border-color: #AC75FF;
    background: rgba(255, 255, 255, 0.07);
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

/* Plotly chart container */
.js-plotly-plot {
    background: rgba(255, 255, 255, 0.03) !important;
    border: 1px solid #654A8C !important;
    border-radius: 12px !important;
    padding: 15px !important;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3), 0 0 20px rgba(124, 77, 255, 0.1);
    transition: all 0.3s ease;
}

.js-plotly-plot:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 40px rgba(90, 32, 185, 0.5), 0 0 40px rgba(124, 77, 255, 0.2);
    border-color: #AC75FF;
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

/* Footer styling */
.footer {
    margin-top: 60px;
    padding: 20px;
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


@st.cache_data(ttl=60)
def load_entries_for_content_types(content_type_uids: tuple, locale: str = None):
    """Load entries for specified content types."""
    all_entries = []
    for ct_uid in content_type_uids:
        entries = get_entries(ct_uid, locale=locale)
        all_entries.extend(entries)
    return all_entries


def render_sidebar():
    """Render the sidebar with all filters."""
    st.sidebar.markdown("## 🎛️ Filters")
    
    with st.sidebar.expander("📅 Time Period", expanded=True):
        time_options = [
            "Over 7 days",
            "Over 30 days",
            "Over 90 days",
            "Over 180 days",
            "Over 1 year",
            "All time",
            "Custom"
        ]
        selected_period = st.selectbox(
            "Select time period",
            options=time_options,
            index=1
        )
        
        if selected_period == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start date",
                    value=datetime.now() - timedelta(days=30)
                )
            with col2:
                end_date = st.date_input(
                    "End date",
                    value=datetime.now()
                )
            date_range = (
                datetime.combine(start_date, datetime.min.time()),
                datetime.combine(end_date, datetime.max.time())
            )
        else:
            date_range = get_time_period_dates(selected_period)
    
    with st.sidebar.expander("📄 Content Type", expanded=True):
        content_types = load_content_types()
        ct_options = {ct["title"]: ct["uid"] for ct in content_types}
        
        select_all_ct = st.checkbox("Select all content types", value=True, key="select_all_ct")
        
        if select_all_ct:
            selected_ct_names = list(ct_options.keys())
        else:
            selected_ct_names = st.multiselect(
                "Select content types",
                options=list(ct_options.keys()),
                default=[]
            )
        
        selected_ct_uids = [ct_options[name] for name in selected_ct_names]
    
    with st.sidebar.expander("🌍 Environment", expanded=False):
        environments = load_environments()
        env_options = [env["name"] for env in environments]
        selected_environments = st.multiselect(
            "Select environments",
            options=env_options,
            default=[]
        )
    
    with st.sidebar.expander("🌐 Locale", expanded=False):
        locales = load_locales()
        locale_options = {f"{loc['name']} ({loc['code']})": loc["code"] for loc in locales}
        selected_locale_labels = st.multiselect(
            "Select locales",
            options=list(locale_options.keys()),
            default=[]
        )
        selected_locales = [locale_options[label] for label in selected_locale_labels]
    
    with st.sidebar.expander("📤 Publish State", expanded=False):
        publish_states = st.multiselect(
            "Select publish states",
            options=["Published", "Draft", "Unpublished"],
            default=[]
        )
    
    with st.sidebar.expander("🏷️ Tags", expanded=False):
        st.info("Tags will be populated after loading entries")
        tag_filter_enabled = st.checkbox("Enable tag filter", value=False)
    
    with st.sidebar.expander("📂 Taxonomies", expanded=False):
        taxonomies = load_taxonomies()
        if taxonomies:
            tax_options = {tax["name"]: tax["uid"] for tax in taxonomies}
            selected_tax_names = st.multiselect(
                "Select taxonomies",
                options=list(tax_options.keys()),
                default=[]
            )
            selected_taxonomies = [tax_options[name] for name in selected_tax_names]
        else:
            st.info("No taxonomies found in this stack")
            selected_taxonomies = []
    
    return {
        "date_range": date_range,
        "content_type_uids": selected_ct_uids,
        "environments": selected_environments,
        "locales": selected_locales,
        "publish_states": publish_states,
        "tag_filter_enabled": tag_filter_enabled,
        "taxonomies": selected_taxonomies,
        "content_types": content_types
    }


def render_metrics(stats: dict):
    """Render summary metrics with custom styling."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📊 Total Entries",
            value=f"{stats['total']:,}"
        )
    
    with col2:
        st.metric(
            label="✅ Fresh (<30 days)",
            value=f"{stats['fresh']:,}",
            delta=f"{stats['fresh_pct']}%"
        )
    
    with col3:
        st.metric(
            label="⚠️ Aging (30-90 days)",
            value=f"{stats['aging']:,}",
            delta=f"{stats['aging_pct']}%"
        )
    
    with col4:
        st.metric(
            label="🔴 Stale (90+ days)",
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
        textposition="outside",
        textfont={"color": "#F5F5F4", "size": 12},
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
    )])
    
    fig.update_layout(
        **PLOTLY_LAYOUT,
        title=dict(text="Content Freshness Distribution", x=0.5, font=dict(color="#D2B7F9", size=16)),
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(color="#E1E0E0", size=11)
        ),
        height=400,
        margin=dict(t=60, b=60, l=20, r=20)
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
        **PLOTLY_LAYOUT,
        title=dict(text="Entries by Content Type", x=0.5, font=dict(color="#D2B7F9", size=16)),
        xaxis_tickangle=-45,
        height=400,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.35,
            xanchor="center",
            x=0.5,
            font=dict(color="#E1E0E0", size=11)
        ),
        margin=dict(t=60, b=100, l=40, r=20),
        bargap=0.2
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
    
    st.markdown("""
        <div class="header-banner">
            <h1>📊 Content Freshness Dashboard</h1>
            <div class="header-meta">
                <div class="header-meta-item">
                    <span>🔄</span>
                    <span>Real-time content freshness monitoring</span>
                </div>
                <div class="header-meta-item">
                    <span>📈</span>
                    <span>Powered by Contentstack</span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    filters = render_sidebar()
    
    if not filters["content_type_uids"]:
        st.warning("⚠️ Please select at least one content type from the sidebar")
        return
    
    with st.spinner("Loading entries..."):
        locale = filters["locales"][0] if filters["locales"] else None
        entries = load_entries_for_content_types(
            tuple(filters["content_type_uids"]),
            locale=locale
        )
    
    if not entries:
        st.warning("⚠️ No entries found for the selected content types")
        return
    
    filtered_entries = entries.copy()
    
    start_date, end_date = filters["date_range"]
    if start_date:
        filtered_entries = filter_by_date_range(
            filtered_entries,
            start_date=start_date,
            end_date=end_date
        )
    
    if filters["publish_states"]:
        filtered_entries = filter_by_publish_state(
            filtered_entries,
            filters["publish_states"]
        )
    
    if filters["tag_filter_enabled"]:
        all_tags = extract_tags_from_entries(entries)
        if all_tags:
            selected_tags = st.sidebar.multiselect(
                "Select tags to filter",
                options=all_tags,
                default=[]
            )
            if selected_tags:
                filtered_entries = filter_by_tags(filtered_entries, selected_tags)
    
    ct_map = {ct["uid"]: ct["title"] for ct in filters["content_types"]}
    
    stats = calculate_freshness_stats(filtered_entries)
    
    st.markdown("### 📈 Summary Overview")
    render_metrics(stats)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🥧 Freshness Distribution")
        if stats["total"] > 0:
            pie_fig = render_pie_chart(stats)
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No data to display")
    
    with col2:
        st.markdown("### 📊 By Content Type")
        df_by_ct = calculate_freshness_by_content_type(filtered_entries, ct_map)
        if not df_by_ct.empty:
            bar_fig = render_bar_chart(df_by_ct)
            if bar_fig:
                st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("No data to display")
    
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
