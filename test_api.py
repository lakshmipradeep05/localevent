import requests

API_KEY = "XBAWKJdieqgwKIDlZdvUNRGAwLI4Dq3e"
city = "New York"
url = "https://app.ticketmaster.com/discovery/v2/events.json"
params = {"apikey": API_KEY, "city": city, "size": 5}

response = requests.get(url, params=params)
data = response.json()

if "_embedded" in data:
    events = data["_embedded"]["events"]
    for event in events:
        name = event["name"]
        date = event["dates"]["start"]["localDate"]
        venue = event["_embedded"]["venues"][0]["name"]
        print(f"{name} | {date} | {venue}")
else:
    print("No events found.")