import requests
from datetime import datetime
import random
import sys
import argparse
import os

"""
Author: soup
Description: This script will check for movies in Radarr that do not have the given custom format assigned and are considered released.
It then asks you if you want to trigger a search for upgrades for those movies. It will ask you how many movies you want to search for.
"""

RADARR_URL = os.getenv(
    "RADARR_URL", "http://localhost:7878/radarr"
)  # Change this to your Radarr URL
RADARR_API_KEY = os.getenv(
    "RADARR_API_KEY", "api_key"
)  # Change this to your Radarr API key
CUSTOM_FORMAT_NAME = "HD Bluray Tier 01"  # Change this to the name of the custom format you want to filter by


def is_movie_available(movie):
    current_date = datetime.now().date()
    if movie["status"] == "released":
        if "physicalRelease" in movie:
            physical_release_date = datetime.strptime(
                movie["physicalRelease"], "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            if physical_release_date <= current_date:
                return True
        if "digitalRelease" in movie:
            digital_release_date = datetime.strptime(
                movie["digitalRelease"], "%Y-%m-%dT%H:%M:%SZ"
            ).date()
            if digital_release_date <= current_date:
                return True
    return False


def monitor_movie(movie):
    update_url = f'{RADARR_URL}/api/v3/movie/{movie["id"]}?apiKey={RADARR_API_KEY}'
    headers = {"Content-Type": "application/json"}
    payload = movie
    payload["monitored"] = True
    response = requests.put(update_url, json=payload, headers=headers)

    if response.status_code not in [200, 202]:
        print(
            f"Error updating monitored status for movie ID {movie['id']}: {response.status_code}"
        )
        return False
    return True


def fetch_custom_formats():
    response = requests.get(
        f"{RADARR_URL}/api/v3/customformat", params={"apiKey": RADARR_API_KEY}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching custom formats: {response.status_code}")
        return []


def find_custom_format_id(custom_formats, custom_format_name):
    for custom_format in custom_formats:
        if custom_format["name"] == custom_format_name:
            return custom_format["id"]
    return None


def fetch_movies():
    response = requests.get(
        f"{RADARR_URL}/api/v3/movie", params={"apiKey": RADARR_API_KEY}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching movies: {response.status_code}")
        return []


def filter_movies(movies, custom_format_id):
    filtered_movies = []
    for movie in movies:
        if not is_movie_available(movie):
            continue
        if "movieFile" in movie:
            movie_file_response = requests.get(
                f'{RADARR_URL}/api/v3/moviefile/{movie["movieFile"]["id"]}',
                params={"apiKey": RADARR_API_KEY},
            )
            if movie_file_response.status_code == 200:
                movie_file = movie_file_response.json()
                if custom_format_id not in [
                    format["id"] for format in movie_file.get("customFormats", [])
                ]:
                    filtered_movies.append(movie)
            else:
                print(
                    f'Error fetching movie file for {movie["title"]}: {movie_file_response.status_code}'
                )
        else:
            filtered_movies.append(movie)
    return filtered_movies


def monitor_filtered_movies(filtered_movies):
    unmonitored_count = 0
    filtered_count = len(filtered_movies)

    for movie in filtered_movies:
        if not movie["monitored"]:
            if monitor_movie(movie):
                movie["monitored"] = True
                unmonitored_count += 1

    return unmonitored_count, filtered_count


def parse_args():
    parser = argparse.ArgumentParser(
        description="Check for custom format, monitor, and search for upgrades in Radarr."
    )
    parser.add_argument(
        "--unattended",
        type=int,
        metavar="N",
        help="Run the script unattended and search for N movies at the end without user interaction.",
    )

    return parser.parse_args()


def main():
    # If the script is not called with --help or -h, print the check statement
    if all(arg not in sys.argv for arg in ("--help", "-h")):
        print(
            f'Checking for movies in Radarr that do not have the custom format "{CUSTOM_FORMAT_NAME}" assigned and are considered available...'
        )

    args = parse_args()

    custom_formats = fetch_custom_formats()
    custom_format_id = find_custom_format_id(custom_formats, CUSTOM_FORMAT_NAME)

    if custom_format_id is None:
        print(f'Error: Custom format "{CUSTOM_FORMAT_NAME}" not found')
    else:
        movies = fetch_movies()
        filtered_movies = filter_movies(movies, custom_format_id)

        # Add this line to print the total count of filtered movies
        print(
            f"Found {len(filtered_movies)} movies without the custom format '{CUSTOM_FORMAT_NAME}'."
        )

        if args.unattended is None:
            save_answer = input(
                "Save the list of movies to not-cutoff.txt and continue to search? (Y/n): "
            )
            if save_answer.lower() != "y" and save_answer != "":
                print("Exiting program.")
                sys.exit(0)
            num_search = input(
                "How many movies do you want to search? (Enter 0 to skip): "
            )
        else:
            save_answer = "y"
            num_search = args.unattended

        if save_answer.lower() != "y" and save_answer != "":
            print("Skipping saving the list of movies.")
        else:
            with open("not-cutoff.txt", "w") as f:
                for movie in filtered_movies:
                    f.write(movie["title"] + "\n")
            print("List of movies has been saved to not-cutoff.txt")

            try:
                num_search = int(num_search)
            except ValueError:
                num_search = 0

            if num_search > 0:
                random_movies = random.sample(filtered_movies, num_search)
                for movie in random_movies:
                    if not movie["monitored"]:
                        monitor_movie(movie)
                    search_url = f"{RADARR_URL}/api/v3/command"
                    search_payload = {
                        "name": "MoviesSearch",
                        "movieIds": [movie["id"]],
                    }
                    response = requests.post(
                        search_url,
                        json=search_payload,
                        params={"apiKey": RADARR_API_KEY},
                    )
                    if response.status_code == 201:
                        print(
                            f"Search for upgraded version of \"{movie['title']}\" has been triggered."
                        )
                    else:
                        print(
                            f"Error searching for upgraded version of \"{movie['title']}\": {response.status_code}"
                        )


if __name__ == "__main__":
    main()
