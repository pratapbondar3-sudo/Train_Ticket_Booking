import datetime
import os
import pickle
import random
import string
import pandas as pd
import streamlit as st

DATA_FILE = "railway_data.pkl"

# ----------------- DATA LAYER (PICKLE) ----------------- #
def load_store():
    if not os.path.exists(DATA_FILE):
        st.error(f"Missing {DATA_FILE}. Run generate_pickle.py first.")
        st.stop()
    with open(DATA_FILE, "rb") as f:
        return pickle.load(f)

def save_store(data):
    with open(DATA_FILE, "wb") as f:
        pickle.dump(data, f)

data_store = load_store()

# ----------------- UI CONFIG & STYLES ----------------- #
st.set_page_config(page_title="Where Is My Train + Booking", page_icon="🚆", layout="wide")

st.markdown("""
<style>
    .header-banner {
        background: linear-gradient(90deg, #0d5c3a 0%, #15803d 100%);
        padding: 18px 24px;
        border-radius: 12px;
        color: white;
        margin-bottom: 20px;
    }
    .halt-card {
        padding: 12px 18px;
        border-left: 5px solid #16a34a;
        background-color: #f0fdf4;
        margin-bottom: 8px;
        border-radius: 4px;
    }
    .current-halt {
        padding: 12px 18px;
        border-left: 6px solid #e11d48;
        background-color: #fff1f2;
        margin-bottom: 8px;
        border-radius: 4px;
        font-weight: bold;
    }
    .upcoming-halt {
        padding: 12px 18px;
        border-left: 5px solid #94a3b8;
        background-color: #f8fafc;
        margin-bottom: 8px;
        border-radius: 4px;
        opacity: 0.8;
    }
    .badge {
        display: inline-block;
        padding: 3px 8px;
        font-size: 12px;
        font-weight: bold;
        border-radius: 6px;
        color: white;
    }
    .badge-on-time { background-color: #16a34a; }
    .badge-delayed { background-color: #dc2626; }
    .badge-platform { background-color: #0284c7; }
</style>
""", unsafe_allow_html=True)

# ----------------- HEADER ----------------- #
st.markdown("""
<div class="header-banner">
    <h2 style='margin:0;'>🚆 Where Is My Train & Ticket Booking</h2>
    <p style='margin:3px 0 0 0; opacity:0.9;'>Live Station GPS Tracking, Intermediate Halts, Delay Predictor & Instant Booking</p>
</div>
""", unsafe_allow_html=True)

tab_live, tab_book, tab_pnr = st.tabs([
    "📍 Live Train Status", 
    "🎟️ Search & Book Tickets", 
    "🔍 PNR Status & Cancel"
])

trains = data_store["trains"]

# ----------------- TAB 1: LIVE TRAIN STATUS (WHERE IS MY TRAIN) ----------------- #
with tab_live:
    col_t, col_day = st.columns([3, 1])
    with col_t:
        train_options = {f"{num} - {info['name']} ({info['source']} ➜ {info['destination']})": num for num, info in trains.items()}
        selected_label = st.selectbox("Select Train to Track:", list(train_options.keys()))
        selected_t_no = train_options[selected_label]
        train_obj = trains[selected_t_no]
    with col_day:
        travel_day = st.selectbox("Journey Date:", ["Today", "Yesterday", "Tomorrow"])

    schedule = train_obj["schedule"]
    num_stops = len(schedule)

    # Simulated realistic live progress slider
    st.subheader(f"Live Location: {train_obj['name']} ({selected_t_no})")
    simulated_stop_idx = st.slider(
        "Simulation GPS Controller (Move train along its route):",
        min_value=0,
        max_value=num_stops - 1,
        value=min(2, num_stops - 1),
        format=f"Stop %d"
    )

    current_station = schedule[simulated_stop_idx]
    delay_minutes = random.choice([0, 0, 5, 12, 25])  # realistic simulation

    # Live Status Alert Banner
    col_status1, col_status2, col_status3 = st.columns(3)
    with col_status1:
        if delay_minutes == 0:
            st.success("🟢 Running On-Time")
        else:
            st.error(f"🔴 Delayed by {delay_minutes} mins")
    with col_status2:
        st.info(f"📍 Current Position: **{current_station['station']}**")
    with col_status3:
        st.markdown(f"<span class='badge badge-platform'>Platform #{current_station['platform']}</span>", unsafe_allow_html=True)

    st.write("---")
    st.write("### Route Timeline & Halts")

    for i, stop in enumerate(schedule):
        dist_info = f"{stop['dist']} km"
        timings = f"Arr: {stop['sch_arr']} | Dep: {stop['sch_dep']}"
        platform_text = f"PF #{stop['platform']}"

        if i < simulated_stop_idx:
            # Departed Stop
            st.markdown(f"""
            <div class="halt-card">
                <span class="badge badge-on-time">DEPARTED</span> <strong>{stop['station']}</strong> 
                <span style="float: right;">{timings} | {dist_info} | <span class="badge badge-platform">{platform_text}</span></span>
            </div>
            """, unsafe_allow_html=True)
        elif i == simulated_stop_idx:
            # Current Stop
            badge_class = "badge-on-time" if delay_minutes == 0 else "badge-delayed"
            status_text = "CURRENT STATION (ON TIME)" if delay_minutes == 0 else f"CURRENT STATION (+{delay_minutes} MINS LATE)"
            st.markdown(f"""
            <div class="current-halt">
                <span class="badge {badge_class}">{status_text}</span> 🚆 <strong>{stop['station']}</strong> 
                <span style="float: right;">{timings} | {dist_info} | <span class="badge badge-platform">{platform_text}</span></span>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Upcoming Stop
            st.markdown(f"""
            <div class="upcoming-halt">
                ⚪ <strong>{stop['station']}</strong> 
                <span style="float: right;">{timings} | {dist_info} | <span class="badge badge-platform">{platform_text}</span></span>
            </div>
            """, unsafe_allow_html=True)

# ----------------- TAB 2: TICKET BOOKING ----------------- #
with tab_book:
    st.subheader("Book Ticket for Active Trains")
    col1, col2 = st.columns(2)

    all_sources = sorted(list({t["source"] for t in trains.values()}))
    all_destinations = sorted(list({t["destination"] for t in trains.values()}))

    with col1:
        src = st.selectbox("From (Origin):", all_sources)
    with col2:
        dst = st.selectbox("To (Destination):", all_destinations)

    matching = {num: t for num, t in trains.items() if t["source"] == src and t["destination"] == dst}

    if not matching:
        st.warning(f"No direct scheduled trains between {src} and {dst}.")
    else:
        st.write(f"#### Available Trains ({len(matching)})")
        for num, t in matching.items():
            with st.container(border=True):
                ca, cb, cc = st.columns([3, 2, 2])
                ca.markdown(f"**{t['name']}** (`#{num}`)")
                cb.markdown(f"💺 Available Seats: **{t['available_seats']}** / {t['total_seats']}")
                cc.markdown(f"💰 Fare: **₹{t['fare']:.2f}**")

        st.write("---")
        st.write("#### Passenger Details")
        with st.form("book_form", clear_on_submit=True):
            chosen_train_no = st.selectbox(
                "Choose Train:",
                list(matching.keys()),
                format_func=lambda x: f"{matching[x]['name']} (#{x})"
            )
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                p_name = st.text_input("Passenger Name", placeholder="e.g., Sumeet Patil")
            with col_p2:
                p_age = st.number_input("Passenger Age", min_value=1, max_value=110, value=26)

            submitted = st.form_submit_button("Book & Confirm Ticket", type="primary", use_container_width=True)

            if submitted:
                if not p_name.strip():
                    st.error("Please enter passenger name.")
                else:
                    target_train = trains[chosen_train_no]
                    if target_train["available_seats"] <= 0:
                        st.error("No seats available on this train.")
                    else:
                        seat_no = (target_train["total_seats"] - target_train["available_seats"]) + 1
                        pnr = "PNR" + "".join(random.choices(string.digits, k=6))

                        # Deduct seat
                        target_train["available_seats"] -= 1

                        # Save booking
                        data_store["bookings"][pnr] = {
                            "pnr": pnr,
                            "train_no": chosen_train_no,
                            "train_name": target_train["name"],
                            "passenger_name": p_name.strip(),
                            "passenger_age": int(p_age),
                            "seat_no": seat_no,
                            "fare": target_train["fare"],
                            "source": src,
                            "destination": dst,
                            "booked_on": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                        }
                        save_store(data_store)

                        st.success("🎉 Ticket Confirmed Successfully!")
                        st.balloons()
                        st.json(data_store["bookings"][pnr])

# ----------------- TAB 3: PNR STATUS & CANCEL ----------------- #
with tab_pnr:
    st.subheader("Manage Reservation")
    input_pnr = st.text_input("Enter PNR Number:", placeholder="e.g., PNR123456").strip().upper()

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        btn_check = st.button("Check PNR Status", type="primary", use_container_width=True)
    with col_btn2:
        btn_cancel = st.button("Cancel Ticket", type="secondary", use_container_width=True)

    bookings = data_store["bookings"]

    if btn_check:
        if input_pnr in bookings:
            rec = bookings[input_pnr]
            st.success(f"Active Booking Found for PNR {input_pnr}")
            st.table([{
                "PNR": rec["pnr"],
                "Passenger": f"{rec['passenger_name']} ({rec['passenger_age']} yrs)",
                "Train": f"{rec['train_name']} (#{rec['train_no']})",
                "Route": f"{rec['source']} ➜ {rec['destination']}",
                "Seat No": f"Coach S1 - #{rec['seat_no']}",
                "Fare": f"₹{rec['fare']:.2f}",
                "Booked On": rec["booked_on"]
            }])
        else:
            st.error("PNR not found or invalid.")

    if btn_cancel:
        if input_pnr in bookings:
            train_no = bookings[input_pnr]["train_no"]
            trains[train_no]["available_seats"] += 1
            del bookings[input_pnr]
            save_store(data_store)
            st.success(f"Ticket {input_pnr} cancelled. Seat released back to Train #{train_no} and stored to pickle file.")
        else:
            st.error("No active reservation found for this PNR.")
