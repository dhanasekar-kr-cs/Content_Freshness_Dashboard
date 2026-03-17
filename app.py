"""
Content Freshness Dashboard
A Streamlit app to visualize content freshness across a Contentstack stack.
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

FRESHNESS_COLORS = {
    "Fresh": "#28a745",
    "Aging": "#ffc107",
    "Stale": "#dc3545",
    "Unknown": "#6c757d"
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
    st.sidebar.header("Filters")
    
    with st.sidebar.expander("Time Period", expanded=True):
        time_options = [
            "Last 7 days",
            "Last 30 days",
            "Last 90 days",
            "Last 180 days",
            "Last 1 year",
            "All time",
            "Custom"
        ]
        selected_period = st.selectbox(
            "Select time period",
            options=time_options,
            index=0
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
    
    with st.sidebar.expander("Content Type", expanded=True):
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
    
    with st.sidebar.expander("Environment", expanded=False):
        environments = load_environments()
        env_options = [env["name"] for env in environments]
        selected_environments = st.multiselect(
            "Select environments",
            options=env_options,
            default=[]
        )
    
    with st.sidebar.expander("Locale", expanded=False):
        locales = load_locales()
        locale_options = {f"{loc['name']} ({loc['code']})": loc["code"] for loc in locales}
        selected_locale_labels = st.multiselect(
            "Select locales",
            options=list(locale_options.keys()),
            default=[]
        )
        selected_locales = [locale_options[label] for label in selected_locale_labels]
    
    with st.sidebar.expander("Publish State", expanded=False):
        publish_states = st.multiselect(
            "Select publish states",
            options=["Published", "Draft", "Unpublished"],
            default=[]
        )
    
    with st.sidebar.expander("Tags", expanded=False):
        st.info("Tags will be populated after loading entries")
        tag_filter_enabled = st.checkbox("Enable tag filter", value=False)
    
    with st.sidebar.expander("Taxonomies", expanded=False):
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
    """Render summary metrics."""
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total Entries",
            value=stats["total"]
        )
    
    with col2:
        st.metric(
            label="Fresh",
            value=f"{stats['fresh']} ({stats['fresh_pct']}%)",
            delta=None
        )
    
    with col3:
        st.metric(
            label="Aging",
            value=f"{stats['aging']} ({stats['aging_pct']}%)",
            delta=None
        )
    
    with col4:
        st.metric(
            label="Stale",
            value=f"{stats['stale']} ({stats['stale_pct']}%)",
            delta=None
        )


def render_pie_chart(stats: dict):
    """Render freshness distribution pie chart."""
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
        hole=0.4,
        marker_colors=colors,
        textinfo="label+percent",
        textposition="outside"
    )])
    
    fig.update_layout(
        title="Content Freshness Distribution",
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        height=400
    )
    
    return fig


def render_bar_chart(df_by_ct: pd.DataFrame):
    """Render stacked bar chart by content type."""
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
        title="Entries by Content Type and Freshness",
        barmode="stack"
    )
    
    fig.update_layout(
        xaxis_tickangle=-45,
        height=400,
        legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5)
    )
    
    return fig


def render_data_table(df: pd.DataFrame):
    """Render sortable data table."""
    if df.empty:
        st.info("No entries to display")
        return
    
    def highlight_freshness(val):
        color_map = {
            "Fresh": "background-color: #d4edda",
            "Aging": "background-color: #fff3cd",
            "Stale": "background-color: #f8d7da",
            "Unknown": "background-color: #e2e3e5"
        }
        return color_map.get(val, "")
    
    styled_df = df.style.applymap(
        highlight_freshness,
        subset=["Freshness"]
    )
    
    st.dataframe(
        styled_df,
        use_container_width=True,
        height=400
    )


def main():
    st.title("Content Freshness Dashboard")
    st.markdown("Monitor content freshness across your Contentstack stack")
    
    filters = render_sidebar()
    
    if not filters["content_type_uids"]:
        st.warning("Please select at least one content type from the sidebar")
        return
    
    with st.spinner("Loading entries..."):
        locale = filters["locales"][0] if filters["locales"] else None
        entries = load_entries_for_content_types(
            tuple(filters["content_type_uids"]),
            locale=locale
        )
    
    if not entries:
        st.warning("No entries found for the selected content types")
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
    
    st.markdown("---")
    st.subheader("Summary")
    render_metrics(stats)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Freshness Distribution")
        if stats["total"] > 0:
            pie_fig = render_pie_chart(stats)
            st.plotly_chart(pie_fig, use_container_width=True)
        else:
            st.info("No data to display")
    
    with col2:
        st.subheader("By Content Type")
        df_by_ct = calculate_freshness_by_content_type(filtered_entries, ct_map)
        if not df_by_ct.empty:
            bar_fig = render_bar_chart(df_by_ct)
            if bar_fig:
                st.plotly_chart(bar_fig, use_container_width=True)
        else:
            st.info("No data to display")
    
    st.markdown("---")
    st.subheader("Entry Details")
    
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
            label="Download as CSV",
            data=df.to_csv(index=False),
            file_name=f"content_freshness_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
