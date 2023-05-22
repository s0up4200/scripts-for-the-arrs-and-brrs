#!/usr/bin/env python3

"""
Author: soup
Description: This script looks for torrents with the noHL tag in qBittorent and checks if they match a regex pattern for either season packs or episodes. It then tags them with "noHL seasons" or "noHL episodes" or "noHL unmatched" respectively.
"""

import requests
import argparse
import re

# Add your qBittorrent Web UI credentials here or call them from the command line
# Environment variables are used by default if not specified here or on the command line
QB_URL = os.environ.get("QB_URL", "http://localhost:8080")
QB_USERNAME = os.environ.get("QB_USERNAME", "my_username")
QB_PASSWORD = os.environ.get("QB_PASSWORD", "my_password")

# Set the tags and category constants
NOHL_TAG = "noHL"  # set this to the tag that identifies your non-hardlinked torrents
CATEGORIES = "tv,4ktv,tv.cross-seed"  # the categories that you want to search for seasons and episodes in

# Set the tags that you want to add to the matching torrents
NOHL_EPISODES_TAG = "noHL episodes"
NOHL_SEASONS_TAG = "noHL seasons"
NOHL_UNMATCHED_TAG = "noHL unmatched"

# Convert the categories string into a list
CATEGORIES_LIST = [category.strip() for category in CATEGORIES.split(",")]


def has_noHL_tag(tags: str) -> bool:
    return NOHL_TAG in tags.split(",")


def has_nohl_episodes_or_seasons(tags: str) -> bool:
    tags_list = tags.split(",")
    return NOHL_EPISODES_TAG in tags_list or NOHL_SEASONS_TAG in tags_list


# Parse command line arguments
parser = argparse.ArgumentParser(
    description='This script looks for torrents with the noHL tag in qBittorent and checks if they match a regex pattern for either season packs or episodes. It then tags them with "noHL seasons" or "noHL episodes" or "noHL unmatched" respectively.'
)
parser.add_argument(
    "--seasons",
    action="store_true",
    help="Search for season packs matching the regex pattern.",
)
parser.add_argument(
    "--episodes",
    action="store_true",
    help="Search for episodes matching the regex pattern.",
)
parser.add_argument(
    "--unmatched",
    action="store_true",
    help="Tag torrents that do not match the season or episode patterns.",
)
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

#print(f"Torrents status code: {response.status_code}")
#print(f"Torrents response text: {response.text}")

print("Please wait...")

try:
    torrents = response.json()
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON.")
    torrents = []

# Add counters for each tag
nohl_seasons_count = 0
nohl_episodes_count = 0
nohl_unmatched_count = 0

# Process the torrents
total_torrents = len(torrents)
for index, torrent in enumerate(torrents):
    torrent_name = torrent["name"]

    # Check if the torrent has the "noHL" tag and belongs to one of the specified categories
    if NOHL_TAG in torrent["tags"] and any(
        category in torrent["category"] for category in CATEGORIES_LIST
    ):
        tags = torrent["tags"]
        tags_list = tags.split(",")

        updated_tags_list = tags_list.copy()

        # Check for seasons and update tags if not present
        if (
            args.seasons
            and re.match(r"(?i).*\bS\d+\b(?!E\d+\b).*", torrent_name)
            and NOHL_SEASONS_TAG not in tags_list
        ):
            updated_tags_list.append(NOHL_SEASONS_TAG)
            nohl_seasons_count += 1

        # Check for episodes and update tags if not present
        if (
            args.episodes
            and re.match(r"(?i).*\bS\d+(?=E\d+\b).*", torrent_name)
            and NOHL_EPISODES_TAG not in tags_list
        ):
            updated_tags_list.append(NOHL_EPISODES_TAG)
            nohl_episodes_count += 1

        # Check for unmatched and update tags if not present
        if (
            args.unmatched
            and not re.match(
                r"(?i)(?=.*\bS\d+\b(?!E\d+\b)|.*\bS\d+(?=E\d+\b)).*", torrent_name
            )
            and NOHL_UNMATCHED_TAG not in tags_list
        ):
            updated_tags_list.append(NOHL_UNMATCHED_TAG)
            nohl_unmatched_count += 1

        # Update tags if there are any changes
        if updated_tags_list != tags_list:
            #print(f"Processing torrent {index + 1}/{total_torrents}: {torrent['name']}")
            #print(f"Current tags: {tags}")
            session.post(
                f"{QB_URL}/api/v2/torrents/addTags",
                data={"hashes": torrent["hash"], "tags": ",".join(updated_tags_list)},
            )

# Print the summary at the end
total_processed = nohl_seasons_count + nohl_episodes_count + nohl_unmatched_count
print(f"Total torrents processed: {total_processed} out of {total_torrents}")

if args.seasons:
    print(f"Tagged {nohl_seasons_count} torrents with '{NOHL_SEASONS_TAG}'")
if args.episodes:
    print(f"Tagged {nohl_episodes_count} torrents with '{NOHL_EPISODES_TAG}'")
if args.unmatched:
    print(f"Tagged {nohl_unmatched_count} torrents with '{NOHL_UNMATCHED_TAG}'")
