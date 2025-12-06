import torch
import argparse
from thop import profile


def load_yolov5(pt_path):
    """Load YOLOv5 checkpoint (state_dict or full ckpt)."""
    ckpt = torch.load(pt_path, map_location="cpu")
    model = ckpt['model'] if isinstance(ckpt, dict) and 'model' in ckpt else ckpt
    model.float()
    model.eval()
    return model


def load_yolov8(pt_path):
    """Load YOLOv8 model using ultralytics API."""
    from ultralytics import YOLO
    model = YOLO(pt_path).model  # .model = pure PyTorch Arch
    model.float()
    model.eval()
    return model


def compute_gflops(model, img_size):
    dummy = torch.randn(1, 3, img_size, img_size)
    flops, params = profile(model, inputs=(dummy,), verbose=False)
    return flops / 1e9, params / 1e6  # GFLOPs, M parameters


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--yolov5", type=str, help="Path to YOLOv5 .pt model")
    parser.add_argument("--yolov8", type=str, help="Path to YOLOv8/YOLO11 .pt model")
    parser.add_argument("--imgsz", type=int, default=640, help="Image size for FLOPs")
    args = parser.parse_args()

    if not args.yolov5 and not args.yolov8:
        print("Error: Use either --yolov5 <file.pt> or --yolov8 <file.pt>")
        return

    if args.yolov5:
        print("Loading YOLOv5 model:", args.yolov5)
        model = load_yolov5(args.yolov5)
        model_type = "YOLOv5"

    elif args.yolov8:
        print("Loading YOLOv8 model:", args.yolov8)
        model = load_yolov8(args.yolov8)
        model_type = "YOLOv8/YOLO11"

    print("Model type detected:", model_type)

    try:
        gflops, params = compute_gflops(model, args.imgsz)
        print(f"Parameters: {params:.2f} M")
        print(f"GFLOPs: {gflops:.2f}")
    except Exception as e:
        print("GFLOPs calculation failed:", e)


if __name__ == "__main__":
    main()

