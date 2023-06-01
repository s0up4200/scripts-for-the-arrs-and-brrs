import argparse
import csv
import os
import sys

import qbittorrentapi

"""
Author: soup
Description: Script to calculate and display average ratios of torrents in categories and tags in qBittorrent client.
"""

# Requirements: pip3 install qbittorrent-api

# Add your qBittorrent Web UI credentials here or call them from the command line
# Environment variables are used by default if not specified here or on the command line
QB_URL = os.environ.get("QB_URL", "http://localhost:8080")
QB_USERNAME = os.environ.get("QB_USERNAME", "my_username")
QB_PASSWORD = os.environ.get("QB_PASSWORD", "my_password")


def login_qbittorrent_client(host, username, password):
    client = qbittorrentapi.Client(host=host, username=username, password=password)

    try:
        client.auth_log_in()
    except qbittorrentapi.LoginFailed as e:
        print(e)
        sys.exit()

    return client


def calculate_average_ratios(torrents):
    category_ratios = {}
    tag_ratios = {}

    for torrent in torrents:
        category = torrent.category
        if category not in category_ratios:
            category_ratios[category] = {"total_ratio": 0, "count": 0, "total_size": 0}

        category_ratios[category]["total_ratio"] += torrent.ratio
        category_ratios[category]["count"] += 1
        category_ratios[category]["total_size"] += torrent.size

        tags = [tag.strip() for tag in torrent.tags.split(",")] if torrent.tags else []
        for tag in tags:
            if tag not in tag_ratios:
                tag_ratios[tag] = {"total_ratio": 0, "count": 0, "total_size": 0}

            tag_ratios[tag]["total_ratio"] += torrent.ratio
            tag_ratios[tag]["count"] += 1
            tag_ratios[tag]["total_size"] += torrent.size

    sorted_categories = sorted(
        category_ratios.items(),
        key=lambda x: x[1]["total_ratio"] / x[1]["count"],
        reverse=True,
    )
    sorted_tags = sorted(
        tag_ratios.items(),
        key=lambda x: x[1]["total_ratio"] / x[1]["count"],
        reverse=True,
    )

    return sorted_categories, sorted_tags


def display_results(sorted_categories, sorted_tags, args):
    if not args.tags_only:
        print("Average Ratios and Total Size for Categories:")
        for category, data in sorted_categories:
            average_ratio = data["total_ratio"] / data["count"]
            total_size_gb = data["total_size"] / (1024**3)  # convert to GB
            if total_size_gb > 1000:
                total_size_tb = total_size_gb / 1024  # convert to TB
                print(
                    f"Category: {category}, Average Ratio: {average_ratio:.2f}, Total Size: {total_size_tb:.2f} TB"
                )
            else:
                print(
                    f"Category: {category}, Average Ratio: {average_ratio:.2f}, Total Size: {total_size_gb:.2f} GB"
                )

    if not args.categories_only:
        print("\nAverage Ratios and Total Size for Tags:")
        for tag, data in sorted_tags:
            average_ratio = data["total_ratio"] / data["count"]
            total_size_gb = data["total_size"] / (1024**3)  # convert to GB
            if total_size_gb > 1000:
                total_size_tb = total_size_gb / 1024  # convert to TB
                print(
                    f"Tag: {tag}, Average Ratio: {average_ratio:.2f}, Total Size: {total_size_tb:.2f} TB"
                )
            else:
                print(
                    f"Tag: {tag}, Average Ratio: {average_ratio:.2f}, Total Size: {total_size_gb:.2f} GB"
                )


def save_results_to_csv(sorted_categories, sorted_tags):
    filename = input("Enter the file name (without .csv extension): ") + ".csv"
    with open(filename, "w", newline="") as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(["Type", "Name", "Average Ratio", "Total Size"])

        for category, data in sorted_categories:
            average_ratio = data["total_ratio"] / data["count"]
            total_size_gb = data["total_size"] / (1024**3)  # convert to GB
            if total_size_gb > 1000:
                total_size_tb = total_size_gb / 1024  # convert to TB
                csv_writer.writerow(
                    [
                        "Category",
                        category,
                        f"{average_ratio:.2f}",
                        f"{total_size_tb:.2f} TB",
                    ]
                )
            else:
                csv_writer.writerow(
                    [
                        "Category",
                        category,
                        f"{average_ratio:.2f}",
                        f"{total_size_gb:.2f} GB",
                    ]
                )

        for tag, data in sorted_tags:
            average_ratio = data["total_ratio"] / data["count"]
            total_size_gb = data["total_size"] / (1024**3)  # convert to GB
            if total_size_gb > 1000:
                total_size_tb = total_size_gb / 1024  # convert to TB
                csv_writer.writerow(
                    ["Tag", tag, f"{average_ratio:.2f}", f"{total_size_tb:.2f} TB"]
                )
            else:
                csv_writer.writerow(
                    ["Tag", tag, f"{average_ratio:.2f}", f"{total_size_gb:.2f} GB"]
                )

    print(f"Results saved to {filename}")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Calculate the average ratio of torrents in categories and tags"
    )
    parser.add_argument(
        "--host",
        type=str,
        default=QB_URL,
        help=f"qBittorrent Web UI host (default: {QB_URL})",
    )
    parser.add_argument(
        "--username",
        type=str,
        default=QB_USERNAME,
        help=f"qBittorrent Web UI username (default: {QB_USERNAME})",
    )
    parser.add_argument(
        "--password",
        type=str,
        default=QB_PASSWORD,
        help=f"qBittorrent Web UI password (default: {QB_PASSWORD})",
    )
    parser.add_argument("--tags-only", action="store_true", help="Only export tags")
    parser.add_argument(
        "--categories-only", action="store_true", help="Only export categories"
    )
    parser.add_argument(
        "--exclude-tags", type=str, nargs="+", default=[], help="Exclude specified tags"
    )
    parser.add_argument(
        "--exclude-categories",
        type=str,
        nargs="+",
        default=[],
        help="Exclude specified categories",
    )

    return parser.parse_args()


def filter_excluded_items(sorted_items, excluded_items):
    return [item for item in sorted_items if item[0] not in excluded_items]


def main():
    args = parse_arguments()

    qbt_client = login_qbittorrent_client(args.host, args.username, args.password)
    torrents = qbt_client.torrents_info()
    sorted_categories, sorted_tags = calculate_average_ratios(torrents)

    sorted_categories = filter_excluded_items(
        sorted_categories, args.exclude_categories
    )
    sorted_tags = filter_excluded_items(sorted_tags, args.exclude_tags)

    display_results(sorted_categories, sorted_tags, args)

    save_to_csv = input(
        "\nDo you want to save the results to a CSV file? (yes/no): "
    ).lower()
    if save_to_csv == "yes":
        save_results_to_csv(sorted_categories, sorted_tags)


if __name__ == "__main__":
    main()
