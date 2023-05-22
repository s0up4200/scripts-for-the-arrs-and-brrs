"""
Author: soup
Description: The point of this script is to make sure everything in Radarr is seeded in your torrent client. Whenever a torrent is deleted from the tracker, programs like https://github.com/StuffAnThings/qbit_manage can automatically delete it from your qBittorrent instance for you.
This naturally breaks the hardlink and leaves you with a movie that is not seeded anymore.

This script checks for non-hardlinked movies in your Radarr library. When it finds a non-hardlinked movie, it deletes the file and instructs Radarr to trigger a search for the movie again.
"""

import os
import csv
import sys
import requests
import time

RADARR_URL = "http://localhost:7878/radarr"  # Replace with your Radarr URL
RADARR_API_KEY = "api_key"  # Replace with your Radarr API key
DIR_PATH = "/path/to/your/movie/directory"  # Replace with your movie directory path


def get_non_hardlinked_files(dir_path):
    non_hardlinked_files = []

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".mkv" or ".mp4"):
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.stat(file_path).st_nlink == 1:
                    non_hardlinked_files.append(file_path)

    return non_hardlinked_files


def save_to_csv(non_hardlinked_files, csv_file_path):
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["File Path"])

        for file_path in non_hardlinked_files:
            csv_writer.writerow([file_path])


def read_from_csv(csv_file_path):
    non_hardlinked_files = []

    with open(csv_file_path, mode="r", newline="", encoding="utf-8") as csv_file:
        csv_reader = csv.reader(csv_file)
        next(csv_reader)  # Skip header

        for row in csv_reader:
            non_hardlinked_files.append(row[0])

    return non_hardlinked_files


def get_movie_by_folder_path(folder_path):
    response = requests.get(
        f"{RADARR_URL}/api/v3/movie",
        params={"apikey": RADARR_API_KEY},
    )

    response.raise_for_status()
    movies = response.json()

    folder_path_abs = os.path.abspath(folder_path)

    for movie in movies:
        movie_path_abs = os.path.abspath(movie["path"])
        if movie_path_abs == folder_path_abs:
            return movie

    return None


def refresh_movie(movie_id):
    command_url = f"{RADARR_URL}/api/v3/command"
    command_payload = {"name": "RescanMovie", "movieId": movie_id}
    response = requests.post(
        command_url, json=command_payload, params={"apikey": RADARR_API_KEY}
    )
    response.raise_for_status()
    print(f"\nRefreshing movie (ID: {movie_id})")
    time.sleep(5)  # Wait for the refresh to complete


def monitor_and_search_movie(movie_id, movie_file_path):
    if not force:
        user_input = input(f"Delete non-hardlinked movie: {movie_file_path}? (y/N): ")
        if user_input.lower() != "y":
            print("Skipping deletion.")
            sys.exit(0)

    # Delete the movie file
    try:
        os.remove(movie_file_path)
        print(f"Deleted non-hardlinked movie: {movie_file_path}")
    except Exception as e:
        print(f"Error deleting movie file: {e}")
        return

    refresh_movie(movie_id)

    movie_url = f"{RADARR_URL}/api/v3/movie/{movie_id}"
    response = requests.get(movie_url, params={"apikey": RADARR_API_KEY})
    response.raise_for_status()
    movie = response.json()
    movie["monitored"] = True

    response = requests.put(movie_url, json=movie, params={"apikey": RADARR_API_KEY})
    response.raise_for_status()

    search_url = f"{RADARR_URL}/api/v3/command"
    search_payload = {"name": "MoviesSearch", "movieIds": [movie_id]}

    response = requests.post(
        search_url, json=search_payload, params={"apikey": RADARR_API_KEY}
    )
    response.raise_for_status()

    print(f"\nMonitoring and searching for movie: {movie['title']} (ID: {movie['id']})")


def process_movies(non_hardlinked_files, amount, force=False):
    print(f"\nLooking for non-hardlinked movies in {DIR_PATH}...\n")
    print(f"Found {len(non_hardlinked_files)} non-hardlinked movies.", end="")
    if len(non_hardlinked_files) > 0:
        print(" Saved to non_hardlinked_files.csv", end="")

    if len(non_hardlinked_files) > 0 and amount > 0:
        print(f" Replacing {amount} of them.\n")
    else:
        print("\n")

    for movie_file_path in non_hardlinked_files[:amount]:
        folder_path = os.path.dirname(movie_file_path)
        movie = get_movie_by_folder_path(folder_path)

        if movie:
            monitor_and_search_movie(movie["id"], movie_file_path)
            non_hardlinked_files.remove(movie_file_path)
            with open("non_hardlinked_files.csv", "w") as f:
                f.write("File Path\n")
                for remaining_file in non_hardlinked_files:
                    f.write(f"{remaining_file}\n")
        else:
            print(f"Movie not found in Radarr for folder path: {folder_path}")


def show_help():
    help_text = """Usage: python3 hardlink-radarr.py [options]

Options:

  --replace <amount>   Replace specified amount of non-hardlinked movies
  --force              Automatically delete non-hardlinked movies without confirmation (Must be called with --replace <amount>)
  --help               Display this help text
  
  If no flags are specified, the script will only save non-hardlinked movies to non_hardlinked_files.csv
"""
    print(help_text)


if __name__ == "__main__":
    if "--help" in sys.argv:
        show_help()
        sys.exit(0)

    csv_file_path = "non_hardlinked_files.csv"

    non_hardlinked_files = get_non_hardlinked_files(DIR_PATH)
    save_to_csv(non_hardlinked_files, csv_file_path)

    force = False
    if "--force" in sys.argv:
        force = True

    if len(sys.argv) > 1 and sys.argv[1] == "--replace":
        if len(sys.argv) < 3:
            print(
                "Error: Missing amount. Usage: python3 hardlink-radarr.py --replace <amount>"
            )
            sys.exit(1)

        amount = int(sys.argv[2])
        non_hardlinked_files = read_from_csv(csv_file_path)
        process_movies(non_hardlinked_files, amount, force)
    else:
        process_movies(non_hardlinked_files, 0, force)
