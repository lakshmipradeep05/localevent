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
# Theme Toggle
# ----------------------------
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])
if theme == "Dark":
    st.markdown("""
    <style>
    body { background-color: #0e1117; color: white; }
    </style>
    """, unsafe_allow_html=True)

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

# ----------------------------
# Header
# ----------------------------
st.title("🎟️ Live Event Finder")
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
            new_username = st.text_input("Username")

        with col2:
            new_email = st.text_input("Email")

        with col3:
            new_password = st.text_input("Password", type="password")

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
            password = st.text_input("Password", type="password")

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
st.sidebar.header("Filters")
city = st.sidebar.text_input("Enter City")
keyword = st.sidebar.text_input("Keyword (optional)")
category = st.sidebar.selectbox(
    "Category",
    ["", "Music", "Sports", "Arts & Theatre", "Film"]
)

st.sidebar.subheader("Date Filter")
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
    start_date = st.sidebar.date_input("Start Date")
    end_date = st.sidebar.date_input("End Date")

search_button = st.sidebar.button("Search Events")

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
            "size": 10
        }
        params["sort"] = "date,asc"
        if keyword:
            params["keyword"] = keyword
        if category:
            params["classificationName"] = category
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
# Display Saved Events + Reminders + Sharing
# ----------------------------
st.sidebar.subheader("Saved Events & Reminders")
if st.session_state["saved_events"] and st.session_state["user"]:
    user_id = st.session_state["user"][0]
    today = datetime.utcnow().date()
    tomorrow = today + timedelta(days=1)

    for event in st.session_state["saved_events"]:
        name, date_str, venue, url = event
        event_date = datetime.strptime(date_str, "%Y-%m-%d").date()

        # Highlight upcoming events (today or tomorrow)
        if today <= event_date <= tomorrow:
            st.sidebar.info(f"⏰ Upcoming: {name} on {date_str}")

        st.sidebar.markdown(f"• [{name}]({url}) on {date_str} at {venue}")

        # Social sharing
        wa_message = urllib.parse.quote(f"Check out this event: {name} on {date_str}. {url}")
        tweet_message = urllib.parse.quote(f"Check out this event: {name} on {date_str} {url}")
        st.sidebar.markdown(f"[WhatsApp](https://wa.me/?text={wa_message}) | [Twitter](https://twitter.com/intent/tweet?text={tweet_message})")
else:
    st.sidebar.write("No saved events yet.")
    