import requests
from datetime import datetime

"""
This script checks and monitors movies in Radarr based on a specified custom format and their availability.
It checks if a movie does not have the specified custom format assigned and if it has been physically or digitally released.
For filtered movies that are not monitored, the script updates their monitored status in Radarr.
At the end, a summary of the number of filtered movies and the unmonitored movies that have been monitored is printed.
"""

radarr_url = "http://localhost:7878/radarr" # Change this to your Radarr URL
api_key = "api_key" # Change this to your Radarr API key
custom_format_name = "HD Bluray Tier 01" # Change this to the name of the custom format you want to filter by

print(f"Checking for movies in Radarr that do not have the custom format \"{custom_format_name}\" assigned and are available...")

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
    update_url = f'{radarr_url}/api/v3/movie/{movie["id"]}?apiKey={api_key}'
    headers = {'Content-Type': 'application/json'}
    payload = movie
    payload['monitored'] = True
    response = requests.put(update_url, json=payload, headers=headers)

    if response.status_code not in [200, 202]:
        print(f"Error updating monitored status for movie ID {movie['id']}: {response.status_code}")
        return False
    return True

# Fetch custom formats
response = requests.get(f'{radarr_url}/api/v3/customformat', params={'apiKey': api_key})
if response.status_code == 200:
    custom_formats = response.json()
else:
    print(f'Error fetching custom formats: {response.status_code}')
    custom_formats = []

# Find custom_format_id for the given custom_format_name
custom_format_id = None
for custom_format in custom_formats:
    if custom_format['name'] == custom_format_name:
        custom_format_id = custom_format['id']
        break

if custom_format_id is None:
    print(f'Error: Custom format "{custom_format_name}" not found')
else:
    # Fetch movies
    response = requests.get(f'{radarr_url}/api/v3/movie', params={'apiKey': api_key})
    if response.status_code == 200:
        movies = response.json()
    else:
        print(f'Error fetching movies: {response.status_code}')
        movies = []

    filtered_movies = []
    for movie in movies:
        if not is_movie_available(movie):
            continue
        if 'movieFile' in movie:
            movie_file_response = requests.get(f'{radarr_url}/api/v3/moviefile/{movie["movieFile"]["id"]}', params={'apiKey': api_key})
            if movie_file_response.status_code == 200:
                movie_file = movie_file_response.json()
                if custom_format_id not in [format['id'] for format in movie_file.get('customFormats', [])]:
                    filtered_movies.append(movie)
            else:
                print(f'Error fetching movie file for {movie["title"]}: {movie_file_response.status_code}')
        else:
            filtered_movies.append(movie)

# Initialize counters
unmonitored_count = 0
filtered_count = len(filtered_movies)

# Monitor the titles of the filtered movies
for movie in filtered_movies:
    #print(movie['title'])
    if not movie['monitored']:
        if monitor_movie(movie):
            movie['monitored'] = True
            unmonitored_count += 1


# Print the summary statement
if unmonitored_count == 0:
    print(f"All {filtered_count} movies do not have the custom format \"{custom_format_name}\" assigned. They are already monitored.")
else:
    print(f"{filtered_count} movies do not have the custom format \"{custom_format_name}\" assigned.")

if unmonitored_count == 1:
    print(f"There was {unmonitored_count} unmonitored movie out of the {filtered_count}, it is now being monitored.")
elif unmonitored_count > 1:
    print(f"There were {unmonitored_count} unmonitored movies out of the {filtered_count}, they are now being monitored.")

answer = input("Do you want to save the list of movies to not-cutoff.txt? (Y/n): ")

if answer.lower() == 'y' or answer == '':
    with open('not-cutoff.txt', 'w') as f:
        for movie in filtered_movies:
            f.write(movie['title'] + '\n')
        print("List of movies has been saved to not-cutoff.txt")