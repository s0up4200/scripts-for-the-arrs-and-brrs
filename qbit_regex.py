import requests
import argparse
import re

# Set your qBittorrent Web UI URL and credentials
QB_URL = "http://127.0.0.1:10923"
QB_USERNAME = "username"
QB_PASSWORD = "password"

# Set the tags and category constants
NOHL_TAG = "noHL"  # set this to the tag that identifies your non-hardlinked torrents
CATEGORIES = "tv,4ktv,tv.cross-seed"  # the categories that you want to search for seasons and episodes in

# Set the tags that you want to add to the matching torrents
NOHL_EPISODES_TAG = "noHL episodes"
NOHL_SEASONS_TAG = "noHL seasons"
NOHL_UNMATCHED_TAG = "noHL unmatched"

# Convert the categories string into a list
CATEGORIES_LIST = [category.strip() for category in CATEGORIES.split(',')]


def has_noHL_tag(tags: str) -> bool:
    return NOHL_TAG in tags.split(',')


def has_nohl_episodes_or_seasons(tags: str) -> bool:
    tags_list = tags.split(',')
    return NOHL_EPISODES_TAG in tags_list or NOHL_SEASONS_TAG in tags_list


# Parse command line arguments
parser = argparse.ArgumentParser(description="This script looks for torrents with the noHL tag in qBittorent and checks if they match a regex pattern for either season packs or episodes. It then tags them with \"noHL seasons\" or \"noHL episodes\" respectively.")
parser.add_argument("--seasons", action="store_true", help="Search for season packs matching the regex pattern.")
parser.add_argument("--episodes", action="store_true", help="Search for episode packs matching the regex pattern.")
parser.add_argument("--unmatched", action="store_true", help="Tag torrents that do not match the season or episode patterns.")
args = parser.parse_args()

# Set the regex pattern and the tag based on the command line arguments
if args.seasons:
    regex_pattern = r"(?i).*\bS\d+\b(?!E\d+\b).*"
    tag = NOHL_SEASONS_TAG
elif args.episodes:
    regex_pattern = r"(?i).*\bS\d+(?=E\d+\b).*"
    tag = NOHL_EPISODES_TAG
elif args.unmatched:
    regex_pattern = r"(?i)(?!.*\bS\d+\b(?!E\d+\b)|.*\bS\d+(?=E\d+\b)).*"
    tag = NOHL_UNMATCHED_TAG
else:
    parser.print_help()
    exit()

# Authenticate with qBittorrent Web UI
session = requests.Session()
auth_response = session.post(
    f"{QB_URL}/api/v2/auth/login",
    data={"username": QB_USERNAME, "password": QB_PASSWORD},
)

print(f"Auth status code: {auth_response.status_code}")
print(f"Auth response text: {auth_response.text}")

# Get the list of torrents
response = session.get(f"{QB_URL}/api/v2/torrents/info", verify=False)

print(f"Torrents status code: {response.status_code}")
print(f"Torrents response text: {response.text}")

try:
    torrents = response.json()
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON.")
    torrents = []

# Process the torrents
total_torrents = len(torrents)
for index, torrent in enumerate(torrents):
    torrent_name = torrent["name"]

    # Check if the torrent matches the regex pattern, has the "noHL" tag,
    # belongs to one of the specified categories, and doesn't have both "noHL"
    # and "noHL episodes" or "noHL seasons" tags (or "noHL unmatched" for the --unmatched option)
    if (re.match(regex_pattern, torrent_name) and
        NOHL_TAG in torrent["tags"] and
        any(category in torrent["category"] for category in CATEGORIES_LIST) and
        not (has_noHL_tag(torrent["tags"]) and
             (has_nohl_episodes_or_seasons(torrent["tags"]) or (args.unmatched and NOHL_UNMATCHED_TAG in torrent["tags"])))
       ):

        tags = torrent["tags"]
        tags_list = tags.split(",")
        print(f"Processing torrent {index + 1}/{total_torrents}: {torrent['name']}")
        print(f"Current tags: {tags}")

        if tag not in tags:
            tags_list.append(tag)

        session.post(f"{QB_URL}/api/v2/torrents/addTags", data={"hashes": torrent["hash"], "tags": ",".join(tags_list)})
        print(f"Updated tags: {','.join(tags_list)}\n")

