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
            events = data["_embedded"]["events"]

            st.success(f"Top events in {city.title()}:")

            for event in events:
                name = event["name"]
                date = event["dates"]["start"]["localDate"]
                venue = event["_embedded"]["venues"][0]["name"]

                st.write(f"**{name}**")
                st.write(f"📅 {date}")
                st.write(f"📍 {venue}")
                st.write("---")
        else:
            st.warning("No events found.")