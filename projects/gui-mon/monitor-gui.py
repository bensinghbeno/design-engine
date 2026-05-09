import pyautogui
import time
import os
import sys
import tkinter as tk

# --- Configuration ---
# Set the confidence level for image matching (0.0 to 1.0)
CONFIDENCE = 0.8 

# Paths to the button images
READY_IMG = 'ready.png'
RETRY_IMG = 'retry.png'
LIVE_IMG = 'live.png'

class VisualMonitor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw() # Hide the main window
        self.overlays = [] # List of overlay windows

    def clear_overlays(self):
        for overlay in self.overlays:
            overlay.destroy()
        self.overlays = []

    def create_overlay(self, x, y, w, h, label):
        """
        Create a transparent overlay window with a yellow outline rectangle and label text
        drawn on top. We use a transparent color for the window background so only the
        rectangle and text are visible.
        """
        overlay = tk.Toplevel(self.root)
        overlay.overrideredirect(True)  # Remove window borders
        overlay.attributes("-topmost", True)  # Always on top

        # Use a rarely-used background color as the transparent key. On platforms
        # that support it (most X11/Windows builds of Tk), this color will become
        # fully transparent so only the drawn rectangle and text are visible.
        transparent_color = "#00ff00"  # bright green unlikely to be seen in UI

        # Reserve a small area above the rectangle so the label can sit outside
        extra_top = max(18, int(min(32, h * 0.25)))
        total_h = h + extra_top

        # Move the overlay up so the extra top area sits above the original y
        overlay.geometry(f"{w}x{total_h}+{x}+{y - extra_top}")

        # Try to enable a transparent color for the window background. If it fails
        # we will fall back to a normal background but still draw only an outline
        # (explicitly set fill='' on the rectangle) and place the label above it.
        has_transparency = False
        try:
            overlay.attributes("-transparentcolor", transparent_color)
            has_transparency = True
        except Exception:
            # Older Tk builds may not support -transparentcolor. Don't set a
            # bright canvas background in that case (avoid showing a filled box).
            # We'll leave the window normal but the rectangle will have no fill.
            try:
                # make the whole window slightly transparent so overlay is less intrusive
                overlay.attributes("-alpha", 0.9)
            except Exception:
                pass

        # Canvas used to draw an outline rectangle and text on top.
        canvas_bg = transparent_color if has_transparency else overlay.cget("bg")
        canvas = tk.Canvas(overlay, width=w, height=total_h, bg=canvas_bg, highlightthickness=0)
        canvas.pack()

        # Draw rectangle outline (explicitly no fill) — use yellow for the bounding box
        padding = max(2, int(min(w, h) * 0.03))  # small padding so border isn't flush to edges
        canvas.create_rectangle(padding, extra_top + padding, w - padding, extra_top + h - padding,
                                outline="yellow", fill="", width=4)

        # Draw label text above the rectangle (outside the box), centered in the
        # reserved top area so it doesn't overlap the rectangle itself.
        canvas.create_text(w // 2, extra_top // 2, text=label, fill="white",
                           font=("Arial", 12, "bold"))

        self.overlays.append(overlay)
        self.root.update()

    def check_and_highlight(self):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] Monitoring screen...")
        self.clear_overlays()
        
        found_any = False

        # 1. Check for LIVE icon
        try:
            live_icon = pyautogui.locateOnScreen(LIVE_IMG, confidence=CONFIDENCE)
            if live_icon:
                print("  - [LIVE] detected.")
                self.create_overlay(live_icon.left, live_icon.top, live_icon.width, live_icon.height, "LIVE")
                found_any = True
        except (pyautogui.ImageNotFoundException, Exception):
            pass

        # 2. Check for READY button
        try:
            ready_btn = pyautogui.locateOnScreen(READY_IMG, confidence=CONFIDENCE)
            if ready_btn:
                print("  - [READY] button detected.")
                self.create_overlay(ready_btn.left, ready_btn.top, ready_btn.width, ready_btn.height, "READY")
                found_any = True
        except (pyautogui.ImageNotFoundException, Exception):
            pass

        # 3. Check for RETRY button
        try:
            retry_btn = pyautogui.locateOnScreen(RETRY_IMG, confidence=CONFIDENCE)
            if retry_btn:
                print("  - [RETRY] button detected.")
                self.create_overlay(retry_btn.left, retry_btn.top, retry_btn.width, retry_btn.height, "RETRY")
                found_any = True
        except (pyautogui.ImageNotFoundException, Exception):
            pass

        if not found_any:
            print("  - No relevant graphics found.")

    def run(self):
        print("==================================================")
        print("Google Home Visual Monitor (No Clicking)")
        print("==================================================")
        print("Press Ctrl+C in terminal to stop.")
        
        # Verify image files exist
        for img in [READY_IMG, RETRY_IMG, LIVE_IMG]:
            if not os.path.exists(img):
                print(f"ERROR: Image file '{img}' not found.")
                sys.exit(1)

        try:
            while True:
                self.check_and_highlight()
                # Keep the overlays visible for a few seconds before the next check
                for _ in range(50): # 5 seconds (50 * 0.1s)
                    self.root.update()
                    time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nMonitor stopped by user.")
            self.root.destroy()

if __name__ == "__main__":
    monitor = VisualMonitor()
    monitor.run()
