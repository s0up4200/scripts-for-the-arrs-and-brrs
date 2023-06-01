import argparse
import os
import random
import sys
from datetime import datetime

import requests

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
CUSTOM_FORMAT_NAMES = [
    "HD Bluray Tier 01",
    "HD Bluray Tier 02",
]  # Change this to the names of the custom formats you want to filter by


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
    update_url = (
        f'{RADARR_URL}/api/v3/movie/{movie["id"]}?apiKey={RADARR_API_KEY}'
    )
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


def find_custom_format_ids(custom_formats, custom_format_names):
    custom_format_ids = []
    for custom_format_name in custom_format_names:
        for custom_format in custom_formats:
            if custom_format["name"] == custom_format_name:
                custom_format_ids.append(custom_format["id"])
                break
        else:
            print(f'Error: Custom format "{custom_format_name}" not found')
    return custom_format_ids


def fetch_movies():
    response = requests.get(
        f"{RADARR_URL}/api/v3/movie", params={"apiKey": RADARR_API_KEY}
    )
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error fetching movies: {response.status_code}")
        return []


def filter_movies(movies, custom_format_ids, match):
    filtered_movies = []
    for movie in movies:
        if not is_movie_available(movie):
            continue
        movie_custom_format_ids = []  # default to empty list
        if "movieFile" in movie:
            movie_file_response = requests.get(
                f'{RADARR_URL}/api/v3/moviefile/{movie["movieFile"]["id"]}',
                params={"apiKey": RADARR_API_KEY},
            )
            if movie_file_response.status_code == 200:
                movie_file = movie_file_response.json()
                movie_custom_format_ids = [
                    format["id"]
                    for format in movie_file.get("customFormats", [])
                ]
            else:
                print(
                    f'Error fetching movie file for {movie["title"]}: {movie_file_response.status_code}'
                )
        if match == "any":
            if not any(
                custom_format_id in movie_custom_format_ids
                for custom_format_id in custom_format_ids
            ):
                filtered_movies.append(movie)
        else:
            if not all(
                custom_format_id in movie_custom_format_ids
                for custom_format_id in custom_format_ids
            ):
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
    parser.add_argument(
        "--match",
        choices=["any", "all"],
        default="all",
        help="Choose whether any or all custom formats need to match ('any' or 'all' defaults to 'all').",
    )

    return parser.parse_args()


def main():
    # If the script is not called with --help or -h, print the check statement
    args = parse_args()
    if all(arg not in sys.argv for arg in ("--help", "-h")):
        print(
            f'Checking for movies in Radarr that do not have {args.match} of the custom formats "{CUSTOM_FORMAT_NAMES}" assigned and are considered available...'
        )

    args = parse_args()

    custom_formats = fetch_custom_formats()
    custom_format_ids = find_custom_format_ids(
        custom_formats, CUSTOM_FORMAT_NAMES
    )

    if not custom_format_ids:
        print(
            f"Error: None of the custom formats {CUSTOM_FORMAT_NAMES} were found"
        )
    else:
        movies = fetch_movies()
        filtered_movies = filter_movies(movies, custom_format_ids, args.match)

        # Add this line to print the total count of filtered movies
        print(
            f"Found {len(filtered_movies)} movies without the custom format '{CUSTOM_FORMAT_NAMES}'."
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
