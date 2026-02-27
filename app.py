import streamlit as st
import requests
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------
# Load Environment Variables
# ----------------------------
load_dotenv()
API_KEY = os.getenv("API_KEY")

# ----------------------------
# Page Configuration
# ----------------------------
st.set_page_config(
    page_title="Live Event Finder",
    page_icon="🎟️",
    layout="wide"
)

# ----------------------------
# Theme Toggle (Simple)
# ----------------------------
theme = st.sidebar.selectbox("Theme", ["Light", "Dark"])

if theme == "Dark":
    st.markdown(
        """
        <style>
        body { background-color: #0e1117; color: white; }
        </style>
        """,
        unsafe_allow_html=True
    )

# ----------------------------
# Session State for Bookmarks
# ----------------------------
if "saved_events" not in st.session_state:
    st.session_state.saved_events = []

# ----------------------------
# Header
# ----------------------------
st.title("🎟️ Live Event Finder")
st.markdown("---")

# ----------------------------
# Sidebar Filters
# ----------------------------
st.sidebar.header("Filters")

city = st.sidebar.text_input("Enter City")
keyword = st.sidebar.text_input("Keyword (optional)")

category = st.sidebar.selectbox(
    "Category",
    ["", "Music", "Sports", "Arts & Theatre", "Film", "Miscellaneous"]
)

# ----------------------------
# Date Filter
# ----------------------------
st.sidebar.subheader("Date Filter")

date_option = st.sidebar.selectbox(
    "Select Date Option",
    ["Any", "Today", "This Weekend", "Custom Range"]
)

start_date = None
end_date = None

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
# Main Logic
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

        if keyword:
            params["keyword"] = keyword

        if category:
            params["classificationName"] = category

        if start_date and end_date:
            params["startDateTime"] = f"{start_date}T00:00:00Z"
            params["endDateTime"] = f"{end_date}T23:59:59Z"

        with st.spinner("Fetching events..."):
            response = requests.get(url, params=params)
            data = response.json()

        # ----------------------------
        # If Events Found
        # ----------------------------
        if "_embedded" in data:

            events = data["_embedded"]["events"]
            map_data = []
            category_count = {}

            st.success(f"Events near {city.title()}")

            for idx, event in enumerate(events):

                name = event.get("name", "No Name")
                date = event.get("dates", {}).get("start", {}).get("localDate", "N/A")
                event_url = event.get("url", "#")

                # Count category
                if "classifications" in event:
                    cat = event["classifications"][0]["segment"]["name"]
                    category_count[cat] = category_count.get(cat, 0) + 1

                image = None
                if "images" in event:
                    image = event["images"][0]["url"]

                venue = "Venue Not Available"

                if "_embedded" in event:
                    venue_info = event["_embedded"]["venues"][0]
                    venue = venue_info.get("name", venue)

                    if "location" in venue_info:
                        lat = float(venue_info["location"]["latitude"])
                        lon = float(venue_info["location"]["longitude"])
                        map_data.append({"lat": lat, "lon": lon})

                # ----------------------------
                # Event Card
                # ----------------------------
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
                            event_data = {
                                "name": name,
                                "date": date,
                                "venue": venue,
                                "url": event_url
                            }

                            if event_data not in st.session_state.saved_events:
                                st.session_state.saved_events.append(event_data)

                    st.markdown("---")

            # ----------------------------
            # Analytics Section
            # ----------------------------
            st.subheader("Event Analytics")

            colA, colB = st.columns(2)

            with colA:
                st.metric("Total Events Found", len(events))

            with colB:

                if len(category_count) == 0:
                    st.info("No category data available.")

                elif len(category_count) == 1:
                    # If only one category → show metric
                    only_category = list(category_count.keys())[0]
                    st.metric("Category", only_category)

                else:
                    # Multiple categories → show bar chart
                    df = pd.DataFrame(
                        list(category_count.items()),
                        columns=["Category", "Count"]
                    )

                    fig, ax = plt.subplots()
                    ax.bar(df["Category"], df["Count"])
                    ax.set_xlabel("Category")
                    ax.set_ylabel("Number of Events")
                    ax.set_title("Events by Category")
                    plt.xticks(rotation=45)

                    st.pyplot(fig)

            # ----------------------------
            # Map Section
            # ----------------------------
            if map_data:
                st.subheader("Event Locations")
                st.map(map_data)

        else:
            st.warning("No events found for this search.")

# ----------------------------
# Saved Events Section
# ----------------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Saved Events")

if st.session_state.saved_events:
    for item in st.session_state.saved_events:
        st.sidebar.write(f"• {item['name']}")
else:
    st.sidebar.write("No saved events yet.")