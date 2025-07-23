import sys
sys.path.append("/home/ben/.local/lib/python3.8/site-packages")

import cv2
import insightface
import numpy as np
import os

if len(sys.argv) != 2:
    print("Usage: python3 register_face.py <path_to_image>")
    sys.exit(1)

image_path = sys.argv[1]

if not os.path.exists(image_path):
    print(f"❌ File not found: {image_path}")
    sys.exit(1)

# Load image
img = cv2.imread(image_path)
if img is None:
    print("❌ Failed to load image.")
    sys.exit(1)

# Load InsightFace model
model = insightface.app.FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
model.prepare(ctx_id=0)

# Detect face
faces = model.get(img)
if not faces:
    print("❌ No face found in image.")
    sys.exit(1)

# Take first face and get embedding
embedding = faces[0].embedding
np.save("my_face_embedding.npy", embedding)
print("✅ Face registered and embedding saved to 'my_face_embedding.npy'")
