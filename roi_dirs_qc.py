import csv
from pathlib import Path

def roi_file_qc(roi_path):
    with open(roi_path, newline='') as f:
        for index, line in enumerate(csv.DictReader(f)):
            poly_string = line["all_points"]
            yield (index, line["Name"], roi_path, len(poly_string))


def roi_dir_qc(roi_paths):
    for roi_path in roi_paths:
        yield from roi_file_qc(roi_path)


def roi_dir_loader(roi_dir):
    yield from roi_dir_qc(
        path for path in roi_dir.iterdir() if path.is_file()
    )


def roi_dirs_loader(roi_dir_list):
    with open(roi_dir_list) as f:
        for roi_dir in f.read().splitlines():
            yield from roi_dir_loader(Path(roi_dir))


if __name__ == "__main__":
    qc = list(roi_dirs_loader("roi_dirs.txt"))
    max_chars = max(v[-1] for v in qc)
    has_max_chars = [
        f'Row #{1+v[0]} "{v[1]}" of "{v[2]}"'
        for v in qc if v[-1] == max_chars
    ]
    print(f"Longest of {len(qc)} ROIs is {max_chars} chars")
    print("\n".join(has_max_chars))
