# scripts

## hardlink-radarr.py

The point of this script is to make sure everything in Radarr is seeded in your torrent client. Whenever a torrent is deleted from the tracker, programs like qbit_manage can automatically delete it from your qBittorrent instance for you.
This naturally breaks the hardlink and leaves you with a movie that is not seeded anymore.

This script checks for non-hardlinked movies in your Radarr library. When it finds a non-hardlinked movie, it deletes the file and instructs Radarr to trigger a search for the movie again.

### Usage

```bash
python3 hardlink-radarr.py /path/to/movies # this saves the non-hardlinked movies to a csv file - nothing is deleted
```

```bash
python3 hardlink-radarr.py /path/to/movies --replace <amount> # this deletes the given amount of non-hardlinked movies and instructs Radarr to search for them again
```

## unwatched
wip
