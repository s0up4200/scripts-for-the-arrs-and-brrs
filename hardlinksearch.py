import os
import csv
import sys

# looks for non-hardlinked mkv files in a directory and its subdirectories
# and saves the file paths to a csv file
# option to delete the files and any other file(s) in the same directory

def get_non_hardlinked_files(dir_path):
    non_hardlinked_files = []

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith('.mkv'):
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.stat(file_path).st_nlink == 1:
                    non_hardlinked_files.append(file_path)

    return non_hardlinked_files

def save_to_csv(non_hardlinked_files, csv_file_path):
    with open(csv_file_path, mode='w', newline='', encoding='utf-8') as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(['File Path'])

        for file_path in non_hardlinked_files:
            csv_writer.writerow([file_path])

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 hardlinksearch.py /path/to/dir")
        sys.exit(1)

    dir_path = sys.argv[1]
    csv_file_path = 'non_hardlinked_files.csv'

    non_hardlinked_files = get_non_hardlinked_files(dir_path)
    save_to_csv(non_hardlinked_files, csv_file_path)
