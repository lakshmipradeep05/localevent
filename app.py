import streamlit as st
import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")

st.title("🎟️ Live Event Finder")

city = st.text_input("Enter your city")

if st.button("Search Events"):

    if not city:
        st.error("Please enter a city name")

    else:
        url = "https://app.ticketmaster.com/discovery/v2/events.json"

        params = {
            "apikey": API_KEY,
            "city": city,
            "size": 5
        }

        response = requests.get(url, params=params)
        data = response.json()

        if "_embedded" in data:

            with st.spinner("Fetching events..."):

                events = data["_embedded"]["events"]
                map_data = []

                st.success(f"Top events near {city.title()}")

                for event in events:

                    name = event["name"]
                    date = event["dates"]["start"]["localDate"]
                    venue = event["_embedded"]["venues"][0]["name"]
                    url = event["url"]

                    # Get image (if available)
                    image = None
                    if "images" in event:
                        image = event["images"][0]["url"]

                    # Collect map coordinates
                    venue_info = event["_embedded"]["venues"][0]

                    if "location" in venue_info:
                        lat = venue_info["location"]["latitude"]
                        lon = venue_info["location"]["longitude"]

                        map_data.append({
                            "lat": float(lat),
                            "lon": float(lon)
                        })

                    col1, col2 = st.columns([1, 2])

                    with col1:
                        if image:
                            st.image(image, use_container_width=True)

                    with col2:
                        st.subheader(name)
                        st.write(f"📅 {date}")
                        st.write(f"📍 {venue}")
                        st.markdown(f"[🎟️ View Event]({url})")

                    st.divider()

                # 👇 MAP SECTION GOES HERE (AFTER LOOP)

                if map_data:
                    st.subheader("📍 Event Locations Map")
                    st.map(map_data)

        else:
            st.warning("No events found.")