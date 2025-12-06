import json
import subprocess
from pathlib import Path
import yaml

# -----------------------------
# Load config
# -----------------------------
with open("config-1g.json") as f:
    cfg = json.load(f)

# Print all values loaded from the JSON file
print("Loaded configuration:")
for key, value in cfg.items():
    print(f"  {key}: {value}")

yolov5_dir = Path(cfg["yolov5_dir"])
train_py = yolov5_dir / "train.py"
cfg_yaml = yolov5_dir / cfg["cfg"]

img_size = cfg["img"]
target_flops = cfg.get("target_flops_g", None)

# -----------------------------
# Estimate FLOPs from YAML
# -----------------------------
# Read model YAML
with open(cfg_yaml) as f:
    model_yaml = yaml.safe_load(f)

# Simple conv-based FLOPs estimate
total_flops = 0
for layer in model_yaml.get('backbone', []) + model_yaml.get('head', []):
    # Only consider Conv2d layers with [from, number, module, args]
    if len(layer) >= 4 and layer[2].lower().startswith('conv'):
        args = layer[3]
        # Basic extraction: [out_channels, kernel_size, stride, ...]
        Cout = args[0]
        K = args[1] if len(args) > 1 else 1
        Cin = args[2] if len(args) > 2 else Cout  # fallback
        H_out = W_out = img_size  # approximate
        flops = H_out * W_out * Cout * (K * K * Cin) * 2
        total_flops += flops

total_flops_g = total_flops / 1e9
print(f"Estimated FLOPs: {total_flops_g:.2f} GFLOPs")
if target_flops and total_flops_g > target_flops:
    print(f"WARNING: Estimated FLOPs {total_flops_g:.2f} > target {target_flops} GFLOPs")

# -----------------------------
# Build train.py command
# -----------------------------
cmd = [
    "python", str(train_py),
    "--img", str(cfg["img"]),
    "--batch", str(cfg["batch"]),
    "--epochs", str(cfg["epochs"]),
    "--weights", cfg["weights"],   # local .pt or hub name
    "--device", str(cfg["device"]),
    "--data", str(cfg["data"]),
    "--cfg", str(cfg_yaml)
]

# -----------------------------
# Launch training
# -----------------------------
print(f"Launching training:\n{' '.join(cmd)}")
subprocess.run(cmd)

