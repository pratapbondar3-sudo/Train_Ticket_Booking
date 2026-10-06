import os
import random
import sqlite3
import string
import pandas as pd
import streamlit as st

DB_FILE = "railway.db"

# ----------------- DATABASE HELPERS ----------------- #
def get_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes tables and ensures default routes exist if starting fresh."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trains (
                train_no INTEGER PRIMARY KEY,
                train_name TEXT NOT NULL,
                source TEXT NOT NULL,
                destination TEXT NOT NULL,
                total_seats INTEGER NOT NULL,
                available_seats INTEGER NOT NULL,
                fare REAL NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookings (
                pnr TEXT PRIMARY KEY,
                passenger_name TEXT NOT NULL,
                passenger_age INTEGER NOT NULL,
                train_no INTEGER NOT NULL,
                seat_no INTEGER NOT NULL,
                fare_paid REAL NOT NULL,
                FOREIGN KEY (train_no) REFERENCES trains (train_no)
            )
        """)
        # Seed routes if empty
        cursor.execute("SELECT COUNT(*) FROM trains")
        if cursor.fetchone()[0] == 0:
            sample_trains = [
                (12124, "Deccan Queen", "Pune", "Mumbai", 75, 75, 390.0),
                (12127, "Mumbai Intercity", "Mumbai", "Pune", 75, 75, 390.0),
                (12110, "Panchavati Express", "Nashik", "Mumbai", 60, 60, 240.0),
                (11011, "Mahalaxmi Express", "Mumbai", "Nashik", 60, 60, 240.0),
                (22107, "CSMT Latur Express", "Mumbai", "Latur", 50, 50, 480.0),
                (11406, "Pune Latur Express", "Pune", "Latur", 50, 50, 360.0),
                (11301, "Udyan Express", "Mumbai", "Bangalore", 80, 80, 1450.0),
                (11005, "Chalukya Express", "Pune", "Bangalore", 80, 80, 1100.0),
                (16536, "Gol Gumbaz Express", "Bangalore", "Pune", 80, 80, 1100.0),
                (17317, "Nashik Bangalore Exp", "Nashik", "Bangalore", 70, 70, 1580.0),
                (12001, "Shatabdi Express", "Delhi", "Bhopal", 50, 50, 1250.0),
                (12951, "Rajdhani Express", "Mumbai", "Delhi", 60, 60, 2100.0),
                (12626, "Kerala Express", "Delhi", "Trivandrum", 80, 80, 1800.0),
            ]
            cursor.executemany("INSERT OR IGNORE INTO trains VALUES (?, ?, ?, ?, ?, ?, ?)", sample_trains)
            conn.commit()

# ----------------- UI CONFIG & STYLING ----------------- #
st.set_page_config(page_title="RailYatra - Indian Railways Portal", page_icon="🚆", layout="wide")

st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
        border-radius: 12px;
        padding: 18px 24px;
        color: white;
        margin-bottom: 20px;
    }
    .ticket-container {
        border: 2px dashed #2a5298;
        border-radius: 12px;
        background-color: #f8fafc;
        padding: 24px;
        color: #1e293b;
        margin-top: 15px;
    }
</style>
""", unsafe_allow_html=True)

init_db()

# ----------------- SIDEBAR & METRICS ----------------- #
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1474487548417-781cb71495f3?w=500&auto=format&fit=crop&q=60", use_container_width=True)
    st.title("🚆 RailYatra Portal")
    st.caption("Connecting Pune, Mumbai, Nashik, Latur, Bangalore & beyond.")
    st.divider()

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM trains")
        t_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM bookings")
        b_count = cursor.fetchone()[0]

    st.metric("Active Routes", t_count)
    st.metric("Confirmed Passengers", b_count)
    st.divider()
    st.caption("Secure SQLite DB Connection Active.")

# ----------------- HEADER ----------------- #
st.markdown("""
<div class="metric-card">
    <h2 style='margin:0; color: white;'>🇮🇳 Indian Railway Ticket Booking & PNR Portal</h2>
    <p style='margin:4px 0 0 0; opacity: 0.9;'>Book tickets instantly, check real-time seat availability, and manage reservations.</p>
</div>
""", unsafe_allow_html=True)

tab_search, tab_pnr, tab_all, tab_cancel = st.tabs([
    "🎟️ Search & Book",
    "🔍 PNR Status",
    "📋 All Running Trains",
    "❌ Cancel Reservation"
])

# ----------------- TAB 1: SEARCH & BOOK ----------------- #
with tab_search:
    st.subheader("Plan Your Journey")

    with get_db() as conn:
        df_trains = pd.read_sql_query("SELECT * FROM trains", conn)

    sources = sorted(df_trains["source"].unique())
    destinations = sorted(df_trains["destination"].unique())

    col_src, col_dst = st.columns(2)
    with col_src:
        src = st.selectbox("Origin Station:", sources, index=sources.index("Pune") if "Pune" in sources else 0)
    with col_dst:
        dst = st.selectbox("Destination Station:", destinations, index=destinations.index("Mumbai") if "Mumbai" in destinations else 0)

    # Filter matching trains
    matching_trains = df_trains[(df_trains["source"] == src) & (df_trains["destination"] == dst)]

    if matching_trains.empty:
        st.warning(f"No direct trains found connecting {src} to {dst}. Check alternative transit routes.")
    else:
        st.write(f"### Available Trains ({len(matching_trains)})")
        for _, t in matching_trains.iterrows():
            with st.container(border=True):
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                c1.markdown(f"**{t['train_name']}** (`#{t['train_no']}`)")
                c2.markdown(f"📍 {t['source']} ➜ {t['destination']}")
                c3.markdown(f"💺 **{t['available_seats']}** / {t['total_seats']} seats left")
                c4.markdown(f"💰 **₹{t['fare']:.2f}**")

        st.divider()
        st.subheader("Passenger Information")
        with st.form("booking_form", clear_on_submit=True):
            train_choice = st.selectbox(
                "Select Train to Book:",
                matching_trains["train_no"].tolist(),
                format_func=lambda x: f"{df_trains[df_trains['train_no']==x]['train_name'].values[0]} (#{x})"
            )
            col_name, col_age = st.columns(2)
            with col_name:
                p_name = st.text_input("Full Name", placeholder="e.g., Rajesh Sharma")
            with col_age:
                p_age = st.number_input("Age", min_value=1, max_value=115, value=28)

            submitted = st.form_submit_button("Confirm & Reserve Seat", type="primary", use_container_width=True)

            if submitted:
                if not p_name.strip():
                    st.error("Please provide passenger name.")
                else:
                    with get_db() as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT available_seats, total_seats, fare FROM trains WHERE train_no = ?", (train_choice,))
                        train_row = cursor.fetchone()

                        if train_row["available_seats"] <= 0:
                            st.error("Booking failed: No seats available on this train.")
                        else:
                            seat_no = (train_row["total_seats"] - train_row["available_seats"]) + 1
                            pnr = "PNR" + "".join(random.choices(string.digits, k=6))

                            cursor.execute("UPDATE trains SET available_seats = available_seats - 1 WHERE train_no = ?", (train_choice,))
                            cursor.execute(
                                "INSERT INTO bookings VALUES (?, ?, ?, ?, ?, ?)",
                                (pnr, p_name.strip(), int(p_age), int(train_choice), seat_no, train_row["fare"])
                            )
                            conn.commit()

                            st.success("🎉 Booking Confirmed!")
                            st.balloons()
                            st.markdown(f"""
                            <div class="ticket-container">
                                <h3 style="margin-top:0; color:#1e3c72;">BOARDING PASS - INDIAN RAILWAYS</h3>
                                <p><strong>PNR:</strong> <span style="font-size:18px; color:#e11d48; font-weight:bold;">{pnr}</span></p>
                                <p><strong>Passenger:</strong> {p_name.strip()} ({p_age} yrs)</p>
                                <p><strong>Train:</strong> {df_trains[df_trains['train_no']==train_choice]['train_name'].values[0]} (#{train_choice})</p>
                                <p><strong>Route:</strong> {src} ➜ {dst}</p>
                                <p><strong>Seat Number:</strong> Coach S1 - Seat #{seat_no}</p>
                                <p><strong>Fare Paid:</strong> ₹{train_row['fare']:.2f}</p>
                            </div>
                            """, unsafe_allow_html=True)

# ----------------- TAB 2: PNR STATUS ----------------- #
with tab_pnr:
    st.subheader("Verify Ticket Status")
    query_pnr = st.text_input("Enter 9-Character PNR:", placeholder="e.g., PNR123456").strip().upper()
    if st.button("Check Status", type="primary"):
        with get_db() as conn:
            cursor = conn.cursor()
            query = """
                SELECT b.pnr, b.passenger_name, b.passenger_age, t.train_name, b.train_no, b.seat_no, b.fare_paid, t.source, t.destination
                FROM bookings b
                JOIN trains t ON b.train_no = t.train_no
                WHERE UPPER(b.pnr) = ?
            """
            cursor.execute(query, (query_pnr,))
            res = cursor.fetchone()

        if res:
            st.success("Ticket Confirmed & Active")
            st.markdown(f"""
            <div class="ticket-container">
                <h4 style="margin:0; color:#1e3c72;">PNR: {res['pnr']}</h4>
                <hr/>
                <p><strong>Passenger:</strong> {res['passenger_name']} | <strong>Age:</strong> {res['passenger_age']}</p>
                <p><strong>Train:</strong> {res['train_name']} (#{res['train_no']})</p>
                <p><strong>Journey:</strong> {res['source']} ➜ {res['destination']}</p>
                <p><strong>Assigned Seat:</strong> #{res['seat_no']}</p>
                <p><strong>Total Fare:</strong> ₹{res['fare_paid']:.2f}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.error("No booking record found for this PNR.")

# ----------------- TAB 3: ALL RUNNING TRAINS ----------------- #
with tab_all:
    st.subheader("System Train Schedule & Seat Matrices")
    with get_db() as conn:
        df_all = pd.read_sql_query("SELECT train_no AS 'Train No', train_name AS 'Train Name', source AS 'Origin', destination AS 'Destination', available_seats AS 'Available Seats', total_seats AS 'Capacity', fare AS 'Fare (₹)' FROM trains", conn)
    st.dataframe(df_all, use_container_width=True, hide_index=True)

# ----------------- TAB 4: CANCELLATION ----------------- #
with tab_cancel:
    st.subheader("Ticket Cancellation & Refund")
    cancel_pnr = st.text_input("Enter PNR to Cancel:", placeholder="e.g., PNR123456").strip().upper()
    if st.button("Cancel Ticket", type="secondary"):
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT train_no FROM bookings WHERE UPPER(pnr) = ?", (cancel_pnr,))
            booking = cursor.fetchone()

            if not booking:
                st.error("Invalid PNR. No matching active booking found.")
            else:
                train_no = booking["train_no"]
                cursor.execute("DELETE FROM bookings WHERE UPPER(pnr) = ?", (cancel_pnr,))
                cursor.execute("UPDATE trains SET available_seats = available_seats + 1 WHERE train_no = ?", (train_no,))
                conn.commit()
                st.success(f"Ticket with PNR **{cancel_pnr}** was successfully cancelled. One seat has been restored to Train #{train_no}.")
