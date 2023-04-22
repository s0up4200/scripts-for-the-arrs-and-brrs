import requests
from datetime import datetime
import random
import argparse

"""
This script checks and monitors movies in Radarr based on a specified custom format and their availability.
It checks if a movie does not have the specified custom format assigned and if it has been physically or digitally released.
For filtered movies that are not monitored, the script updates their monitored status in Radarr.
At the end, a summary of the number of filtered movies and the unmonitored movies that have been monitored is printed.
"""

RADARR_URL = "http://localhost:7878/radarr"  # Change this to your Radarr URL
API_KEY = "api_key"  # Change this to your Radarr API key
CUSTOM_FORMAT_NAME = "HD Bluray Tier 01"  # Change this to the name of the custom format you want to filter by

print(f"Checking for movies in Radarr that do not have the custom format \"{CUSTOM_FORMAT_NAME}\" assigned and are available...")


def is_movie_available(movie):
    current_date = datetime.now().date()
    if movie['status'] == 'released':
        if 'physicalRelease' in movie:
            physical_release_date = datetime.strptime(movie['physicalRelease'], "%Y-%m-%dT%H:%M:%SZ").date()
            if physical_release_date <= current_date:
                return True
        if 'digitalRelease' in movie:
            digital_release_date = datetime.strptime(movie['digitalRelease'], "%Y-%m-%dT%H:%M:%SZ").date()
            if digital_release_date <= current_date:
                return True
    return False

def monitor_movie(movie):
    update_url = f'{RADARR_URL}/api/v3/movie/{movie["id"]}?apiKey={API_KEY}'
    headers = {'Content-Type': 'application/json'}
    payload = movie
    payload['monitored'] = True
    response = requests.put(update_url, json=payload, headers=headers)

    if response.status_code not in [200, 202]:
        print(f"Error updating monitored status for movie ID {movie['id']}: {response.status_code}")
        return False
    return True

def fetch_custom_formats():
    response = requests.get(f'{RADARR_URL}/api/v3/customformat', params={'apiKey': API_KEY})
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching custom formats: {response.status_code}')
        return []


def find_custom_format_id(custom_formats, custom_format_name):
    for custom_format in custom_formats:
        if custom_format['name'] == custom_format_name:
            return custom_format['id']
    return None


def fetch_movies():
    response = requests.get(f'{RADARR_URL}/api/v3/movie', params={'apiKey': API_KEY})
    if response.status_code == 200:
        return response.json()
    else:
        print(f'Error fetching movies: {response.status_code}')
        return []

def filter_movies(movies, custom_format_id):
    filtered_movies = []
    for movie in movies:
        if not is_movie_available(movie):
            continue
        if 'movieFile' in movie:
            movie_file_response = requests.get(f'{RADARR_URL}/api/v3/moviefile/{movie["movieFile"]["id"]}', params={'apiKey': API_KEY})
            if movie_file_response.status_code == 200:
                movie_file = movie_file_response.json()
                if custom_format_id not in [format['id'] for format in movie_file.get('customFormats', [])]:
                    filtered_movies.append(movie)
            else:
                print(f'Error fetching movie file for {movie["title"]}: {movie_file_response.status_code}')
        else:
            filtered_movies.append(movie)
   
def filter_movies(movies, custom_format_id):
    filtered_movies = []
    for movie in movies:
        if not is_movie_available(movie):
            continue
        if 'movieFile' in movie:
            movie_file_response = requests.get(f'{RADARR_URL}/api/v3/moviefile/{movie["movieFile"]["id"]}', params={'apiKey': API_KEY})
            if movie_file_response.status_code == 200:
                movie_file = movie_file_response.json()
                if custom_format_id not in [format['id'] for format in movie_file.get('customFormats', [])]:
                    filtered_movies.append(movie)
            else:
                print(f'Error fetching movie file for {movie["title"]}: {movie_file_response.status_code}')
        else:
            filtered_movies.append(movie)
    return filtered_movies

def monitor_filtered_movies(filtered_movies):
    unmonitored_count = 0
    filtered_count = len(filtered_movies)

    for movie in filtered_movies:
        if not movie['monitored']:
            if monitor_movie(movie):
                movie['monitored'] = True
                unmonitored_count += 1

    return unmonitored_count, filtered_count

def print_summary_statement(unmonitored_count, filtered_count):
    if unmonitored_count == 0:
        print(f"{filtered_count} movies do not have the custom format \"{CUSTOM_FORMAT_NAME}\" assigned. They are already monitored.")
    else:
        print(f"{filtered_count} movies do not have the custom format \"{CUSTOM_FORMAT_NAME}\" assigned.")

    if unmonitored_count == 1:
        print(f"There was {unmonitored_count} unmonitored movie out of the {filtered_count}, it is now being monitored.")
    elif unmonitored_count > 1:
        print(f"There were {unmonitored_count} unmonitored movies out of the {filtered_count}, they are now being monitored.")


def parse_args():
    parser = argparse.ArgumentParser(description='Check and monitor movies in Radarr.')
    parser.add_argument('--unattended', type=int, metavar='N',
                        help='Run the script unattended and search for N movies at the end without user interaction.')

    return parser.parse_args()


def main():
    custom_formats = fetch_custom_formats()
    custom_format_id = find_custom_format_id(custom_formats, CUSTOM_FORMAT_NAME)

    if custom_format_id is None:
        print(f'Error: Custom format "{CUSTOM_FORMAT_NAME}" not found')
    else:
        movies = fetch_movies()
        filtered_movies = filter_movies(movies, custom_format_id)
        unmonitored_count, filtered_count = monitor_filtered_movies(filtered_movies)
        print_summary_statement(unmonitored_count, filtered_count)

        args = parse_args()

        if args.unattended is None:
            save_answer = input("Do you want to save the list of movies to not-cutoff.txt? (Y/n): ")
            search_answer = input("Do you want to search for upgrades of these movies? (Y/n): ")
            num_search = input("How many movies do you want to search? (Enter 0 to skip): ")
        else:
            save_answer = 'y'
            search_answer = 'y'
            num_search = args.unattended

        # Prompt the user to save the list of movies and search for upgraded versions
        if save_answer.lower() != 'y' and save_answer != '':
            print("Skipping saving the list of movies.")
        else:
            with open('not-cutoff.txt', 'w') as f:
                for movie in filtered_movies:
                    f.write(movie['title'] + '\n')
            print("List of movies has been saved to not-cutoff.txt")

            if search_answer.lower() == 'y' or search_answer == '':
                try:
                    num_search = int(num_search)
                except ValueError:
                    num_search = 0
                if num_search > 0:
                    with open('not-cutoff.txt') as f:
                        titles = f.readlines()
                    random_titles = random.sample(titles, num_search)
                    for title in random_titles:
                        title = title.strip()
                        movie = next((m for m in filtered_movies if m['title'] == title), None)
                        if movie is not None:
                            search_url = f'{RADARR_URL}/api/v3/command'
                            search_payload = {'name': 'MoviesSearch', 'movieIds': [movie['id']]}
                            response = requests.post(search_url, json=search_payload, params={'apiKey': API_KEY})
                            if response.status_code == 201:
                                print(f"Search for upgraded version of \"{movie['title']}\" has been triggered.")
                            else:
                                print(f"Error searching for upgraded version of \"{movie['title']}\": {response.status_code}")


if __name__ == '__main__':
    main()
