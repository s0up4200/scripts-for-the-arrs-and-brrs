import csv
import os
import sys

# looks for non-hardlinked mkv files in a directory and its subdirectories
# and saves the file paths to a csv file
# option to delete the files and any other file(s) in the same directory


def get_non_hardlinked_files(dir_path):
    non_hardlinked_files = []

    for root, dirs, files in os.walk(dir_path):
        for file in files:
            if file.endswith(".mkv"):
                file_path = os.path.join(root, file)
                if os.path.isfile(file_path) and os.stat(file_path).st_nlink == 1:
                    non_hardlinked_files.append(file_path)

    return non_hardlinked_files


def save_to_csv(non_hardlinked_files, csv_file_path):
    with open(csv_file_path, mode="w", newline="", encoding="utf-8") as csv_file:
        csv_writer = csv.writer(csv_file)
        csv_writer.writerow(["File Path"])

        for file_path in non_hardlinked_files:
            csv_writer.writerow([file_path])


def delete_files(non_hardlinked_files, dry_run):
    for file_path in non_hardlinked_files:
        folder_path = os.path.dirname(file_path)
        if dry_run:
            print(f"[DRY-RUN] Would delete all files in folder: {folder_path}")
        else:
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    file_to_delete = os.path.join(root, file)
                    os.remove(file_to_delete)
                    print(f"Deleted file: {file_to_delete}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 hardlinksearch.py /path/to/dir [--delete [--dry-run]]")
        sys.exit(1)

    dir_path = sys.argv[1]
    csv_file_path = "non_hardlinked_files.csv"

    non_hardlinked_files = get_non_hardlinked_files(dir_path)
    save_to_csv(non_hardlinked_files, csv_file_path)

    if len(sys.argv) > 2 and sys.argv[2] == "--delete":
        dry_run = len(sys.argv) > 3 and sys.argv[3] == "--dry-run"
        delete_files(non_hardlinked_files, dry_run)
