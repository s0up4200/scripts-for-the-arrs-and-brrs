# scripts

## qbit-regex.py

This script searches for torrents with the `noHL` tag in qBittorrent and checks if they match a regular expression pattern for either season packs or episodes. It then tags them with `noHL seasons` or `noHL episodes` based on what argument you call the script with.

Put in your qbit credentials and tell it what `noHL tag` and categories to look for matches in:

```python
QB_URL = "http://127.0.0.1:12345"
QB_USERNAME = "username"
QB_PASSWORD = "password"

# Set the tags and category constants
NOHL_TAG = "noHL" # set this to the tag that identifies your non-hardlinked torrents
CATEGORIES = "tv,4ktv,tv.cross-seed" # the categories that you want to search for seasons and episodes in

# Set the tags that you want to add to the matching torrents
NOHL_EPISODES_TAG = "noHL episodes"
NOHL_SEASONS_TAG = "noHL seasons"
```

```bash
python3 qbit-regex.py --episodes
```

```bash
python3 qbit-regex.py --seasons
```

## hardlink-radarr.py

The point of this script is to make sure everything in Radarr is seeded in your torrent client. Whenever a torrent is deleted from the tracker, programs like [qbit_manage](https://github.com/StuffAnThings/qbit_manage) can automatically delete it from your qBittorrent instance for you.
This naturally breaks the hardlink and leaves you with a movie that is not seeded anymore.

This script checks for non-hardlinked movies in your Radarr library. When it finds a non-hardlinked movie, it deletes the file and instructs Radarr to trigger a search for the movie again.

### Usage

Add your `RADARR_URL`, `RADARR_API_KEY` and `DIR_PATH` to the script on line 7, 8 and 9.

```bash
python3 hardlink-radarr.py --help
```
    
```text
Usage: python3 hardlink-radarr.py [options]

Options:

  --replace <amount>   Replace specified amount of non-hardlinked movies
  --force              Automatically delete non-hardlinked movies without confirmation (Must be called with --replace <amount>)
  --help               Display this help text

  If no flags are specified, the script will only save non-hardlinked movies to non_hardlinked_files.csv
```

## not-cutoff-radarr.py

Add your `RADARR_URL`, `RADARR_API_KEY` and `CUSTOM_FORMAT_NAME` to the script on line 13, 14 and 15.

Attended
```bash
python3 not-cutoff-radarr.py
```

Unattended. Provide the amount of movies it should trigger a search for.
```bash
python3 not-cutoff-radarr.py --unattended <amount>
```

This script checks and monitors movies in Radarr based on a specified custom format and their availability.
It checks if a movie does not have the specified custom format assigned and if it has been physically or digitally released.
For filtered movies that are not monitored, the script updates their monitored status in Radarr.
At the end, a summary of the number of filtered movies and the unmonitored movies that have been monitored is printed.

## qBittorrent Ratio Analyzer

This script calculates the average ratio of torrents in each category and tag in qBittorrent. The results can be displayed in the console and optionally saved to a CSV file.

### Requirements

To run the script, you will need Python 3 and the qbittorrent-api library installed. You can install the library using the following command:

```bash
pip3 install qbittorrent-api
```

### Usage

Open the script file in a text editor and set your qBittorrent Web UI credentials (host, username, and password:

```python
QBITTORRENT_HOST = 'http://localhost:8080'
QBITTORRENT_USERNAME = 'my_username'
QBITTORRENT_PASSWORD = 'my_password'
```

Alternatively, you can pass these credentials as command-line arguments when running the script.

### Available command-line arguments

```
--host               qBittorrent Web UI host (default: value set in script)
--username           qBittorrent Web UI username (default: value set in script)
--password           qBittorrent Web UI password (default: value set in script)
--tags-only          Only export tags
--categories-only    Only export categories
--exclude-tags       "Tag1" "Tag2" "Tag3"
--exclude-categories "Category1" "Category2" "Category3"
```

## unwatched
wip
