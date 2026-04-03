import os
import re
from bs4 import BeautifulSoup
from urllib.parse import unquote, urljoin, urlparse

# --- CONFIGURATION VIA ENVIRONMENT VARIABLES ---
# To run this, set these in your terminal first:
# $env:INPUT_HTML="your_file.html" (PowerShell)
# export INPUT_HTML="your_file.html" (Bash)

INPUT_HTML = os.getenv("INPUT_HTML", "index.html")
LOCAL_FILES_DIR = os.getenv("LOCAL_FILES_DIR", "").strip()
OUTPUT_FILE = os.getenv("OUTPUT_FILE", "resurrected_archive.html")
TIMESTAMP = os.getenv("WAYBACK_TIMESTAMP", "20151201")


class MementoMessenger:
    def __init__(self, html_path, files_dir, timestamp):
        self.html_path = os.path.abspath(html_path)
        self.html_dir = os.path.dirname(self.html_path)

        html_stem = os.path.splitext(os.path.basename(self.html_path))[0]
        default_files_dir = f"{html_stem}_files"
        self.files_dir = files_dir or default_files_dir

        if os.path.isabs(self.files_dir):
            self.files_dir_path = self.files_dir
        else:
            self.files_dir_path = os.path.join(self.html_dir, self.files_dir)

        self.files_dir_exists = os.path.isdir(self.files_dir_path)
        output_name = os.path.basename(OUTPUT_FILE)
        self.output_dir = os.path.join(self.html_dir, "resurrected")
        self.output_file = os.path.join(self.output_dir, output_name)
        self.wayback_prefix = f"https://web.archive.org/web/{timestamp}id_/"
        self.fb_base = "https://www.facebook.com/"

    def _is_ignored_url(self, value):
        if not value:
            return True

        normalized = value.strip()
        if normalized.startswith("#"):
            return True

        parsed = urlparse(normalized)
        return parsed.scheme in {"data", "javascript", "mailto", "tel"}

    def _resolve_local_asset_path(self, original_url):
        parsed = urlparse(original_url)
        raw_path = unquote(parsed.path or "")
        normalized_path = raw_path.replace("\\", "/")
        normalized_path = re.sub(r"^\./", "", normalized_path)

        candidates = []

        if normalized_path:
            candidates.append(os.path.normpath(os.path.join(self.html_dir, normalized_path)))
            candidates.append(
                os.path.normpath(os.path.join(self.files_dir_path, normalized_path.lstrip("/")))
            )

            files_dir_name = os.path.basename(self.files_dir_path).replace("\\", "/")
            prefix = f"{files_dir_name}/"
            if normalized_path.startswith(prefix):
                suffix = normalized_path[len(prefix) :]
                candidates.append(os.path.normpath(os.path.join(self.files_dir_path, suffix)))
                candidates.append(os.path.normpath(os.path.join(self.html_dir, suffix)))

            basename = os.path.basename(normalized_path)
            if basename:
                candidates.append(os.path.normpath(os.path.join(self.files_dir_path, basename)))
                # Flat export fallback: assets are next to the HTML file.
                candidates.append(os.path.normpath(os.path.join(self.html_dir, basename)))

        checked = set()
        for candidate in candidates:
            if candidate in checked:
                continue
            checked.add(candidate)
            if os.path.exists(candidate):
                return candidate

        return None

    def _to_wayback_url(self, original_url):
        parsed = urlparse(original_url)
        if parsed.scheme in {"http", "https"}:
            full_url = original_url
        else:
            full_url = urljoin(self.fb_base, original_url)

        return self.wayback_prefix + full_url

    def _rewrite_asset_url(self, original_url):
        if self._is_ignored_url(original_url):
            return original_url, "Ignored"

        local_path = self._resolve_local_asset_path(original_url)
        if local_path:
            relative_asset_path = os.path.relpath(local_path, self.output_dir).replace("\\", "/")
            return relative_asset_path, "Local"

        return self._to_wayback_url(original_url), "Remote"

    def repair(self):
        if not os.path.exists(self.html_path):
            print(
                f"Error: {self.html_path} not found. Ensure INPUT_HTML env var is set."
            )
            return

        print(f"--- Starting Resurrection: {self.html_path} ---")

        with open(self.html_path, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f, "html.parser")

        if not self.files_dir_exists:
            print(
                f"[Info] Local asset folder not found at: {self.files_dir_path}. "
                "Trying flat-file fallback and Wayback recovery."
            )

        asset_tags = {"link": "href", "script": "src", "img": "src", "source": "src"}
        local_count = 0
        remote_count = 0
        ignored_count = 0

        for tag_name, attr in asset_tags.items():
            for element in soup.find_all(tag_name):
                original_url = element.get(attr)
                if not original_url:
                    continue

                rewritten_url, source = self._rewrite_asset_url(original_url)
                element[attr] = rewritten_url
                if source == "Local":
                    local_count += 1
                elif source == "Remote":
                    remote_count += 1
                else:
                    ignored_count += 1
                print(f"[{source}] {tag_name}.{attr}: {original_url[:50]}...")

        # Fix inline styles (background images)
        for element in soup.find_all(style=True):
            style_content = element["style"]
            if "url(" in style_content:
                def replace_style_url(match):
                    quote = match.group(1)
                    raw_url = match.group(2).strip().strip('"\'')
                    rewritten_url, _ = self._rewrite_asset_url(raw_url)
                    return f"url({quote}{rewritten_url}{quote})"

                new_style = re.sub(r'url\((["\']?)([^)]+)\1\)', replace_style_url, style_content)
                element["style"] = new_style

        os.makedirs(self.output_dir, exist_ok=True)

        with open(self.output_file, "w", encoding="utf-8") as f:
            f.write(str(soup))

        print("-" * 40)
        print(
            f"Asset summary -> Local: {local_count}, Remote: {remote_count}, Ignored: {ignored_count}"
        )
        if local_count == 0:
            print(
                "Warning: No local CSS/JS/image assets were found. "
                "If the page still looks broken, place the '*_files' folder next to the input HTML "
                "or put the exported asset files in the same folder as the HTML."
            )
        print(f"Success! Generated: {self.output_file}")


if __name__ == "__main__":
    bot = MementoMessenger(INPUT_HTML, LOCAL_FILES_DIR, TIMESTAMP)
    bot.repair()
