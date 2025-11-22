import torch
from thop import profile

def detect_model_type(model):
    if hasattr(model, 'yaml') and 'nc' in model.yaml:
        return "YOLOv5"
    name = model.__class__.__name__.lower()
    if "efficientrep" in name or "rep" in name or "yolov6" in name:
        return "YOLOv6"
    if "yolo" in name:
        return "YOLOv8/YOLOv11"
    return "Unknown YOLO model"

def compute_gflops(model, img_size=640):
    dummy = torch.randn(1, 3, img_size, img_size)
    flops, params = profile(model, inputs=(dummy,), verbose=False)
    return flops/1e9, params/1e6  # GFLOPs, M parameters

def main(pt_path):
    print("Loading model:", pt_path)
    ckpt = torch.load(pt_path, map_location="cpu")

    model = ckpt['model'] if isinstance(ckpt, dict) and 'model' in ckpt else ckpt
    model = model.float()  # FP32

    print("Detected model type:", detect_model_type(model))

    try:
        gflops, params = compute_gflops(model)
        print(f"Parameters: {params:.2f} M")
        print(f"GFLOPs: {gflops:.2f}")
    except Exception as e:
        print("FLOP calculation failed:", e)

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--pt", type=str, required=True)
    args = parser.parse_args()
    main(args.pt)

