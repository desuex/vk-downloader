import os
import re
import requests
from bs4 import BeautifulSoup
import time
import argparse

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}


def read_file_with_encoding(file_path):
    try:
        with open(file_path, "rb") as file:
            raw_data = file.read()
            # First, try UTF-8
            try:
                return raw_data.decode("utf-8")
            except UnicodeDecodeError:
                # Fallback to win-1251 for Russian
                return raw_data.decode("windows-1251", errors="replace")
    except Exception as e:
        print(f"Failed to read {file_path}: {e}")
        return None


def sanitize_filename(name):
    """Sanitize a filename to make it valid for all file systems."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)  # Replace invalid characters
    name = re.sub(r'\.+$', '', name)  # Remove trailing dots
    return name[:255]  # Limit the length to 255 characters


def extract_album_name(soup):
    """Extract album name from the HTML soup."""
    crumbs = soup.select_one(".page_block_header_inner")
    if crumbs:
        album_name = crumbs.find_all("div", class_="ui_crumb")[-1].text.strip()
        return sanitize_filename(album_name)
    return "Unknown Album"


def extract_images(soup):
    """Extract image URLs and alt names from the HTML soup."""
    images = []
    for img_tag in soup.find_all("img"):
        src = img_tag.get("src")
        alt = img_tag.get("alt", "unknown_image")
        if src and re.search(r"\.(jpe?g|png|gif)(\?.*)?$", src, re.IGNORECASE):
            images.append((src, alt))
    return images


def download_image(url, save_path, retries=3, delay=5):
    """Download an image from a URL with retry logic."""
    for attempt in range(retries):
        try:
            response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
            if response.status_code >= 400 and response.status_code < 500:
                print(f"Skipping {url}: HTTP {response.status_code} - Client error, will not retry.")
                return False

            response.raise_for_status()

            # Use the same extension as in the URL
            ext_match = re.search(r"\.(jpe?g|png|gif)(\?.*)?$", url, re.IGNORECASE)
            extension = ext_match.group(1) if ext_match else "jpg"
            save_path = re.sub(r"\.\w+$", f".{extension}", save_path)

            with open(save_path, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            print(f"Downloaded: {save_path}")
            return True
        except requests.exceptions.RequestException as e:
            print(f"Attempt {attempt + 1} failed for {url}: {e}")
            time.sleep(delay)
    print(f"Failed to download {url} after {retries} attempts.")
    return False


def process_album(html_file, download_dir):
    """Process a single album HTML file."""
    content = read_file_with_encoding(html_file)
    if content is None:
        return

    soup = BeautifulSoup(content, "html.parser")

    album_name = extract_album_name(soup)
    images = extract_images(soup)

    # Create a directory for the album
    album_dir = os.path.join(download_dir, album_name)
    os.makedirs(album_dir, exist_ok=True)

    # Download all images
    for src, alt in images:
        # Create a valid file name for the image
        file_name = sanitize_filename(alt) + os.path.splitext(src)[-1].split('?')[0]
        save_path = os.path.join(album_dir, file_name)
        download_image(src, save_path)


def main():
    """Main function to scan and process all album HTML files."""
    parser = argparse.ArgumentParser(description="Download VK album images.")
    parser.add_argument("--root-dir", type=str, required=True,
                        help="Path to the root directory of VK albums.")
    parser.add_argument("--download-dir", type=str, required=True,
                        help="Path to the directory where images will be downloaded.")
    args = parser.parse_args()

    root_dir = args.root_dir
    download_dir = args.download_dir

    html_files = [
        os.path.join(root_dir, file)
        for file in os.listdir(root_dir)
        if file.endswith(".html")
    ]

    for html_file in html_files:
        print(f"Processing album: {html_file}")
        process_album(html_file, download_dir)


if __name__ == "__main__":
    main()
