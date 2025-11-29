import json
import subprocess
from pathlib import Path
import yaml
import torch
import torch.nn as nn


# -------------------------------------------------------
# Accurate YOLOv5 FLOPs using PyTorch model graph
# -------------------------------------------------------
def compute_model_flops(weights_path, img_size):
    device = "cpu"
    dummy = torch.zeros(1, 3, img_size, img_size).to(device)

    # Load YOLOv5 model directly from weights (most accurate)
    model = torch.hub.load(
        "ultralytics/yolov5",
        "custom",
        path=weights_path,
        force_reload=False,
        device=device
    )

    model.eval()

    total_flops = 0

    def conv_flops(module, x):
        # Conv2d FLOPs = 2HW * Cin*Cout * K^2
        if isinstance(module, nn.Conv2d):
            Cin = module.in_channels
            Cout = module.out_channels
            K = module.kernel_size[0]
            H, W = x.shape[2], x.shape[3]
            return 2 * H * W * Cin * Cout * (K * K)
        return 0

    # Run forward hooks to sum FLOPs
    def hook_fn(module, inputs, outputs):
        nonlocal total_flops
        x = inputs[0]
        total_flops += conv_flops(module, x)

    hooks = []

    for m in model.modules():
        if isinstance(m, nn.Conv2d):
            hooks.append(m.register_forward_hook(hook_fn))

    # Forward pass to trigger hooks
    with torch.no_grad():
        model(dummy)

    for h in hooks:
        h.remove()

    return total_flops / 1e9  # GFLOPs


# -------------------------------------------------------
# Main execution
# -------------------------------------------------------
def main():
    # Load config JSON
    with open("config-4g.json") as f:
        cfg = json.load(f)

    print("Loaded configuration:")
    for k, v in cfg.items():
        print(f"  {k}: {v}")

    yolov5_dir = Path(cfg["yolov5_dir"])
    train_py = yolov5_dir / "train.py"
    weights = cfg["weights"]
    img_size = cfg["img"]
    target_flops = cfg.get("target_flops_g", None)

    # -------------------------------------------------------
    # FLOPs using real PyTorch graph (accurate)
    # -------------------------------------------------------
    print("\nComputing FLOPs from model graph...")
    flops_g = compute_model_flops(weights, img_size)
    print(f"Estimated FLOPs: {flops_g:.2f} GFLOPs")

    if target_flops and flops_g > target_flops:
        print(f"WARNING: Estimated FLOPs {flops_g:.2f} > target {target_flops} GFLOPs\n")

    # -------------------------------------------------------
    # Build training command
    # -------------------------------------------------------
    cmd = [
        "python", str(train_py),
        "--img", str(cfg["img"]),
        "--batch", str(cfg["batch"]),
        "--epochs", str(cfg["epochs"]),
        "--weights", cfg["weights"],
        "--device", str(cfg["device"]),
        "--data", str(cfg["data"]),
        "--cfg", str(yolov5_dir / cfg["cfg"])
    ]

    print("Launching training:")
    print(" ".join(cmd))
    subprocess.run(cmd)


if __name__ == "__main__":
    main()

