#!/usr/bin/env python3

import argparse
import re
import os
import time
import requests

# Author: soup
# Description: This script looks for torrents with the noHL tag in qBittorent and checks if they match a regex pattern for either season packs or episodes.
# It then tags them with "noHL seasons" or "noHL episodes" or "noHL unmatched" respectively.


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


def delete_tags():
    tags_to_delete = []

    if args.seasons:
        tags_to_delete.append(NOHL_SEASONS_TAG)
    if args.episodes:
        tags_to_delete.append(NOHL_EPISODES_TAG)
    if args.unmatched:
        tags_to_delete.append(NOHL_UNMATCHED_TAG)

    if not tags_to_delete:
        return

    response = requests.post(
        f"{QB_URL}/api/v2/torrents/deleteTags",
        data={"tags": ",".join(tags_to_delete)},
        auth=(QB_USERNAME, QB_PASSWORD),
        verify=True,
        timeout=10.0,
    )

    if response.status_code != 200:
        print(f"Failed to delete tags: {tags_to_delete}.")


CATEGORIES_LIST = [category.strip() for category in CATEGORIES.split(",")]

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
parser.add_argument(
    "--all",
    action="store_true",
    help="Run all actions together",
)
args = parser.parse_args()

if args.all:
    args.seasons = args.episodes = args.unmatched = True

# Authenticate with qBittorrent Web UI
session = requests.Session()
auth_response = session.post(
    f"{QB_URL}/api/v2/auth/login",
    data={"username": QB_USERNAME, "password": QB_PASSWORD},
)

print(f"Auth status code: {auth_response.status_code}")
print(f"Auth response text: {auth_response.text}")

# Delete tags
delete_tags()
time.sleep(5)  # wait for tags to be deleted
print("Please wait...")

# Get the list of torrents
response = session.get(f"{QB_URL}/api/v2/torrents/info", verify=False)

try:
    torrents = response.json()
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON.")
    torrents = []

# Process the torrents
total_torrents = len(torrents)
counts = {NOHL_SEASONS_TAG: 0, NOHL_EPISODES_TAG: 0, NOHL_UNMATCHED_TAG: 0}

for index, torrent in enumerate(torrents):
    torrent_name = torrent["name"]
    tags = torrent["tags"]
    tags_list = tags.split(",")

    if NOHL_TAG not in tags_list:
        continue

    if not any(category in torrent["category"] for category in CATEGORIES_LIST):
        continue

    updated_tags_list = tags_list.copy()

    if (
        args.seasons
        and re.match(r"(?i).*\bS\d+\b(?!E\d+\b).*", torrent_name)
        and NOHL_SEASONS_TAG not in tags_list
    ):
        updated_tags_list.append(NOHL_SEASONS_TAG)
        counts[NOHL_SEASONS_TAG] += 1

    if (
        args.episodes
        and re.match(r"(?i).*\bS\d+(?=E\d+\b).*", torrent_name)
        and NOHL_EPISODES_TAG not in tags_list
    ):
        updated_tags_list.append(NOHL_EPISODES_TAG)
        counts[NOHL_EPISODES_TAG] += 1

    if (
        args.unmatched
        and not re.match(
            r"(?i)(?=.*\bS\d+\b(?!E\d+\b)|.*\bS\d+(?=E\d+\b)).*", torrent_name
        )
        and NOHL_UNMATCHED_TAG not in tags_list
    ):
        updated_tags_list.append(NOHL_UNMATCHED_TAG)
        counts[NOHL_UNMATCHED_TAG] += 1

    if updated_tags_list != tags_list:
        session.post(
            f"{QB_URL}/api/v2/torrents/addTags",
            data={"hashes": torrent["hash"], "tags": ",".join(updated_tags_list)},
        )

# Print the summary at the end
total_processed = sum(counts.values())
print(f"Total torrents processed: {total_processed} out of {total_torrents}")

if args.seasons:
    print(f"Tagged {counts[NOHL_SEASONS_TAG]} torrents with '{NOHL_SEASONS_TAG}'")
if args.episodes:
    print(f"Tagged {counts[NOHL_EPISODES_TAG]} torrents with '{NOHL_EPISODES_TAG}'")
if args.unmatched:
    print(f"Tagged {counts[NOHL_UNMATCHED_TAG]} torrents with '{NOHL_UNMATCHED_TAG}'")
