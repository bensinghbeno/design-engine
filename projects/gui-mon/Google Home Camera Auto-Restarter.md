# Google Home Camera Auto-Restarter

This Python script automatically monitors your Google Home camera feed in Chrome. If the feed stops and a "Live video" or "Retry" button appears, the script will automatically click it to restart the feed.

## 🚀 Setup Instructions

### 1. Install Python
If you don't have Python installed, download it from [python.org](https://www.python.org/downloads/). During installation, make sure to check the box **"Add Python to PATH"**.

### 2. Install Dependencies
Open your terminal (Command Prompt on Windows or Terminal on macOS) and run the following command:
```bash
pip install pyautogui opencv-python pillow
```

### 3. Prepare the Files
1.  Save the `google_home_monitor.py` script to a folder on your computer.
2.  In the **same folder**, save the three images you shared with me as:
    *   `ready.png` (The "Live video" button)
    *   `retry.png` (The "Retry" button)
    *   `live.png` (The live camera icon)

### 4. Run the Script
1.  Open your Google Home camera feed in Chrome and keep the window visible on your screen.
2.  Run the script from your terminal:
    ```bash
    python google_home_monitor.py
    ```
3.  The script will check the screen every 10 seconds. You can stop it at any time by pressing `Ctrl+C` in the terminal.

## 🛠 Troubleshooting
*   **Not clicking?** If the script doesn't recognize the buttons, you can adjust the `CONFIDENCE` value in the script (e.g., change `0.8` to `0.7`).
*   **Window visibility:** The Chrome window must be visible (not minimized) for the script to see and click the buttons.
*   **Multiple monitors:** If you use multiple monitors, the script might need specific configuration for `pyautogui` to look at the correct screen.
