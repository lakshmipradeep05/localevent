import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import sqlite3
import urllib.parse

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")

# ----------------------------
# Database Connection
# ----------------------------
conn = sqlite3.connect("event_finder.db", check_same_thread=False)
cursor = conn.cursor()

# ----------------------------
# Ensure tables exist
# ----------------------------
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS saved_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    event_name TEXT,
    event_date TEXT,
    event_venue TEXT,
    event_url TEXT,
    saved_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
conn.commit()

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(
    page_title="Live Event Finder",
    page_icon="🎟️",
    layout="wide"
)
# ----------------------------
# Initialize session state
# ----------------------------
if "user" not in st.session_state:
    st.session_state["user"] = None
if "saved_events" not in st.session_state:
    st.session_state["saved_events"] = []
if "search_results" not in st.session_state:
    st.session_state["search_results"] = []
if "search_city" not in st.session_state:
    st.session_state["search_city"] = ""

# ----------------------------
# Helper function to load saved events
# ----------------------------
def load_saved_events():
    if st.session_state["user"]:
        user_id = st.session_state["user"][0]
        cursor.execute("""
            SELECT event_name, event_date, event_venue, event_url
            FROM saved_events
            WHERE user_id=?
            ORDER BY saved_at DESC
        """, (user_id,))
        st.session_state["saved_events"] = cursor.fetchall()
    else:
        st.session_state["saved_events"] = []

# ----------------------------
# Save event function
# ----------------------------
def save_event(user_id, name, date, venue, event_url):
    cursor.execute("""
        SELECT * FROM saved_events
        WHERE user_id=? AND event_name=? AND event_date=?
    """, (user_id, name, date))
    existing = cursor.fetchone()
    if existing:
        st.info("You already saved this event!")
    else:
        cursor.execute("""
            INSERT INTO saved_events (user_id, event_name, event_date, event_venue, event_url)
            VALUES (?, ?, ?, ?, ?)
        """, (user_id, name, date, venue, event_url))
        conn.commit()
        load_saved_events()
        st.success("Event saved to your account!")
        st.rerun()


# ----------------------------
# App Header
# ----------------------------
st.markdown(
    "<h1 style='text-align: center;'>🎉 Eventure</h1>",
    unsafe_allow_html=True
)

st.markdown(
    "<h3 style='text-align: center; color: gray;'>Discover Live Events Near You</h3>",
    unsafe_allow_html=True
)

st.markdown(
    "<p style='text-align: center; font-size:16px;'>"
    "Find, save, and get personalized recommendations for concerts, sports, theatre, and more!"
    "</p>",
    unsafe_allow_html=True
)

st.markdown("---")
# ----------------------------
# User Authentication (Clean Top Section)
# ----------------------------
if not st.session_state["user"]:

    st.subheader("🔐 Login / Sign Up")

    auth_choice = st.radio("Choose Option", ["Login", "Sign Up"], horizontal=True)

    if auth_choice == "Sign Up":

        col1, col2, col3 = st.columns(3)

        with col1:
            new_username = st.text_input("Username", key="signup_username")

        with col2:
            new_email = st.text_input("Email", key="signup_email")

        with col3:
            new_password = st.text_input("Password", type="password", key="signup_password")

        if st.button("Create Account"):

            if new_username and new_email and new_password:
                try:
                    cursor.execute(
                        "INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                        (new_username, new_email, new_password)
                    )
                    conn.commit()
                    st.success("Account created! Please login.")
                except sqlite3.IntegrityError:
                    st.error("Username or Email already exists.")
            else:
                st.warning("Please fill all fields.")

    else:

        col1, col2 = st.columns(2)

        with col1:
            username = st.text_input("Username")

        with col2:
            password = st.text_input("Password", type="password", key="login_password")

        if st.button("Login"):

            cursor.execute(
                "SELECT * FROM users WHERE username=? AND password=?",
                (username, password)
            )
            user = cursor.fetchone()

            if user:
                st.session_state["user"] = user
                load_saved_events()
                st.success(f"Welcome {username}!")
                st.rerun()
            else:
                st.error("Invalid credentials")
# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("🔍 Filters")
city = st.sidebar.text_input("📍 Enter City", key="city_input")
keyword = st.sidebar.text_input("Keyword (optional)", key="keyword_input")
category = st.sidebar.selectbox(
    "🎭 Category",
    ["", "Music", "Sports", "Arts & Theatre", "Film"],
    key="category_select"
)

st.sidebar.subheader("📅 Date Filter")
date_option = st.sidebar.selectbox(
    "Select Date Option",
    ["Any", "Today", "This Weekend", "Custom Range"]
)

start_date = end_date = None
today = datetime.utcnow()
if date_option == "Today":
    start_date = today
    end_date = today + timedelta(days=1)
elif date_option == "This Weekend":
    start_date = today
    end_date = today + timedelta(days=3)
elif date_option == "Custom Range":
    start_date = st.sidebar.date_input("Start Date", key="start_date")
    end_date = st.sidebar.date_input("End Date", key="end_date")

search_button = st.sidebar.button("🚀 Search Events")

# ----------------------------
# Search Events Logic
# ----------------------------
if search_button:
    if not city:
        st.error("Please enter a city name.")
    else:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"
        params = {
            "apikey": API_KEY,
            "city": city,
            "size": 20
        }
        params["sort"] = "relevance,asc"
        if keyword:
            params["keyword"] = keyword
        if category:
            params["classificationName"] = category
        if not category:
            params["segmentName"] = "Music,Sports,Arts & Theatre"
        if start_date and end_date:
            params["startDateTime"] = f"{start_date.strftime('%Y-%m-%d')}T00:00:00Z"
            params["endDateTime"] = f"{end_date.strftime('%Y-%m-%d')}T23:59:59Z"

        with st.spinner("Fetching events..."):
            response = requests.get(url, params=params)
            data = response.json()
            if "_embedded" in data:
                st.session_state["search_results"] = data["_embedded"]["events"]
                st.session_state["search_city"] = city
            else:
                st.session_state["search_results"] = []
                st.warning("No events found for this search.")

# ----------------------------
# Display Search Results
# ----------------------------
if st.session_state["search_results"]:
    events = st.session_state["search_results"]
    map_data = []
    category_count = {}
    st.success(f"Events near {st.session_state.get('search_city', '').title()}")

    for idx, event in enumerate(events):
        name = event.get("name", "No Name")
        date = event.get("dates", {}).get("start", {}).get("localDate", "N/A")
        event_url = event.get("url", "#")
        image = event.get("images")[0]["url"] if "images" in event else None
        venue = "Venue Not Available"

        if "_embedded" in event:
            venue_info = event["_embedded"]["venues"][0]
            venue = venue_info.get("name", venue)
            if "location" in venue_info:
                lat = float(venue_info["location"]["latitude"])
                lon = float(venue_info["location"]["longitude"])
                map_data.append({"lat": lat, "lon": lon})

        if "classifications" in event:
            cat = event["classifications"][0]["segment"]["name"]
            category_count[cat] = category_count.get(cat, 0) + 1

        # Event Card
        with st.container():
            col1, col2, col3 = st.columns([1, 3, 1])
            with col1:
                if image:
                    st.image(image, use_container_width=True)
            with col2:
                st.markdown(f"### {name}")
                st.write(f"📅 **Date:** {date}")
                st.write(f"📍 **Venue:** {venue}")
                st.markdown(f"[🎟️ View Event]({event_url})")
            with col3:
                if st.button("⭐ Save", key=f"save_{idx}"):
                    if st.session_state["user"]:
                        save_event(
                            st.session_state["user"][0],
                            name,
                            date,
                            venue,
                            event_url
                        )
                    else:
                        st.warning("Please log in to save events.")
            st.markdown("---")

    # Analytics
    st.subheader("Event Analytics")
    colA, colB = st.columns(2)
    
    with colA:
        st.metric("Total Events Found", len(events))
    
    with colB:
        if category_count:
            # 1. Clear the current figure to prevent data ghosting
            plt.clf() 
            
            # 2. Create the plot with improved styling
            df = pd.DataFrame(list(category_count.items()), columns=["Category", "Count"])
            
            # Use a slightly larger figure size to give labels more room
            fig, ax = plt.subplots(figsize=(6, 4))
            
            ax.bar(df["Category"], df["Count"], color='skyblue', edgecolor='navy')
            ax.set_xlabel("Category", fontsize=10)
            ax.set_ylabel("Number of Events", fontsize=10)
            ax.set_title("Events by Category", fontsize=12)
            
            # 3. FIX: Adjust label rotation and alignment to prevent overlapping
            plt.xticks(rotation=45, ha='right')
            
            # 4. FIX: Use tight_layout so labels don't get cut off at the bottom
            plt.tight_layout()
            
            st.pyplot(fig)

    # Map
    if map_data:
        st.subheader("Event Locations")
        st.map(map_data)
# ----------------------------
# 🔥 Smart Recommendation System
# ----------------------------
if st.session_state["user"]:

    st.subheader("🔥 Recommended For You")

    user_id = st.session_state["user"][0]

    # Get user's favorite category
    cursor.execute("""
        SELECT category, COUNT(category)
        FROM saved_events
        WHERE user_id=? AND category IS NOT NULL
        GROUP BY category
        ORDER BY COUNT(category) DESC
        LIMIT 1
    """, (user_id,))

    result = cursor.fetchone()

    if result:

        favorite_category = result[0]
        st.info(f"Personalized based on: {favorite_category}")

        # Get already saved event names
        cursor.execute("""
            SELECT event_name FROM saved_events
            WHERE user_id=?
        """, (user_id,))

        saved_names = [row[0] for row in cursor.fetchall()]

        scored_events = []

        for event in st.session_state["search_results"]:

            score = 0

            name = event.get("name", "")
            city_match = 0

            # Category match
            if "classifications" in event:
                cat = event["classifications"][0]["segment"]["name"]
                if cat == favorite_category:
                    score += 3

            # Avoid already saved events
            if name not in saved_names:
                score += 2

            # Optional: Boost if keyword matches search
            if keyword and keyword.lower() in name.lower():
                score += 2

            if score > 0:
                scored_events.append((score, event))

        # Sort by highest score
        scored_events.sort(reverse=True, key=lambda x: x[0])

        if scored_events:

            for score, event in scored_events[:5]:  # Show top 5 only

                st.success(f"⭐ {event.get('name')}")
                st.write(f"📅 {event.get('dates', {}).get('start', {}).get('localDate')}")
                st.markdown(f"[View Event]({event.get('url')})")
                st.markdown("---")

        else:
            st.write("No strong recommendations found in this search.")

    else:
        st.write("Save more events to improve recommendations!")
# ----------------------------
# Right Side Panel
# ----------------------------

left, center, right = st.columns([1, 3, 1])

with right:

    # ---------------- Chatbot ----------------
    st.subheader("🤖 Event Assistant")

    if "chat_history" not in st.session_state:
        st.session_state["chat_history"] = []

    # Input box
    user_input = st.text_input("Type a message...", key="chat_input")

    if st.button("Send", key="chat_send") and user_input:
        text = user_input.lower()
        if "concert" in text or "music" in text:
            response = "Here are some upcoming music events! 🎵"
        elif "sports" in text:
            response = "I can show you nearby sports events! 🏟️"
        elif "save" in text:
            response = "You can save events by clicking the ⭐ button next to them."
        elif "recommend" in text:
            response = "I can recommend events based on your saved events!"
        else:
            response = "I can help with filters, saving events, and recommendations!"

        st.session_state["chat_history"].append(("You", user_input))
        st.session_state["chat_history"].append(("Bot", response))

# Display chat messages
    for sender, message in st.session_state["chat_history"]:
        if sender == "You":
            st.markdown(
                f"<div style='background-color:#DCF8C6; padding:10px; border-radius:10px; margin:5px 0; width: fit-content; float:right; clear:both;'><b>{sender}:</b> {message}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"<div style='background-color:#F1F0F0; padding:10px; border-radius:10px; margin:5px 0; width: fit-content; float:left; clear:both;'><b>{sender}:</b> {message}</div>",
                unsafe_allow_html=True,
            )

    st.markdown("<div style='clear:both'></div>", unsafe_allow_html=True)

    # ---------------- Saved Events ----------------
    st.subheader("⭐ Saved Events")

    if st.session_state["saved_events"] and st.session_state["user"]:

        today = datetime.utcnow().date()
        tomorrow = today + timedelta(days=1)

        for event in st.session_state["saved_events"]:
            name = event[0]
            date_str = event[1]
            venue = event[2]
            url = event[3]

            # category may or may not exist
            cat = event[4] if len(event) > 4 else None
            event_date = datetime.strptime(date_str, "%Y-%m-%d").date()

            # Reminder highlight
            if today <= event_date <= tomorrow:
                st.info(f"⏰ Upcoming: {name} on {date_str}")

            st.markdown(f"• [{name}]({url}) on {date_str}")

            # Sharing
            wa_message = urllib.parse.quote(
                f"Check out this event: {name} on {date_str}. {url}"
            )
            tweet_message = urllib.parse.quote(
                f"Check out this event: {name} on {date_str} {url}"
            )

            st.markdown(
                f"[WhatsApp](https://wa.me/?text={wa_message}) | "
                f"[Twitter](https://twitter.com/intent/tweet?text={tweet_message})"
            )

    else:
        st.write("No saved events yet.")
# ----------------------------
# Logout button
# ----------------------------
if st.session_state["user"]:
    st.sidebar.write(f"👤 Logged in as: {st.session_state['user'][1]}")
    if st.sidebar.button("Logout"):
        st.session_state["user"] = None
        st.session_state["saved_events"] = []
        st.session_state["search_results"] = []
        st.sidebar.success("Logged out successfully")
        st.rerun()
    