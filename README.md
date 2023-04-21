# scripts

## hardlink-radarr.py

The point of this script is to make sure everything in Radarr is seeded in your torrent client. Whenever a torrent is deleted from the tracker, programs like [qbit_manage](https://github.com/StuffAnThings/qbit_manage) can automatically delete it from your qBittorrent instance for you.
This naturally breaks the hardlink and leaves you with a movie that is not seeded anymore.

This script checks for non-hardlinked movies in your Radarr library. When it finds a non-hardlinked movie, it deletes the file and instructs Radarr to trigger a search for the movie again.

### Usage

Add your Radarr URL and api_key to the script on line 7 and 8.

Run without deletion. Saves them to a csv file.
```bash
python3 hardlink-radarr.py /path/to/movies
```

Run and replace the amount given in the command.
```bash
python3 hardlink-radarr.py /path/to/movies --replace <amount>
```

## unwatched
wip
