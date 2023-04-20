# scripts

## hardlinksearch

`python3 hardlinksearch.py /path/to/dir/to/check` to just save to csv   
`python3 hardlinksearch.py /path/to/dir/to/check --delete --dry-run` with or without `--dry-run`

hardlinksearch searches for non-hardlinked mkv files in a specified dir and saves them to a csv   
optionally call with `--delete [--dry-run]` to delete the non-hardlinked files **!!!AND ANY OTHER FILE WITHING THE SAME DIR!!!**

## search_missing_radarr
search_missing_radarr triggers a search for a monitored movie that is missing (and considered to have a digital or physical release)   
call with a number to decide how many movies to search for `python3 search_missing_radarr.py 3`

## unwatched
wip
