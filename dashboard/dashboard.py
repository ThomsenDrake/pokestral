import streamlit as st
import sqlite3
import json
import psutil
import time
from datetime import datetime
from typing import Dict, Any, List

# Database connection
def get_db_connection():
    return sqlite3.connect('database/pokemon_blue.db')

# Helper functions
def get_latest_run() -> Dict[str, Any]:
    """Get the most recent run data."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM runs ORDER BY id DESC LIMIT 1')
        row = cursor.fetchone()
        return dict(zip([column[0] for column in cursor.description], row)) if row else None

def get_party_data(run_id: int) -> List[Dict[str, Any]]:
    """Get party data for a specific run."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE run_id = ? AND event_type = "party_update"', (run_id,))
        rows = cursor.fetchall()
        return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

def get_action_timeline(run_id: int) -> List[Dict[str, Any]]:
    """Get action timeline for a specific run."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM events WHERE run_id = ? ORDER BY timestamp', (run_id,))
        rows = cursor.fetchall()
        return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

def get_goals(run_id: int) -> List[Dict[str, Any]]:
    """Get goals for a specific run."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM summaries WHERE run_id = ?', (run_id,))
        rows = cursor.fetchall()
        return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]

def get_system_metrics() -> Dict[str, float]:
    """Get system metrics (CPU, memory)."""
    cpu_usage = psutil.cpu_percent(interval=1)
    memory_info = psutil.virtual_memory()
    return {
        'cpu_usage': cpu_usage,
        'memory_usage': memory_info.percent,
        'memory_total': memory_info.total,
        'memory_available': memory_info.available
    }

# Streamlit app
def main():
    st.title("Pokémon Blue AI Agent Dashboard")

    # Sidebar for navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Overview", "Party Data", "Action Timeline", "Goals", "System Metrics"])

    # Get latest run data
    latest_run = get_latest_run()

    if page == "Overview":
        st.header("Overview")
        if latest_run:
            st.subheader("Current Run Status")
            st.write(f"Run ID: {latest_run['id']}")
            st.write(f"Start Time: {latest_run['start_time']}")
            st.write(f"Status: {latest_run['status']}")
            st.write(f"Performance Metrics: {latest_run.get('performance_metrics', 'N/A')}")

            # Display errors if any
            with get_db_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM errors WHERE run_id = ?', (latest_run['id'],))
                errors = cursor.fetchall()
                if errors:
                    st.subheader("Recent Errors")
                    for error in errors:
                        st.error(f"{error[3]}: {error[4]}")
        else:
            st.write("No runs found in the database.")

    elif page == "Party Data":
        st.header("Party Data")
        if latest_run:
            party_data = get_party_data(latest_run['id'])
            if party_data:
                st.write("Party Members:")
                for member in party_data:
                    details = json.loads(member['details'])
                    st.write(f"- {details.get('name', 'Unknown')} (Lvl {details.get('level', '?')})")
            else:
                st.write("No party data available for this run.")
        else:
            st.write("No runs found in the database.")

    elif page == "Action Timeline":
        st.header("Action Timeline")
        if latest_run:
            timeline = get_action_timeline(latest_run['id'])
            if timeline:
                st.write("Recent Actions:")
                for event in timeline:
                    st.write(f"- {event['timestamp']}: {event['event_type']} - {event.get('details', '')}")
            else:
                st.write("No actions recorded for this run.")
        else:
            st.write("No runs found in the database.")

    elif page == "Goals":
        st.header("Goals and Performance")
        if latest_run:
            goals = get_goals(latest_run['id'])
            if goals:
                st.write("Current Goals:")
                for goal in goals:
                    st.write(f"- {goal['timestamp']}: {goal['summary_text']}")
            else:
                st.write("No goals set for this run.")
        else:
            st.write("No runs found in the database.")

    elif page == "System Metrics":
        st.header("System Metrics")
        metrics = get_system_metrics()
        st.write(f"CPU Usage: {metrics['cpu_usage']}%")
        st.write(f"Memory Usage: {metrics['memory_usage']}%")
        st.write(f"Total Memory: {metrics['memory_total'] / (1024 ** 3):.2f} GB")
        st.write(f"Available Memory: {metrics['memory_available'] / (1024 ** 3):.2f} GB")

        # API Latency (mocked for now)
        st.subheader("API Latency")
        st.write("Last API Call: 120ms (mocked)")

if __name__ == "__main__":
    main()