from pathlib import Path
from PIL import Image
from collections import defaultdict, Counter
import hashlib
import random
import shutil


# =========================================================
# SETTINGS
# =========================================================

RAW_DIR = Path("data/raw/archive (2)/Rice Leaf Disease Images")
OUTPUT_DIR = Path("data/processed")

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# =========================================================
# CHECK DATASET
# =========================================================

if not RAW_DIR.exists():
    print("ERROR: Dataset folder not found.")
    print("Expected:")
    print(RAW_DIR)
    exit()


class_folders = [
    folder for folder in RAW_DIR.iterdir()
    if folder.is_dir()
]

class_folders.sort()

if not class_folders:
    print("ERROR: No class folders found.")
    exit()


print("\n==========================================")
print("        LEAFSIGHT DATASET PREPARATION")
print("==========================================")

print("\nDataset location:")
print(RAW_DIR)

print("\nClasses found:")

for folder in class_folders:
    print(" -", folder.name)


# =========================================================
# COLLECT IMAGES
# =========================================================

images_by_class = defaultdict(list)

total_files = 0
corrupted = []

for class_folder in class_folders:

    class_name = class_folder.name

    for image_path in class_folder.rglob("*"):

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        total_files += 1

        try:

            with Image.open(image_path) as img:
                img.verify()

            images_by_class[class_name].append(image_path)

        except Exception:

            corrupted.append(image_path)


print("\n------------------------------------------")
print("INITIAL DATASET")
print("------------------------------------------")

print("Total images:", total_files)
print("Corrupted:", len(corrupted))


# =========================================================
# FIND EXACT DUPLICATES
# =========================================================

print("\nChecking duplicates...")

hash_to_files = defaultdict(list)

for class_name, files in images_by_class.items():

    for image_path in files:

        try:

            file_hash = hashlib.md5(
                image_path.read_bytes()
            ).hexdigest()

            hash_to_files[file_hash].append(
                (class_name, image_path)
            )

        except Exception:

            corrupted.append(image_path)


duplicate_groups = 0
duplicate_copies = 0
cross_class_duplicates = []

files_to_keep = defaultdict(list)

for file_hash, file_list in hash_to_files.items():

    classes = set(
        class_name for class_name, _ in file_list
    )

    # Same image appearing under different labels
    if len(classes) > 1:

        cross_class_duplicates.append(file_list)

        continue

    # Exact duplicate within same class
    duplicate_groups_count = len(file_list)

    if duplicate_groups_count > 1:

        duplicate_groups += 1
        duplicate_copies += duplicate_groups_count - 1

    # Keep only one copy
    class_name, image_path = file_list[0]

    files_to_keep[class_name].append(image_path)


# =========================================================
# FINAL CLEAN COUNTS
# =========================================================

clean_counts = {
    class_name: len(files)
    for class_name, files in files_to_keep.items()
}

clean_total = sum(clean_counts.values())


print("\n------------------------------------------")
print("DUPLICATE ANALYSIS")
print("------------------------------------------")

print("Duplicate groups:", duplicate_groups)
print("Duplicate copies removed:", duplicate_copies)

print(
    "Cross-class duplicate groups:",
    len(cross_class_duplicates)
)


if cross_class_duplicates:

    print("\nWARNING:")
    print(
        "Some identical images appear under different classes."
    )

    print("These groups will NOT be used.")


# =========================================================
# CLASS DISTRIBUTION
# =========================================================

print("\n------------------------------------------")
print("CLEAN CLASS DISTRIBUTION")
print("------------------------------------------")

for class_name in sorted(clean_counts):

    print(
        f"{class_name}: "
        f"{clean_counts[class_name]}"
    )

print("------------------------------------------")
print("Clean total:", clean_total)


# =========================================================
# CREATE OUTPUT DIRECTORIES
# =========================================================

if OUTPUT_DIR.exists():

    print("\nRemoving old processed dataset...")

    shutil.rmtree(OUTPUT_DIR)


for split in ["train", "val", "test"]:

    for class_name in clean_counts:

        (
            OUTPUT_DIR
            / split
            / class_name
        ).mkdir(
            parents=True,
            exist_ok=True
        )


# =========================================================
# SPLIT DATASET
# =========================================================

random.seed(SEED)

split_counts = {
    "train": Counter(),
    "val": Counter(),
    "test": Counter()
}


for class_name in sorted(files_to_keep):

    files = files_to_keep[class_name].copy()

    random.shuffle(files)

    total = len(files)

    train_end = int(total * TRAIN_RATIO)

    val_end = train_end + int(
        total * VAL_RATIO
    )

    train_files = files[:train_end]

    val_files = files[train_end:val_end]

    test_files = files[val_end:]


    # Copy training files
    for image_path in train_files:

        destination = (
            OUTPUT_DIR
            / "train"
            / class_name
            / image_path.name
        )

        shutil.copy2(
            image_path,
            destination
        )

        split_counts["train"][class_name] += 1


    # Copy validation files
    for image_path in val_files:

        destination = (
            OUTPUT_DIR
            / "val"
            / class_name
            / image_path.name
        )

        shutil.copy2(
            image_path,
            destination
        )

        split_counts["val"][class_name] += 1


    # Copy test files
    for image_path in test_files:

        destination = (
            OUTPUT_DIR
            / "test"
            / class_name
            / image_path.name
        )

        shutil.copy2(
            image_path,
            destination
        )

        split_counts["test"][class_name] += 1


# =========================================================
# FINAL REPORT
# =========================================================

print("\n==========================================")
print("          FINAL DATASET SPLIT")
print("==========================================")

for split in ["train", "val", "test"]:

    total = sum(
        split_counts[split].values()
    )

    print(
        f"\n{split.upper()}: {total} images"
    )

    for class_name in sorted(clean_counts):

        print(
            f"  {class_name}: "
            f"{split_counts[split][class_name]}"
        )


print("\n==========================================")
print("DATASET PREPARATION COMPLETE")
print("==========================================")

print("\nProcessed dataset:")
print(OUTPUT_DIR)

print("\nStructure:")

print("""
data/
├── raw/
│   └── archive (2)/
│       └── Rice Leaf Disease Images/
│
└── processed/
    ├── train/
    ├── val/
    └── test/
""")

print("Next phase: ViT + GRU")