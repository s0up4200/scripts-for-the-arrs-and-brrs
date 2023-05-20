#!/usr/bin/env python3
##############################################################################
### NZBGET/SABNZBD POST-PROCESSING SCRIPT                                  ###
#
# Check for cross-seeds
#
# Author: Soup/Roxedus/Thezak/GPT/Gabe
#
#
# Copy script to SAB/NZBGet's script folder.
# Run sudo chmod +x xseed.py
#
#
# NOTE: This script requires Python to be installed on your system.
#
### NZBGET POST-PROCESSING SCRIPT                                          ###
##############################################################################

import os
import sys
import subprocess

# Set the data directory constant
DATA_DIR = "/path/to/your/data/dir"

# Determine if the script is running in SABnzbd or NZBGet
NZB_MODE = "sab" if os.environ.get("SAB_COMPLETE_DIR") else "get"


# Determine if the script is running in a Docker container, or bare metal
def is_running_in_docker():
    return os.path.exists("/.dockerenv")


# Get the path of the completed download
if NZB_MODE == "sab":
    completed_download_dir = os.environ.get("SAB_COMPLETE_DIR")
    completed_filename = os.environ.get("SAB_FILENAME")
    POSTPROCESS_SUCCESS = 0
    POSTPROCESS_ERROR = 1

elif NZB_MODE == "get":
    completed_download_dir = os.environ.get("NZBPP_DIRECTORY")
    completed_filename = os.environ.get("NZBPP_NZBNAME")
    POSTPROCESS_SUCCESS = 93
    POSTPROCESS_ERROR = 94

# Iterate over the files in the completed download directory
for file_name in os.listdir(completed_download_dir):
    completed_download = os.path.join(completed_download_dir, file_name)
    hardlink_path = os.path.join(DATA_DIR, file_name)

    # Create the hardlink
    if os.path.isfile(completed_download):
        os.link(completed_download, hardlink_path)

        # Run the cross-seed search
        if not is_running_in_docker():
            cross_seed_command = [
                "/home/media/.nvm/versions/node/v18.12.1/bin/cross-seed",
                "search",
                f"--data-dirs={DATA_DIR}",
                "--output-dir=.",
                "--torznab=https://localhost/prowlarr/1/api?apikey=12345",
            ]
        else:
            cross_seed_command = [
                f"docker exec cross-seed",
                "/usr/local/bin/cross-seed",
                "search",
                "--data-dirs={DATA_DIR}",
                "--output-dir=.",
                "--torznab=https://localhost/prowlarr/1/api?apikey=12345",
            ]

        result = subprocess.run(
            cross_seed_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Check for search results
        if "No cross-seeds found" in result.stdout:
            # If search results are nil, delete the hardlinked file
            os.remove(hardlink_path)
            print(f"No cross-seeds found. Removed hardlinked file: {hardlink_path}")
        else:
            print(f"Cross-seeds found for: {hardlink_path}")
    else:
        print(f"Error: {completed_download} is not a file.")
        sys.exit(POSTPROCESS_ERROR)

# Exit with a success status
sys.exit(POSTPROCESS_SUCCESS)
