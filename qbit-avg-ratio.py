import qbittorrentapi
import sys
import csv
import argparse

# Requirements: pip3 install qbittorrent-api

# Checks the average ratio of torrents in each category and tag
# Optionally saves the results to a CSV file

# Replace the credentials below with your qBittorrent credentials
qbt_client = qbittorrentapi.Client(host='http://localhost:web_ui_port', username='user', password='pass')

try:
    qbt_client.auth_log_in()
except qbittorrentapi.LoginFailed as e:
    print(e)
    sys.exit()

# Set up command-line arguments
parser = argparse.ArgumentParser(description='Calculate the average ratio of torrents in categories and tags')
parser.add_argument('--tags-only', action='store_true', help='Only export tags')
parser.add_argument('--categories-only', action='store_true', help='Only export categories')

args = parser.parse_args()

# Fetch all torrents
torrents = qbt_client.torrents_info()

# Create dictionaries to store the categories/tags and their respective ratios
category_ratios = {}
tag_ratios = {}

for torrent in torrents:
    # Calculate average ratio per category
    category = torrent.category
    if category not in category_ratios:
        category_ratios[category] = {'total_ratio': 0, 'count': 0}

    category_ratios[category]['total_ratio'] += torrent.ratio
    category_ratios[category]['count'] += 1

    # Calculate average ratio per tag
    tags = [tag.strip() for tag in torrent.tags.split(',')] if torrent.tags else []
    for tag in tags:
        if tag not in tag_ratios:
            tag_ratios[tag] = {'total_ratio': 0, 'count': 0}

        tag_ratios[tag]['total_ratio'] += torrent.ratio
        tag_ratios[tag]['count'] += 1

# Sort categories and tags by average ratio
sorted_categories = sorted(category_ratios.items(), key=lambda x: x[1]['total_ratio'] / x[1]['count'], reverse=True)
sorted_tags = sorted(tag_ratios.items(), key=lambda x: x[1]['total_ratio'] / x[1]['count'], reverse=True)

if not args.tags_only:
    # Display the results for categories
    print("Average Ratios for Categories:")
    for category, data in sorted_categories:
        average_ratio = data['total_ratio'] / data['count']
        print(f"Category: {category}, Average Ratio: {average_ratio:.2f}")

if not args.categories_only:
    # Display the results for tags
    print("\nAverage Ratios for Tags:")
    for tag, data in sorted_tags:
        average_ratio = data['total_ratio'] / data['count']
        print(f"Tag: {tag}, Average Ratio: {average_ratio:.2f}")

# Prompt user to save results to a CSV file
save_to_csv = input("\nDo you want to save the results to a CSV file? (yes/no): ").lower()
if save_to_csv == 'yes':
    filename = input("Enter the file name (without .csv extension): ") + ".csv"
    with open(filename, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(['Type', 'Name', 'Average Ratio'])

        for category, data in sorted_categories:
            average_ratio = data['total_ratio'] / data['count']
            csv_writer.writerow(['Category', category, f"{average_ratio:.2f}"])

        for tag, data in sorted_tags:
            average_ratio = data['total_ratio'] / data['count']
            csv_writer.writerow(['Tag', tag, f"{average_ratio:.2f}"])

    print(f"Results saved to {filename}")