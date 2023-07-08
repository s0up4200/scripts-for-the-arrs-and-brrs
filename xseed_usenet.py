#!/usr/bin/env python3
##############################################################################
### SABNZBD/NZBGET POST-PROCESSING SCRIPT                                  ###

# Check for cross-seeds
#
# Author: Soup
#
#
# Script to automate hardlinking and cross-seeding for Usenet downloads.
#
# Copy script to SAB/NZBGet's script folder.
# Run sudo chmod +x xseed_usenet.py
#
#
# NOTE: This script requires Python to be installed on your system.

### SABNZBD/NZBGET POST-PROCESSING SCRIPT                                  ###
##############################################################################

import argparse
import os
import sys
from pathlib import Path

import requests

# settings
base_path = "/home/user/Downloads/complete/"  # replace with the path where your completed Usenet downloads are stored
cross_base_url = "http://127.0.0.1:2468"  # replace with the base URL of your cross-seed instance
dest_path = "/home/user/torrents/qbittorrent/usenet/"  # replace with the path where you want to create hardlinks
cross_seed_data_path = "/home/user/torrents/qbittorrent/cross-seed-data/" # replace with the path where your cross-seed instance stores its data
unattended = False  # set to True to run without user interaction
cleanup = False # set to True to delete the files in dest_path if they are found in cross_seed_data_path

# Determine if the script is running in SABnzbd or NZBGet
NZB_MODE = "sab" if os.environ.get("SAB_COMPLETE_DIR") else "get"

# Get the path of the completed download
if NZB_MODE == "sab":
    unattended = True
    base_path = os.environ.get("SAB_COMPLETE_DIR")
    POSTPROCESS_SUCCESS = 0
    POSTPROCESS_ERROR = 1

elif NZB_MODE == "get":
    unattended = True
    base_path = os.environ.get("NZBPP_DIRECTORY")
    POSTPROCESS_SUCCESS = 93
    POSTPROCESS_ERROR = 94

else:
    POSTPROCESS_SUCCESS = 0
    POSTPROCESS_ERROR = 1


def find_files(path: Path, extensions: tuple):
    for entry in path.iterdir():
        if entry.is_file() and entry.suffix in extensions:
            yield entry
        elif entry.is_dir():
            yield from find_files(entry, extensions)


def hardlink_files(file_paths: list, dest: Path):
    for file_path in file_paths:
        dest_file = dest / file_path.name
        if not dest_file.exists():  # to prevent FileExistsError
            os.link(file_path, dest_file)
            yield dest_file


def send_webhook(url: str, directory_path: str):
    data = {"path": directory_path}
    response = requests.post(url + "/api/webhook", data=data)
    if response.status_code == 204:
        print("Trigger sent successfully.")
        if cleanup:
            cleanup_files()
            print("Cleanup successful.")
            sys.exit(POSTPROCESS_SUCCESS)
        else:
            sys.exit(POSTPROCESS_SUCCESS)
    else:
        print("Trigger failed.")
        sys.exit(POSTPROCESS_ERROR)

def cleanup_files():
    dest_path_files = os.listdir(dest_path)
    cross_seed_files = os.listdir(cross_seed_data_path)

    for dest_path_file in dest_path_files:
        if dest_path_file in cross_seed_files:
            file_path = os.path.join(dest_path, dest_path_file)
            os.remove(file_path)
            print(f"Removed {file_path}")


def user_prompt(question, default="no"):
    valid = {"yes": True, "y": True, "no": False, "n": False}
    prompt = " [Y/n] " if default == "yes" else " [y/N] "

    while True:
        print(question + prompt, end="")
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


def user_prompt_cleanup(question, default="no"):
    valid = {"yes": True, "y": True, "no": False, "n": False}
    prompt = " [Y/n] " if default == "yes" else " [y/N] "

    while True:
        print(question + prompt, end="")
        choice = input().lower()
        if default is not None and choice == "":
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            print("Please respond with 'yes' or 'no' (or 'y' or 'n').")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process some files.")
    parser.add_argument(
        "--unattended",
        action="store_true",
        help="run script without user interaction",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="delete files in dest_path if they are found in cross_seed_data_path",
    )
    args, unknown = parser.parse_known_args()
    unattended = unattended or args.unattended

    cleanup = cleanup or args.cleanup
    files = list(find_files(Path(base_path), (".mkv", ".mp4")))

    print(f"{len(files)} non-hardlinked movies found.")

    if len(files) > 0:
        if unattended:
            print("Running in unattended mode.")
        else:
            if not user_prompt("Do you want to hardlink them?", default="no"):
                files = []

        hardlinked_files = list(hardlink_files(files, Path(dest_path)))

    if unattended or user_prompt(
        f"Do you want to trigger a cross-seed search in {dest_path}?",
        default="yes",
    ):
        print(f"Triggering cross-seed search in {dest_path}")
        send_webhook(cross_base_url, dest_path)
    else:
        print("Not triggering a cross-seed search")

    if cleanup or user_prompt_cleanup(
        f"Do you want to clean up the files in {dest_path} if they are in {cross_seed_data_path}?",
        default="no",
    ):
        print(f"Cleaning up the files in {dest_path} if they are in {cross_seed_data_path}")
        cleanup_files()
    else:
        print("Not cleaning up")