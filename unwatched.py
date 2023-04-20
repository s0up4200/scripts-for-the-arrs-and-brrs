import requests
import json
import csv

# Get the unwatched titles from Tautulli and export them to a CSV file.

def get_unwatched_titles(api_key, base_url):
    url = f"{base_url}/api/v2?apikey={api_key}&cmd=get_library_media_info&section_id=1&unwatched=1"
    response = requests.get(url)

    if response.status_code == 200:
        data = json.loads(response.text)
        return data["response"]["data"]["data"]
    else:
        print(f"Error: {response.status_code}")
        return []

def export_unwatched_titles_to_csv(unwatched_titles, file_name="unwatched_titles.csv"):
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
    api_key = "api_key"
    base_url = "http://127.0.0.1:8181/tautulli"
    
    unwatched_titles = get_unwatched_titles(api_key, base_url)

    if unwatched_titles:
        export_unwatched_titles_to_csv(unwatched_titles)
        print(f"{len(unwatched_titles)} unwatched titles have been exported to 'unwatched_titles.csv'.")
    else:
        print("No unwatched titles found.")
