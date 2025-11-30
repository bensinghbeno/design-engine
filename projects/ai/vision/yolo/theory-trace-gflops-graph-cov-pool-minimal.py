#!/usr/bin/env python3
"""
gflops_hooks_yolov5.py

Count MACs (multiply-accumulate ops) via forward hooks for a PyTorch model (YOLOv5 .pt recommended).
Outputs:
 - total MACs
 - total FLOPs (2 * MACs)
 - total params
 - optional per-layer breakdown

Notes:
 - This uses forward hooks. It counts operations of nn.Modules (Conv2d, Linear, BatchNorm2d, Pooling, Upsample, etc.)
 - Some ops implemented via torch.nn.functional or in custom Python control flow that do not live inside nn.Module
   will not be captured. Convolutional MACs (which dominate) are captured.
"""

import argparse
import torch
import torch.nn as nn
import math
from collections import defaultdict

# ----------------------------
# FLOP / MAC calculators
# ----------------------------

def conv2d_mac(module: nn.Conv2d, inp, out):
    # MACs = N * Cout * Hout * Wout * (Cin/groups) * kernel_h * kernel_w
    # note: bias adds are negligible and excluded; FLOPs = 2 * MACs if you want raw FLOPs
    try:
        batch_size = out.shape[0]
        Cout = out.shape[1]
        Hout = out.shape[2]
        Wout = out.shape[3]
        Cin = module.in_channels
        kernel_ops = module.kernel_size[0] * module.kernel_size[1]
        groups = module.groups if module.groups is not None else 1
        macs = batch_size * Cout * Hout * Wout * (Cin // groups) * kernel_ops
        return int(macs)
    except Exception:
        return 0

def linear_mac(module: nn.Linear, inp, out):
    # MACs approx = batch_size * in_features * out_features
    try:
        batch = out.shape[0] if out.dim() >= 2 else 1
        macs = batch * module.in_features * module.out_features
        return int(macs)
    except Exception:
        return 0

def bn_mac(module: nn.modules.batchnorm._BatchNorm, inp, out):
    # BN: scale and shift ~ 2 ops per element (we count MAC-like ops here)
    try:
        elems = inp[0].numel()
        return int(elems * 2)
    except Exception:
        return 0

def relu_mac(module, inp, out):
    # elementwise compare ~ 1 op per element
    try:
        return int(inp[0].numel())
    except Exception:
        return 0

def pooling_mac(module, inp, out):
    # MaxPool/AvgPool: typically kernel_h * kernel_w - 1 comparisons per output element for max pool
    try:
        out_elems = out.numel()
        if isinstance(module, nn.AdaptiveAvgPool2d) or isinstance(module, nn.AvgPool2d):
            # average compute: kernel_size multiplications and adds -> approx kernel_ops per output
            # approximate as kernel_h * kernel_w
            k = module.kernel_size if isinstance(module.kernel_size, tuple) else (module.kernel_size, module.kernel_size)
            kernel_ops = k[0] * k[1]
            return int(out_elems * kernel_ops)
        elif isinstance(module, nn.MaxPool2d):
            k = module.kernel_size if isinstance(module.kernel_size, tuple) else (module.kernel_size, module.kernel_size)
            kernel_ops = k[0] * k[1]
            # comparisons ~ kernel_ops per output
            return int(out_elems * kernel_ops)
        else:
            return int(out_elems)  # fallback
    except Exception:
        return 0

def upsample_mac(module, inp, out):
    # Upsample (nearest/linear): approximate as zero arithmetic (or 1 op per output for interpolation)
    try:
        return int(out.numel())
    except Exception:
        return 0

def elementwise_mac(module, inp, out):
    try:
        return int(out.numel())
    except Exception:
        return 0

# Mapping module class -> MAC function
MAC_HANDLERS = {
    nn.Conv2d: conv2d_mac,
    nn.Linear: linear_mac,
    nn.BatchNorm2d: bn_mac,
    nn.BatchNorm1d: bn_mac,
    nn.ReLU: relu_mac,
    nn.SiLU: relu_mac,
    nn.LeakyReLU: relu_mac,
    nn.MaxPool2d: pooling_mac,
    nn.AvgPool2d: pooling_mac,
    nn.AdaptiveAvgPool2d: pooling_mac,
    nn.Upsample: upsample_mac,
    nn.ConvTranspose2d: conv2d_mac,
    # any other simple elementwise modules:
    nn.Dropout: lambda m, i, o: 0,
    nn.Flatten: lambda m, i, o: 0,
}

# ----------------------------
# Hook-based MAC counter
# ----------------------------

class MacCounter:
    def __init__(self):
        self.hooks = []
        self.module_macs = defaultdict(int)
        self.total_macs = 0
        self.handled_ops = set()

    def _hook(self, module, inp, out):
        # called during forward for modules that registered this hook
        macs = 0
        for mod_type, fn in MAC_HANDLERS.items():
            if isinstance(module, mod_type):
                try:
                    macs = fn(module, inp, out)
                except Exception:
                    macs = 0
                break
        # if we didn't match a handler, fallback: try to count by output elements (cheap approx)
        if macs == 0 and hasattr(out, "numel"):
            # conservative: elementwise ops (e.g., add, mul) are 1 op per element
            # But to avoid double-counting child convs inside custom modules, only apply fallback
            # if module has no children (leaf)
            if len(list(module.children())) == 0:
                macs = int(out.numel())

        # record
        if macs:
            key = module.__class__.__name__
            self.module_macs[f"{key}"].__add__(0)  # ensure key exists
            self.module_macs[f"{key}"] += int(macs)
            self.total_macs += int(macs)
            self.handled_ops.add(module.__class__.__name__)

    def register_hooks(self, model: nn.Module):
        # Register hooks on all modules (we will skip the top-level container)
        for name, module in model.named_modules():
            # ignore the top-level module (name == '')
            if name == "":
                continue
            # Only register on leaf modules (no children) to avoid double-counting
            if len(list(module.children())) == 0:
                # Register hook
                h = module.register_forward_hook(self._hook)
                self.hooks.append(h)

    def remove_hooks(self):
        for h in self.hooks:
            h.remove()
        self.hooks = []

# ----------------------------
# Utilities
# ----------------------------

def load_yolov5_model(pt_path: str, device: torch.device):
    # Load via torch.hub but avoid autoshape/wrappers. autoshape=False prevents AutoShape wrapper.
    # If using a local clone or different loader, modify accordingly.
    yolo = torch.hub.load("ultralytics/yolov5", "custom", path=pt_path, autoshape=False, force_reload=False)
    # yolo is a DetectMultiBackend-like object; core model is at yolo.model
    model_core = getattr(yolo, "model", yolo)
    model_core.to(device).eval()
    return model_core

def count_parameters(model: nn.Module):
    return sum(p.numel() for p in model.parameters())

def human_readable(n):
    # format large numbers
    if n >= 1e12:
        return f"{n/1e12:.3f} T"
    if n >= 1e9:
        return f"{n/1e9:.3f} B"
    if n >= 1e6:
        return f"{n/1e6:.3f} M"
    if n >= 1e3:
        return f"{n/1e3:.3f} K"
    return str(n)

# ----------------------------
# Main
# ----------------------------

def main():
    parser = argparse.ArgumentParser(description="Estimate MACs/FLOPs for a YOLOv5 .pt using forward-hooks")
    parser.add_argument("--pt", required=True, help="Path to YOLOv5 .pt file")
    parser.add_argument("--imgsz", type=int, default=640, help="Input image size (square). Default 640")
    parser.add_argument("--batch", type=int, default=1, help="Batch size for dummy input (default 1)")
    parser.add_argument("--detail", action="store_true", help="Print per-module-type breakdown")
    parser.add_argument("--no-cuda", action="store_true", help="Force CPU")
    args = parser.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() and not args.no_cuda else "cpu")

    print(f"\nLoading model: {args.pt}")
    model = load_yolov5_model(args.pt, device)
    total_params = count_parameters(model)
    print(f"Model loaded. Parameters: {human_readable(total_params)} ({total_params} params)")

    # Prepare dummy input
    dummy = torch.randn(args.batch, 3, args.imgsz, args.imgsz, device=device)

    # Create counter and register hooks
    counter = MacCounter()
    counter.register_hooks(model)

    # Run forward once (no grad)
    with torch.no_grad():
        try:
            # Some YOLOv5 variants expect different forward signatures; call with only img
            _ = model(dummy)
        except TypeError:
            # fallback: try passing only the tensor as first positional argument
            _ = model(dummy)

    counter.remove_hooks()

    total_macs = int(counter.total_macs)
    total_flops = total_macs * 2  # FLOPs convention: 2 * MACs (multiply + add)
    print("\n-----------------------------")
    print(f"Input size : {args.imgsz} x {args.imgsz}, batch {args.batch}")
    print(f"Total MACs : {human_readable(total_macs)} ({total_macs})")
    print(f"Total FLOPs: {human_readable(total_flops)} ({total_flops})  (FLOPs = 2 * MACs)")
    print(f"Parameters : {human_readable(total_params)} ({total_params})")
    print("-----------------------------\n")

    if args.detail:
        # print per-layer-type breakdown sorted by MACs desc
        items = sorted(counter.module_macs.items(), key=lambda x: x[1], reverse=True)
        print("Per-module-type MAC breakdown (top entries):")
        for name, mac in items[:80]:
            print(f"  {name:30s} : {human_readable(mac):>8s} ({mac})")
        if len(items) == 0:
            print("  (no module-level MACs were recorded)")

    # Inform user about limitations
    print("\nNote:")
    print(" - This method counts MACs from nn.Module leaf modules (Conv2d, Linear, BatchNorm, Pooling, Upsample, etc).")
    print(" - Some operations implemented via torch.nn.functional or custom Python ops inside forward()")
    print("   that are not part of an nn.Module will not be captured. Convolutional MACs (dominant) are counted.")
    print(" - If you want a layer-by-layer exact graph-derived count (including functional ops),")
    print("   you can try torch.fx tracing on the raw model, but some YOLO wrappers (AutoShape) cause trace errors.")
    print(" - If you want, I can produce an FX-based version that attempts to patch control-flow issues.\n")

if __name__ == "__main__":
    main()

