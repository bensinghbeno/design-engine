import os
import sys

if (len(sys.argv) == 1):
    sys.exit('  No Arguments provided, Please provide image directory path')
else:	
	jpg_image_dir_path = sys.argv[1];

print("  Searching for jpg images in : %s"%jpg_image_dir_path);

for jpgFilePath in [doc for doc in os.listdir(jpg_image_dir_path) if doc.endswith(".jpg")]:
	print("   - %s"%jpgFilePath);
