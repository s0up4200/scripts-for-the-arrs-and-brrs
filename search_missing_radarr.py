import sys
import requests
from datetime import datetime

# This script searches for missing movies in Radarr that is considered available
# with a physical or digital release date.
# The maximum movies to search for is specified by the user when the script is run.

RADARR_API_KEY = "api_key"
RADARR_URL = "http://127.0.0.1:7171/radarr"

def search_missing_movies(api_key, base_url, max_movies_to_search):
    # Get the list of missing movies
    missing_movies_url = f"{base_url}/api/v3/movie?apiKey={api_key}"
    response = requests.get(missing_movies_url)
    
    # Check if the response is valid before parsing JSON
    if response.status_code != 200:
        print(f"Failed to get missing movies. Error: {response.status_code}")
        return
    
    try:
        all_movies = response.json()
    except ValueError as e:
        print(f"Failed to parse missing movies JSON response. Error: {e}")
        return

    # Get the current date
    current_date = datetime.now().date()

    # Filter out movies that are not monitored, not missing, or don't have a physical/digital release
    available_missing_movies = [movie for movie in all_movies if movie['monitored'] and not movie['hasFile'] and movie['status'] == 'released' and ('physicalRelease' in movie and datetime.strptime(movie['physicalRelease'], "%Y-%m-%dT%H:%M:%SZ").date() <= current_date or 'digitalRelease' in movie and datetime.strptime(movie['digitalRelease'], "%Y-%m-%dT%H:%M:%SZ").date() <= current_date)]
    
    # Perform a search for each missing movie (up to the maximum specified)
    count = 0
    for movie in available_missing_movies:
        if count >= max_movies_to_search:
            break

        search_url = f"{base_url}/api/v3/command?apiKey={api_key}"
        search_data = {
            "name": "MoviesSearch",
            "movieIds": [movie["id"]],
        }
        response = requests.post(search_url, json=search_data)

        if response.status_code == 201:
            print(f"Search triggered for '{movie['title']}'")
            count += 1
        else:
            print(f"Failed to trigger search for '{movie['title']}'")

    if count == 0:
        print("No missing movies found.")
    else:
        print(f"Search triggered for {count} movie(s).")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 search_missing_radarr.py <max_movies_to_search>")
        sys.exit(1)

    try:
        max_movies_to_search = int(sys.argv[1])
    except ValueError:
        print("Error: max_movies_to_search must be an integer")
        sys.exit(1)

    search_missing_movies(RADARR_API_KEY, RADARR_URL, max_movies_to_search)