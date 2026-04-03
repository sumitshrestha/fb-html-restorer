import os
import re
from bs4 import BeautifulSoup
from urllib.parse import unquote

# --- CONFIGURATION VIA ENVIRONMENT VARIABLES ---
# To run this, set these in your terminal first:
# $env:INPUT_HTML="your_file.html" (PowerShell)
# export INPUT_HTML="your_file.html" (Bash)

INPUT_HTML = os.getenv("INPUT_HTML", "index.html")
LOCAL_FILES_DIR = os.getenv("LOCAL_FILES_DIR", "index_files")
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "resurrected_archive.html")
TIMESTAMP = os.getenv("WAYBACK_TIMESTAMP", "20151201")


class MementoMessenger:
    def __init__(self, html_path, files_dir, timestamp):
        self.html_path = html_path
        self.files_dir = files_dir
        self.wayback_prefix = f"https://web.archive.org/web/{timestamp}id_/"
        self.fb_base = "https://www.facebook.com/"

    def repair(self):
        if not os.path.exists(self.html_path):
            print(
                f"Error: {self.html_path} not found. Ensure INPUT_HTML env var is set."
            )
            return

        print(f"--- Starting Resurrection: {self.html_path} ---")

        with open(self.html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")

        asset_tags = {"link": "href", "script": "src", "img": "src", "source": "src"}

        for tag_name, attr in asset_tags.items():
            for element in soup.find_all(tag_name):
                original_url = element.get(attr)
                if not original_url:
                    continue

                # Handle local file pathing
                clean_local_name = unquote(original_url).split("/")[-1]
                local_check_path = os.path.join(self.files_dir, clean_local_name)

                if os.path.exists(local_check_path):
                    element[attr] = f"{self.files_dir}/{clean_local_name}"
                    print(f"[Local] Kept: {clean_local_name}")
                else:
                    full_url = original_url
                    if not original_url.startswith("http"):
                        full_url = self.fb_base + original_url.lstrip("/")

                    element[attr] = self.wayback_prefix + full_url
                    print(f"[Remote] Patched: {original_url[:50]}...")

        # Fix inline styles (background images)
        for element in soup.find_all(style=True):
            style_content = element["style"]
            if "url(" in style_content:
                new_style = re.sub(
                    r'url\((["\']?)([^)]+)\1\)',
                    rf"url(\1{self.wayback_prefix}{self.fb_base}\2\1)",
                    style_content,
                )
                element["style"] = new_style

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(soup.prettify())

        print("-" * 40)
        print(f"Success! Generated: {OUTPUT_FILE}")


if __name__ == "__main__":
    bot = MementoMessenger(INPUT_HTML, LOCAL_FILES_DIR, TIMESTAMP)
    bot.repair()
