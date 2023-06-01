#!/usr/bin/env python3

"""
Author: soup

This script manages torrents in qBittorrent. It identifies torrents with the noHL tag 
and checks if they align with a regex pattern for either season packs or episodes. 
Subsequently, the matching torrents are tagged as "noHL seasons", "noHL episodes", 
or "noHL unmatched", respectively.
"""

import argparse
import re
import os
import time
import requests

# Add your qBittorrent Web UI credentials here or call them from the command line
# Environment variables are used by default if not specified here or on the command line
QB_URL = os.environ.get("QB_URL", "http://localhost:8080")
QB_USERNAME = os.environ.get("QB_USERNAME", "my_username")
QB_PASSWORD = os.environ.get("QB_PASSWORD", "my_password")

NOHL_TAG = "noHL"  # set this to the tag that identifies your non-hardlinked torrents
CATEGORIES = "tv,4ktv,tv.cross-seed"  # the categories that you want to search in

# Set the tags that you want to add to the matching torrents
NOHL_EPISODES_TAG = "noHL episodes"
NOHL_SEASONS_TAG = "noHL seasons"
NOHL_UNMATCHED_TAG = "noHL unmatched"

# Regex patterns for season packs, episodes, and unmatched torrents
# Do not change these unless you know what you are doing
SEASONS_REGEX_PATTERN = r"(?i).*\bS\d+\b(?!E\d+\b).*"
EPISODES_REGEX_PATTERN = r"(?i).*\bS\d+(?=E\d+\b).*"
UNMATCHED_REGEX_PATTERN = r"(?i)(?!.*\bS\d+\b(?!E\d+\b)|.*\bS\d+(?=E\d+\b)).*"


def delete_tags():
    """
    Deletes specific tags before processing the torrents.
    This is to ensure that the torrents that are no longer
    tagged with noHL are removed from the equation.

    It only deletes the following tags:
    NOHL_EPISODES_TAG
    NOHL_SEASONS_TAG
    NOHL_UNMATCHED_TAG
    """
    tags_to_delete = []

    if args.seasons:
        tags_to_delete.append(NOHL_SEASONS_TAG)
    if args.episodes:
        tags_to_delete.append(NOHL_EPISODES_TAG)
    if args.unmatched:
        tags_to_delete.append(NOHL_UNMATCHED_TAG)

    if not tags_to_delete:
        return

    delete_response = requests.post(
        f"{QB_URL}/api/v2/torrents/deleteTags",
        data={"tags": ",".join(tags_to_delete)},
        auth=(QB_USERNAME, QB_PASSWORD),
        verify=True,
        timeout=10.0,
    )

    if delete_response.status_code != 200:
        print(f"Failed to delete tags: {tags_to_delete}.")


# Convert the categories string into a list
CATEGORIES_LIST = [category.strip() for category in CATEGORIES.split(",")]


def has_noHL_tag(tags: str) -> bool:
    return NOHL_TAG in tags.split(",")


def has_nohl_episodes_or_seasons(tags: str) -> bool:
    tags_list = tags.split(",")
    return NOHL_EPISODES_TAG in tags_list or NOHL_SEASONS_TAG in tags_list


# Parse command line arguments
parser = argparse.ArgumentParser(
    description="Script to manage noHL-tagged torrents in qBittorent, classifying them accordingly."
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

if not (args.seasons or args.episodes or args.unmatched or args.all):
    parser.print_help()
    exit()

if args.all:
    args.seasons = args.episodes = args.unmatched = True

# Set the regex pattern and the tag based on the command line arguments
if args.seasons:
    regex_pattern = SEASONS_REGEX_PATTERN
    tag = NOHL_SEASONS_TAG
elif args.episodes:
    regex_pattern = EPISODES_REGEX_PATTERN
    tag = NOHL_EPISODES_TAG
elif args.unmatched:
    regex_pattern = UNMATCHED_REGEX_PATTERN
    tag = NOHL_UNMATCHED_TAG
else:
    parser.print_help()
    exit()

session = requests.Session()  # Authenticate with qBittorrent Web UI
auth_response = session.post(
    f"{QB_URL}/api/v2/auth/login",
    data={"username": QB_USERNAME, "password": QB_PASSWORD},
)

print("Script version 1.1")
print(f"Auth status code: {auth_response.status_code}")
print(f"Auth response text: {auth_response.text}")
print("Please wait...")

delete_tags()
time.sleep(2)  # wait for tags to be deleted

# Get the list of torrents
response = session.get(f"{QB_URL}/api/v2/torrents/info", verify=False)

try:
    torrents = response.json()
except requests.exceptions.JSONDecodeError:
    print("Failed to decode JSON.")
    torrents = []

nohl_seasons_count = 0
nohl_episodes_count = 0
nohl_unmatched_count = 0

# Process the torrents
total_torrents = len(torrents)
progress_interval = 20  # Print progress every 20 torrents
for index, torrent in enumerate(
    torrents, 1
):  # Start index from 1 for user-friendly output
    torrent_name = torrent["name"]

    # Print iteration progress without creating a new line
    if index % progress_interval == 0 or index == total_torrents:
        print(f"Processing torrent {index}/{total_torrents}\r", end="")

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
            and re.match(SEASONS_REGEX_PATTERN, torrent_name)
            and NOHL_SEASONS_TAG not in tags_list
        ):
            updated_tags_list.append(NOHL_SEASONS_TAG)
            nohl_seasons_count += 1

        # Check for episodes and update tags if not present
        if (
            args.episodes
            and re.match(EPISODES_REGEX_PATTERN, torrent_name)
            and NOHL_EPISODES_TAG not in tags_list
        ):
            updated_tags_list.append(NOHL_EPISODES_TAG)
            nohl_episodes_count += 1

        # Check for unmatched and update tags if not present
        if (
            args.unmatched
            and not (
                re.match(SEASONS_REGEX_PATTERN, torrent_name)
                or re.match(EPISODES_REGEX_PATTERN, torrent_name)
            )
            and NOHL_UNMATCHED_TAG not in tags_list
        ):
            updated_tags_list.append(NOHL_UNMATCHED_TAG)
            nohl_unmatched_count += 1

        # Update tags if there are any changes
        if updated_tags_list != tags_list:
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
