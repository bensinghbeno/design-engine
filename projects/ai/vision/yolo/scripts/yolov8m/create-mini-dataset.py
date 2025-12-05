#!/usr/bin/env python3
import os
import random
import shutil

# -------------------------------
# CONFIG
# -------------------------------
ROOT = "/home/ben/dev/ai/vision/datasets/coco-2017"

OUT_ROOT = "/home/ben/dev/ai/vision/datasets/coco-mini-yolo"
TRAIN_COUNT = 300
VAL_COUNT = 100

PERSON_CLASS = "0"   # YOLO class index for person


# -------------------------------
# Utility
# -------------------------------
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def get_person_images(img_dir, label_dir):
    person_imgs = []

    for fname in os.listdir(label_dir):
        if not fname.endswith(".txt"):
            continue

        label_path = os.path.join(label_dir, fname)
        with open(label_path, "r") as f:
            lines = f.readlines()

        # Check if any object is class 0 (person)
        has_person = any(line.strip().startswith(PERSON_CLASS + " ") or
                         line.strip() == PERSON_CLASS
                         for line in lines)

        if has_person:
            img_name = fname.replace(".txt", ".jpg")
            img_path = os.path.join(img_dir, img_name)
            if os.path.exists(img_path):
                person_imgs.append(img_name)
            else:
                print(f"[WARN] Missing image (skipped): {img_path}")

    print(f"Found {len(person_imgs)} person images in: {img_dir}")
    return person_imgs


def copy_subset(img_list, count, src_img_dir, src_lbl_dir, dst_img_dir, dst_lbl_dir):
    ensure_dir(dst_img_dir)
    ensure_dir(dst_lbl_dir)

    selected = random.sample(img_list, min(count, len(img_list)))

    for img_name in selected:
        lbl_name = img_name.replace(".jpg", ".txt")

        src_img = os.path.join(src_img_dir, img_name)
        src_lbl = os.path.join(src_lbl_dir, lbl_name)

        dst_img = os.path.join(dst_img_dir, img_name)
        dst_lbl = os.path.join(dst_lbl_dir, lbl_name)

        shutil.copy(src_img, dst_img)
        shutil.copy(src_lbl, dst_lbl)

    return len(selected)


# -------------------------------
# MAIN
# -------------------------------
if __name__ == "__main__":
    # Input YOLO dataset
    TRAIN_IMG_DIR = os.path.join(ROOT, "images/train")
    TRAIN_LBL_DIR = os.path.join(ROOT, "labels/train")

    VAL_IMG_DIR = os.path.join(ROOT, "images/val")
    VAL_LBL_DIR = os.path.join(ROOT, "labels/val")

    # Output dataset
    OUT_TRAIN_IMG = os.path.join(OUT_ROOT, "images/train")
    OUT_TRAIN_LBL = os.path.join(OUT_ROOT, "labels/train")

    OUT_VAL_IMG = os.path.join(OUT_ROOT, "images/val")
    OUT_VAL_LBL = os.path.join(OUT_ROOT, "labels/val")

    print("=== Scanning train for person images ===")
    train_imgs = get_person_images(TRAIN_IMG_DIR, TRAIN_LBL_DIR)
    print()

    print("=== Scanning val for person images ===")
    val_imgs = get_person_images(VAL_IMG_DIR, VAL_LBL_DIR)
    print()

    print(f"=== Creating mini train ({TRAIN_COUNT}) ===")
    n_train = copy_subset(train_imgs, TRAIN_COUNT,
                          TRAIN_IMG_DIR, TRAIN_LBL_DIR,
                          OUT_TRAIN_IMG, OUT_TRAIN_LBL)
    print(f"✔ Mini train created: {n_train} images\n")

    print(f"=== Creating mini val ({VAL_COUNT}) ===")
    n_val = copy_subset(val_imgs, VAL_COUNT,
                        VAL_IMG_DIR, VAL_LBL_DIR,
                        OUT_VAL_IMG, OUT_VAL_LBL)
    print(f"✔ Mini val created: {n_val} images\n")

    print("🎉 DONE — Mini YOLO dataset ready!")
    print(f"Output: {OUT_ROOT}")

