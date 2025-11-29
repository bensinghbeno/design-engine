from pathlib import Path
import shutil

# --- PATHS ---
SRC = Path("/home/ben/Documents/toyo/ulpc/dev/mobilenet-custom/gemini/dataset-train/2017")
DST = Path("/home/ben/dev/ai/vision/datasets/coco-2017-person")

# Create destination structure
for split in ["train", "val"]:
    (DST / "labels" / split).mkdir(parents=True, exist_ok=True)
    (DST / "images" / split).mkdir(parents=True, exist_ok=True)

# --- PROCESS LABELS + COPY IMAGES ---
for split in ["train", "val"]:

    src_labels = SRC / "labels" / split
    src_images = SRC / "images" / split

    dst_labels = DST / "labels" / split
    dst_images = DST / "images" / split

    keep_count = 0
    skip_count = 0
    image_copy_count = 0

    for label_file in src_labels.glob("*.txt"):

        lines = label_file.read_text().strip().split("\n")
        new_lines = []

        for line in lines:
            line = line.strip()

            # Skip empty/malformed lines
            if not line:
                continue

            parts = line.split()

            if len(parts) < 5:
                continue

            try:
                cls = int(parts[0])
            except ValueError:
                continue

            # PERSON ONLY (COCO class 0)
            if cls == 0:
                parts[0] = "0"
                new_lines.append(" ".join(parts))

        # If this file has person labels — keep it and copy matching image
        if new_lines:
            dst_label_path = dst_labels / label_file.name
            dst_label_path.write_text("\n".join(new_lines))
            keep_count += 1

            # Copy matching image
            img_name = label_file.stem + ".jpg"
            src_img_path = src_images / img_name
            if src_img_path.exists():
                shutil.copy(src_img_path, dst_images / img_name)
                image_copy_count += 1

        else:
            skip_count += 1

    print(f"{split}:")
    print(f"  kept label files:   {keep_count}")
    print(f"  skipped (no person): {skip_count}")
    print(f"  copied images:        {image_copy_count}")

