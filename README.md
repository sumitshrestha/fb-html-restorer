# 📜 Memento Messenger

**Memento Messenger** is a digital archaeology tool designed to "resurrect" broken Facebook message archives saved years ago. 

When you save a webpage "Complete" in browsers like Firefox, the layout often breaks over time because the original CSS and JavaScript links point to servers that no longer exist. This script restores those archives by stitching together your **local saved assets** with historical files from the **Internet Archive (Wayback Machine)**.

---

## ✨ Features
* **Hybrid Rendering:** Prioritizes the images and styles you already have in your local `_files` folder.
* **Wayback Fallback:** Automatically fetches missing 2015/2016-era scripts and icons from the Internet Archive.
* **Privacy-First:** Uses environment variables for all file names and paths so no personal data is ever hardcoded into the script.
* **Style Repair:** Fixes broken inline CSS and background images (like chat bubbles and UI icons).

---

## 🚀 Getting Started

### 1. Prerequisites
Ensure you have **Python 3.8+** installed. Then, install the required parsing libraries:

```bash
pip install -r requirements.txt
```

### 2. Setup
Place your `.html` file and its corresponding `_files` folder in the same directory as `resurrect.py`.

### 3. Execution
The script uses environment variables to identify your specific archive. Set them in your terminal before running:

#### **On Windows (PowerShell):**
```powershell
$env:INPUT_HTML = "Your_Archive_Name.html"
$env:LOCAL_FILES_DIR = "Your_Archive_Name_files"
$env:WAYBACK_TIMESTAMP = "20151201"  # YYYYMMDD format

python resurrect.py
```

#### **On Linux/Mac (Bash):**
```bash
export INPUT_HTML="Your_Archive_Name.html"
export LOCAL_FILES_DIR="Your_Archive_Name_files"
export WAYBACK_TIMESTAMP="20151201"

python resurrect.py
```

---

## 🛠️ How it Works
The script performs a "Deep Scan" of your HTML file:
1.  **Local Check:** It looks for every image, script, and stylesheet in your `$LOCAL_FILES_DIR`.
2.  **Remote Patching:** If an asset is missing (common with "Save Page As" errors), it constructs a request to the Wayback Machine using your provided `$WAYBACK_TIMESTAMP`.
3.  **UI Reconstruction:** It outputs a new file (default: `resurrected_archive.html`) that combines both sources into a functional, nostalgically accurate UI.

---

## ⚖️ Disclaimer
This tool is intended for **personal archival recovery only**. It does not bypass Facebook's privacy settings or "scrape" live data; it simply repairs files that you have already saved to your local machine.

---

> *"Some conversations are worth keeping exactly as they were."*