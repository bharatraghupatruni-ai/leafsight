from pathlib import Path
from PIL import Image
import hashlib
from collections import Counter

# Dataset location
DATASET_DIR = Path("data/raw/archive (2)")

# Image extensions
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

class_counts = Counter()
image_hashes = {}
corrupted_images = []
dimensions = Counter()

total_images = 0

print("\n========== LEAFSIGHT DATASET AUDIT ==========\n")

# Go through each class folder
for class_folder in sorted(DATASET_DIR.iterdir()):

    if not class_folder.is_dir():
        continue

    class_name = class_folder.name

    for image_path in class_folder.rglob("*"):

        if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        total_images += 1
        class_counts[class_name] += 1

        try:
            # Open image
            with Image.open(image_path) as img:
                img.verify()

            # Open again to get details
            with Image.open(image_path) as img:
                dimensions[img.size] += 1

                # Create image hash
                image_bytes = image_path.read_bytes()
                image_hash = hashlib.md5(image_bytes).hexdigest()

            # Store duplicate information
            if image_hash in image_hashes:
                image_hashes[image_hash].append(str(image_path))
            else:
                image_hashes[image_hash] = [str(image_path)]

        except Exception:
            corrupted_images.append(str(image_path))


# -----------------------------
# RESULTS
# -----------------------------

print("TOTAL IMAGES:", total_images)

print("\nCLASS DISTRIBUTION")
print("------------------")

for class_name, count in class_counts.items():
    print(f"{class_name}: {count}")


# Duplicate images
duplicate_groups = {
    h: paths
    for h, paths in image_hashes.items()
    if len(paths) > 1
}

duplicate_files = sum(len(paths) - 1 for paths in duplicate_groups.values())

print("\nDUPLICATES")
print("----------")
print("Duplicate groups:", len(duplicate_groups))
print("Duplicate copies:", duplicate_files)


# Corrupted images
print("\nCORRUPTED IMAGES")
print("----------------")
print("Count:", len(corrupted_images))

if corrupted_images:
    for path in corrupted_images[:20]:
        print(path)


# Image dimensions
print("\nIMAGE DIMENSIONS")
print("----------------")

for size, count in dimensions.most_common(15):
    print(f"{size}: {count}")


print("\n============================================")
print("AUDIT COMPLETE")
print("============================================")