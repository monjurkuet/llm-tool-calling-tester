import streamlit as st
import pandas as pd
import psycopg2
import psycopg2.extras
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
import json

# Database configuration
DB_CONFIG = {
    "host": "localhost",
    "port": 5432,
    "database": "autonomous_planner",
    "user": "agentzero",
    "password": "",
}

# Page configuration
st.set_page_config(
    page_title="Session Analysis Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for better styling
st.markdown(
    """
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 0.25rem solid #1f77b4;
    }
    .sidebar .sidebar-content {
        background-color: #ffffff;
    }
</style>
""",
    unsafe_allow_html=True,
)


import psycopg2.pool


# Database connection pool
@st.cache_resource
def get_connection_pool():
    """Create connection pool for database access"""
    try:
        pool = psycopg2.pool.SimpleConnectionPool(minconn=1, maxconn=5, **DB_CONFIG)
        return pool
    except Exception as e:
        st.error(f"Connection pool creation failed: {e}")
        return None


def get_db_connection():
    """Get connection from pool"""
    pool = get_connection_pool()
    if not pool:
        return None
    try:
        conn = pool.getconn()
        return conn
    except Exception as e:
        st.error(f"Failed to get connection from pool: {e}")
        return None


def return_connection(conn):
    """Return connection to pool"""
    if conn:
        pool = get_connection_pool()
        if pool:
            try:
                pool.putconn(conn)
            except Exception:
                pass  # Pool might be closed


@st.cache_data(ttl=300)
def load_sessions_data():
    """Load all session metadata"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        query = """
        SELECT session_id, title, created_at, updated_at, projectid, directory,
               files, additions, deletions
        FROM raw_session_metadata
        ORDER BY created_at DESC
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error loading sessions data: {e}")
        return pd.DataFrame()
    finally:
        return_connection(conn)


@st.cache_data(ttl=300)
def load_analysis_data():
    """Load all analysis results"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        query = """
        SELECT session_id, analysis_type, metric_name, metric_value
        FROM session_analysis_results
        """
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Error loading analysis data: {e}")
        return pd.DataFrame()
    finally:
        return_connection(conn)


@st.cache_data(ttl=300)
def get_summary_stats():
    """Get summary statistics for dashboard"""
    conn = get_db_connection()
    if not conn:
        return {}

    try:
        stats = {}

        # Total sessions
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM raw_session_metadata")
            stats["total_sessions"] = cursor.fetchone()[0]

        # Total analysis records
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM session_analysis_results")
            stats["total_analysis"] = cursor.fetchone()[0]

        # Last updated
        with conn.cursor() as cursor:
            cursor.execute("SELECT MAX(last_updated) FROM ingestion_state")
            last_update = cursor.fetchone()[0]
            stats["last_updated"] = last_update if last_update else None

        # Sessions by project
        with conn.cursor() as cursor:
            cursor.execute("""
            SELECT projectid, COUNT(*) as count
            FROM raw_session_metadata
            WHERE projectid IS NOT NULL
            GROUP BY projectid
            ORDER BY count DESC
            LIMIT 10
            """)
            stats["top_projects"] = cursor.fetchall()

        return stats
    except Exception as e:
        st.error(f"Error getting summary stats: {e}")
        return {}
    finally:
        return_connection(conn)


@st.cache_data(ttl=300)
def load_analysis_data():
    """Load all analysis results"""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()

    try:
        query = """
        SELECT session_id, analysis_type, metric_name, metric_value
        FROM session_analysis_results
        """
        df = pd.read_sql_query(query, conn)
        # Convert JSONB values to Python objects
        df["metric_value"] = df["metric_value"].apply(
            lambda x: json.loads(x) if isinstance(x, str) else x
        )
        return df
    except Exception as e:
        st.error(f"Error loading analysis data: {e}")
        return pd.DataFrame()
    finally:
        conn.close()


@st.cache_data(ttl=300)
def get_summary_stats():
    """Get summary statistics for dashboard"""
    conn = get_db_connection()
    if not conn:
        return {}

    try:
        stats = {}

        # Total sessions
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM raw_session_metadata")
        stats["total_sessions"] = cursor.fetchone()[0]

        # Total analysis records
        cursor.execute("SELECT COUNT(*) FROM session_analysis_results")
        stats["total_analysis"] = cursor.fetchone()[0]

        # Last updated
        cursor.execute("SELECT MAX(last_updated) FROM ingestion_state")
        last_update = cursor.fetchone()[0]
        stats["last_updated"] = last_update if last_update else None

        # Sessions by project
        cursor.execute("""
        SELECT projectid, COUNT(*) as count
        FROM raw_session_metadata
        WHERE projectid IS NOT NULL
        GROUP BY projectid
        ORDER BY count DESC
        LIMIT 10
        """)
        stats["top_projects"] = cursor.fetchall()

        cursor.close()
        return stats
    except Exception as e:
        st.error(f"Error getting summary stats: {e}")
        return {}
    finally:
        conn.close()


def show_session_details():
    st.header("🔍 Session Details")

    # Load sessions for selection
    sessions_df = load_sessions_data()

    if sessions_df.empty:
        st.error("No session data available")
        return

    # Session selector
    session_options = sessions_df.apply(
        lambda row: f"{row['session_id'][:8]}... - {row['title'][:50]}{'...' if len(row['title']) > 50 else ''}",
        axis=1,
    ).tolist()

    selected_session = st.selectbox(
        "Select a session to view details:",
        options=session_options,
        index=0 if len(session_options) > 0 else None,
        key="session_selector",
    )

    if selected_session:
        # Extract session_id from selection
        selected_id = selected_session.split(" - ")[0].replace("...", "")
        # Find the full session_id
        session_row = sessions_df[sessions_df["session_id"].str.startswith(selected_id)].iloc[0]
        session_id = session_row["session_id"]

        # Display session metadata
        st.subheader("📋 Session Metadata")
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f"**Session ID:** `{session_id}`")
            st.markdown(f"**Title:** {session_row['title']}")
            st.markdown(f"**Project:** {session_row.get('projectid', 'N/A')}")
            st.markdown(
                f"**Created:** {session_row['created_at'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(session_row['created_at']) else 'N/A'}"
            )

        with col2:
            st.markdown(
                f"**Updated:** {session_row['updated_at'].strftime('%Y-%m-%d %H:%M:%S') if pd.notna(session_row['updated_at']) else 'N/A'}"
            )
            st.markdown(f"**Files Changed:** {session_row.get('files', 'N/A')}")
            st.markdown(f"**Lines Added:** {session_row.get('additions', 'N/A')}")
            st.markdown(f"**Lines Deleted:** {session_row.get('deletions', 'N/A')}")

        # Load analysis data for this session
        analysis_df = load_analysis_data()
        session_analysis = analysis_df[analysis_df["session_id"] == session_id]

        if not session_analysis.empty:
            st.subheader("📊 Analysis Metrics")

            # Group by analysis type
            analysis_types = session_analysis["analysis_type"].unique()

            for analysis_type in analysis_types:
                type_data = session_analysis[session_analysis["analysis_type"] == analysis_type]

                st.markdown(f"**{analysis_type.replace('_', ' ').title()}**")

                # Create metrics display
                metrics = []
                for _, row in type_data.iterrows():
                    metric_name = row["metric_name"]
                    try:
                        metric_value = json.loads(row["metric_value"])
                    except:
                        metric_value = row["metric_value"]

                    metrics.append(f"- **{metric_name.replace('_', ' ').title()}:** {metric_value}")

                st.markdown("\n".join(metrics))

                # Simple bar chart for numeric metrics
                numeric_metrics = type_data[type_data["metric_value"].str.match(r"^\d+(\.\d+)?$")]
                if not numeric_metrics.empty:
                    chart_data = numeric_metrics.copy()
                    chart_data["metric_value"] = pd.to_numeric(
                        chart_data["metric_value"], errors="coerce"
                    )
                    chart_data = chart_data.dropna()

                    if not chart_data.empty:
                        fig = px.bar(
                            chart_data,
                            x="metric_name",
                            y="metric_value",
                            title=f"{analysis_type.replace('_', ' ').title()} Metrics",
                        )
                        st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No analysis data available for this session")


def show_overview():
    st.header("📈 Overview")

    # Load summary stats
    stats = get_summary_stats()

    if not stats:
        st.error("Unable to load dashboard data. Please check database connection.")
        return

    # Metrics cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Total Sessions</h3>
            <h2>{:,}</h2>
        </div>
        """.format(stats.get("total_sessions", 0)),
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            """
        <div class="metric-card">
            <h3>Analysis Records</h3>
            <h2>{:,}</h2>
        </div>
        """.format(stats.get("total_analysis", 0)),
            unsafe_allow_html=True,
        )

    with col3:
        last_update = stats.get("last_updated")
        update_str = last_update.strftime("%Y-%m-%d %H:%M") if last_update else "Never"
        st.markdown(
            """
        <div class="metric-card">
            <h3>Last Updated</h3>
            <h4>{}</h4>
        </div>
        """.format(update_str),
            unsafe_allow_html=True,
        )

    # Top projects chart
    st.subheader("🏗️ Top Projects by Session Count")
    top_projects = stats.get("top_projects", [])
    if top_projects:
        projects_df = pd.DataFrame(top_projects, columns=["Project", "Sessions"])
        fig = px.bar(
            projects_df,
            x="Project",
            y="Sessions",
            title="Sessions per Project",
            color="Sessions",
            color_continuous_scale="Blues",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No project data available")


def show_sessions_browser():
    st.header("🔍 Sessions Browser")

    # Load data
    df = load_sessions_data()

    if df.empty:
        st.error("No session data available")
        return

    # Filters
    col1, col2 = st.columns(2)

    with col1:
        date_range = st.date_input(
            "Date Range",
            value=(df["created_at"].min().date(), df["created_at"].max().date()),
            key="date_filter",
        )

    with col2:
        search_term = st.text_input("Search titles", "", key="search_filter")

    # Apply filters
    filtered_df = df.copy()
    if len(date_range) == 2:
        filtered_df = filtered_df[
            (filtered_df["created_at"].dt.date >= date_range[0])
            & (filtered_df["created_at"].dt.date <= date_range[1])
        ]

    if search_term:
        filtered_df = filtered_df[
            filtered_df["title"].str.contains(search_term, case=False, na=False)
        ]

    # Display table
    st.dataframe(
        filtered_df[
            ["session_id", "title", "created_at", "projectid", "files", "additions", "deletions"]
        ],
        use_container_width=True,
        column_config={
            "session_id": st.column_config.TextColumn("Session ID", width="small"),
            "title": st.column_config.TextColumn("Title", width="large"),
            "created_at": st.column_config.DatetimeColumn("Created", format="YYYY-MM-DD HH:mm"),
            "projectid": st.column_config.TextColumn("Project", width="medium"),
            "files": st.column_config.NumberColumn("Files", format="%d"),
            "additions": st.column_config.NumberColumn("Additions", format="%d"),
            "deletions": st.column_config.NumberColumn("Deletions", format="%d"),
        },
    )

    st.caption(f"Showing {len(filtered_df)} of {len(df)} sessions")

    # Export button
    if not filtered_df.empty:
        csv = filtered_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Filtered Data as CSV",
            data=csv,
            file_name="filtered_sessions.csv",
            mime="text/csv",
            key="download_csv",
        )


def show_analytics():
    st.header("📊 Analytics")

    # Load data
    sessions_df = load_sessions_data()
    analysis_df = load_analysis_data()

    if sessions_df.empty or analysis_df.empty:
        st.error("No data available for analytics")
        return

    # Basic metrics over time
    st.subheader("📅 Sessions Over Time")

    # Group by date
    sessions_df["date"] = sessions_df["created_at"].dt.date
    daily_sessions = sessions_df.groupby("date").size().reset_index(name="count")

    fig = px.line(daily_sessions, x="date", y="count", title="Daily Session Count", markers=True)
    st.plotly_chart(fig, use_container_width=True)

    # Activity metrics distribution
    st.subheader("📈 Activity Metrics Distribution")

    col1, col2, col3 = st.columns(3)

    with col1:
        fig = px.histogram(sessions_df, x="files", title="Files Changed Distribution", nbins=20)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        fig = px.histogram(sessions_df, x="additions", title="Lines Added Distribution", nbins=20)
        st.plotly_chart(fig, use_container_width=True)

    with col3:
        fig = px.histogram(sessions_df, x="deletions", title="Lines Deleted Distribution", nbins=20)
        st.plotly_chart(fig, use_container_width=True)


def main():
    st.markdown(
        '<h1 class="main-header">📊 Session Analysis Dashboard</h1>', unsafe_allow_html=True
    )

    # Sidebar
    st.sidebar.title("Navigation")
    page = st.sidebar.radio(
        "Go to", ["Overview", "Sessions Browser", "Session Details", "Analytics"]
    )

    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

    # Last updated info
    st.sidebar.caption(f"Data last cached: {datetime.now().strftime('%H:%M:%S')}")

    if page == "Overview":
        show_overview()
    elif page == "Sessions Browser":
        show_sessions_browser()
    elif page == "Session Details":
        show_session_details()
    elif page == "Analytics":
        show_analytics()


if __name__ == "__main__":
    main()
