import sys
from datetime import datetime, timedelta

import requests

# This script searches for missing movies in Radarr that are considered available
# with a physical or digital release date.
# The maximum movies to search for is specified by the user when the script is run.
# Does not make repeated searches for the same movie. Interval is set to 12 hours
# Interval can be changed on line 36

RADARR_API_KEY = "api_key"
RADARR_URL = "http://127.0.0.1:7171/radarr"
SEARCHED_MOVIES_FILE = "searched_movies.txt"


def read_searched_movies():
    searched_movies = {}

    try:
        with open(SEARCHED_MOVIES_FILE, "r") as f:
            for line in f:
                movie_id, timestamp_str = line.strip().split(",")
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S")
                searched_movies[int(movie_id)] = timestamp
    except FileNotFoundError:
        pass

    return searched_movies


def write_searched_movies(searched_movies):
    with open(SEARCHED_MOVIES_FILE, "w") as f:
        for movie_id, timestamp in searched_movies.items():
            timestamp_str = timestamp.strftime("%Y-%m-%dT%H:%M:%S")
            f.write(f"{movie_id},{timestamp_str}\n")


def remove_old_searched_movies(searched_movies):
    cutoff_time = datetime.now() - timedelta(hours=12)
    return {
        movie_id: timestamp
        for movie_id, timestamp in searched_movies.items()
        if timestamp >= cutoff_time
    }


def search_missing_movies(api_key, base_url, max_movies_to_search):
    # Read the searched_movies file and remove old entries
    searched_movies = read_searched_movies()
    searched_movies = remove_old_searched_movies(searched_movies)
    write_searched_movies(searched_movies)

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
    available_missing_movies = [
        movie
        for movie in all_movies
        if movie["monitored"]
        and not movie["hasFile"]
        and movie["status"] == "released"
        and (
            "physicalRelease" in movie
            and datetime.strptime(movie["physicalRelease"], "%Y-%m-%dT%H:%M:%SZ").date()
            <= current_date
            or "digitalRelease" in movie
            and datetime.strptime(movie["digitalRelease"], "%Y-%m-%dT%H:%M:%SZ").date()
            <= current_date
        )
    ]

    # Perform a search for each missing movie (up to the maximum specified)
    count = 0
    for movie in available_missing_movies:
        if count >= max_movies_to_search:
            break

        movie_id = movie["id"]
        if movie_id in searched_movies:
            continue

        search_url = f"{base_url}/api/v3/command?apiKey={api_key}"
        search_data = {
            "name": "MoviesSearch",
            "movieIds": [movie_id],
        }
        response = requests.post(search_url, json=search_data)

        if response.status_code == 201:
            print(f"Search triggered for '{movie['title']}'")
            count += 1
            searched_movies[movie_id] = datetime.now()
        else:
            print(f"Failed to trigger search for '{movie['title']}'")

    write_searched_movies(searched_movies)

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
