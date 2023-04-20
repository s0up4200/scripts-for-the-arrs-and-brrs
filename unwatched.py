import requests
import json
import csv

def get_unwatched_titles(api_key, base_url, section_id):
    url = f"{base_url}/api/v2?apikey={api_key}&cmd=get_library_media_info&section_id={section_id}&unwatched=1"
    response = requests.get(url)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data["response"]["data"]["data"]
    else:
        print(f"Error: {response.status_code}")
        return []

def export_unwatched_titles_to_csv(unwatched_titles, file_name):
    with open(file_name, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Title", "Year", "Rating", "Content Rating"])

        for title in unwatched_titles:
            writer.writerow([
                title.get("title", ""),
                title.get("year", ""),
                title.get("rating", "N/A"),
                title.get("content_rating", "N/A")
            ])

if __name__ == "__main__":
    api_key = "<your_tautulli_api_key>"
    base_url = "<your_tautulli_base_url>"
    
    # Replace these with the correct section IDs for your movies and shows libraries
    movies_section_id = 1
    shows_section_id = 2

    unwatched_movies = get_unwatched_titles(api_key, base_url, movies_section_id)
    unwatched_shows = get_unwatched_titles(api_key, base_url, shows_section_id)

    if unwatched_movies:
        export_unwatched_titles_to_csv(unwatched_movies, "unwatched_movies.csv")
        print(f"{len(unwatched_movies)} unwatched movies have been exported to 'unwatched_movies.csv'.")
    else:
        print("No unwatched movies found.")

    if unwatched_shows:
        export_unwatched_titles_to_csv(unwatched_shows, "unwatched_shows.csv")
        print(f"{len(unwatched_shows)} unwatched shows have been exported to 'unwatched_shows.csv'.")
    else:
        print("No unwatched shows found.")
