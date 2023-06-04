#!/usr/bin/env python3

import logging
import logging.handlers
import os
import sys
import time

import requests

# Set your Sonarr API key and base URL
api_key = 'YOUR_API_KEY'
base_url = 'http://localhost:8989/api/v3'

# Set the number of requests per second to limit the script to (set to 0 to disable the rate limit **No warranty is provided for this)
requests_per_second = 1

# Set the maximum number of retries and the timeout for each request
max_retries = 3
timeout = 30

# Set up logging with file rotation
log_file = 'sonarr_tag_nohl.log'
max_bytes = 1048576
backup_count = 50
handler = logging.handlers.RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logging.getLogger('').addHandler(handler)
logging.getLogger('').setLevel(logging.INFO)
# Add a StreamHandler to print all logging messages to the screen
stream_handler = logging.StreamHandler()
stream_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s'))
logging.getLogger('').addHandler(stream_handler)

# Define a function to make GET requests with retries and timeout
def make_get_request(url, headers=None):
    for i in range(max_retries):
        try:
            response = requests.get(url, headers=headers, timeout=timeout)
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as ex:
            logging.warning(f'GET request failed ({ex}), retrying ({i+1}/{max_retries})...')
    logging.error(f'GET request failed after {max_retries} retries, exiting script')
    exit(1)

# Define a function to make PUT requests with retries and timeout
def make_put_request(url, headers=None, json=None):
    for i in range(max_retries):
        try:
            response = requests.put(url, headers=headers, json=json, timeout=timeout)
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as ex:
            logging.warning(f'PUT request failed ({ex}), retrying ({i+1}/{max_retries})...')
    logging.error(f'PUT request failed after {max_retries} retries, exiting script')
    exit(1)

# Define a function to make POST requests with retries and timeout
def make_post_request(url, headers=None, json=None):
    for i in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=json, timeout=timeout)
            response.raise_for_status()
            return response
        except (requests.exceptions.Timeout, requests.exceptions.HTTPError) as ex:
            logging.warning(f'POST request failed ({ex}), retrying ({i+1}/{max_retries})...')
    logging.error(f'POST request failed after {max_retries} retries, exiting script')
    exit(1)

# Define a function to get all tags from Sonarr and create a dictionary mapping tag labels to tag IDs
def get_tag_map():
    tags = make_get_request(f'{base_url}/tag', headers={'X-Api-Key': api_key}).json()
    tag_map = {tag['label']: tag['id'] for tag in tags}
    return tag_map

# Define a function to check for the requred tags and add the required tags to sonarr if they are not in the tag_map
def check_tag(tag_map):
    required_tags = ["hardlinked", "nohl"]
    for tag in required_tags:
        if tag not in tag_map:
            logging.info(f'Tag {tag} does not exist, creating it.')
            new_tag = make_post_request(f'{base_url}/tag', headers={'X-Api-Key': api_key}, json={'label': tag}).json()
            tag_map[new_tag['label']] = new_tag['id']

# Define a function to get all series from Sonarr
def get_series():
    series = make_get_request(f'{base_url}/series', headers={'X-Api-Key': api_key}).json()
    return series

# Define a function to get all episodes for a series
def get_episodes(series_id):
    episodes = make_get_request(f'{base_url}/episode?seriesId={series_id}', headers={'X-Api-Key': api_key}).json()
    return episodes

# Define a function to check if a file is hardlinked
def is_hardlinked(file_path):
    try:
        is_hardlinked = os.stat(f'{file_path}').st_nlink
        if is_hardlinked == 1:
            return False
        else:
            return True
    except OSError:
        logging.error(f'Error checking file {file_path}: could not determine if file is hardlinked')
        exit(1)

def show_help():
    help_text = """Usage: python3 hardlink-radarr.py [options]

Options:

  --recheck            Recheck all series, even those already tagged as "hardlinked" or "nohl"
  --help               Display this help text
  
  If no flags are specified, the script will only check shows that do not have the "hardlinked" or "nohl" tags
"""
    print(help_text)

# Define a function to tag a series as "hardlinked" or "nohl"
def tag_series(series_id, tag_id):
    make_put_request(f'{base_url}/series/editor', headers={'X-Api-Key': api_key}, json={'seriesIds': [series_id], 'tags': [tag_id], 'applyTags': 'add'})
    
def untag_series(series_id, tag_id):
    make_put_request(f'{base_url}/series/editor', headers={'X-Api-Key': api_key}, json={'seriesIds': [series_id], 'tags': [tag_id], 'applyTags': 'remove'})

if __name__ == "__main__":

    if "--help" in sys.argv:
        show_help()
        sys.exit(0)

    recheck = False
    if "--recheck" in sys.argv:
        recheck = True

    # Get a list of all tags from Sonarr
    logging.info('-------- Starting --------')
    logging.info('Getting list of tags from Sonarr')
    tag_map = get_tag_map()
    check_tag(tag_map)
    
    # Get a list of all series from Sonarr
    logging.info('Getting list of series from Sonarr')
    series = get_series()
    
    # Loop through each series and check if the files are hardlinked
    for s in series:
    
        # Check if the series has the "hardlinked" or "nohl" tag
        tags = []
        if isinstance(s['tags'], list):
            for tag_id in s['tags']:
                tag_label = next((tag['label'] for tag in tags if tag['id'] == tag_id), None)
                if tag_label:
                    tags.append(tag_label.lower())
        if recheck == True:
                logging.info(f'Series {s["title"]} already has "hardlinked" or "nohl" tag, rechecking')
        else:    
            if tag_map['hardlinked'] in s['tags'] or tag_map['nohl'] in s['tags']:
                logging.info(f'Series {s["title"]} already has "hardlinked" or "nohl" tag, skipping')
                continue
    
        # Get the series's path
        path = s['path']
        logging.info(f'Checking series {s["title"]} at path {path}')
    
        # Get the list of episodes for the series
        logging.info(f'Getting list of episodes for series {s["title"]}')
        episodes = get_episodes(s['id'])
    
        # Check if the series has any downloaded episodes
        if all(episode['episodeFileId'] == 0 for episode in episodes):
            logging.info(f'series {s["title"]} has no downloaded episodes, skipping')
            continue
    
        # Loop through each episode and check if the file is hardlinked
        all_hardlinked = True
        for e in episodes:
    
            # Check if the episode has an associated file
            if e['episodeFileId'] == 0:
                logging.info(f'Episode {e["title"]} has no associated file, skipping')
                continue
    
            # Get the episode file ID
            episode_file_id = e['episodeFileId']
    
            # Get the file path for the episode
            episode_file = make_get_request(f'{base_url}/episodefile/{episode_file_id}', headers={'X-Api-Key': api_key}).json()
            file_path = episode_file['path']
            logging.info(f'Checking file {file_path} for series {s["title"]}')
    
            # Check if the file is hardlinked
            if not is_hardlinked(file_path):
                logging.info(f'Episode {e["title"]} is hardlinked')
                all_hardlinked = False
                break
    
            # Wait for the specified number of seconds before making the next request
            if requests_per_second >= 1:
                time.sleep(1 / requests_per_second)
            
        # If all files are hardlinked, tag the series as "hardlinked"
        # Apply the "hardlinked" or "nohl" tag to the series
        if all_hardlinked:
            logging.info(f'All files for series {s["title"]} are hardlinked')
            if tag_map['nohl'] in s['tags']:
                logging.info(f'Removing "nohl" tag from series {s["title"]}')
                untag_series(s['id'], tag_map['nohl'])
            logging.info(f'Adding "hardlinked" tag to series {s["title"]}')
            tag_series(s['id'], tag_map['hardlinked'])
        elif not all_hardlinked:
            logging.info(f'File {file_path} for series {s["title"]} is not hardlinked')
            if tag_map['hardlinked'] in s['tags']:
                logging.info(f'Removing "hardlinked" tag from series {s["title"]}')
                untag_series(s['id'], tag_map['hardlinked'])
            logging.info(f'Adding "nohl" tag to series {s["title"]}')
            tag_series(s['id'], tag_map['nohl'])
        else:
            logging.error(f'Failed to tag series {s["title"]}. Exiting')
            exit(1)

        # Go to next series
        logging.info('--------Next--------')

    # We done bois
    logging.info('--------Complete--------')