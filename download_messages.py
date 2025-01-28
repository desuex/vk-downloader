import os
import re
import time
import argparse

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from charset_normalizer import detect

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36"
}

def read_file_with_encoding(file_path):
    """Read a file with automatic encoding detection."""
    with open(file_path, "rb") as f:
        raw_data = f.read()
        result = detect(raw_data)
        encoding = result["encoding"]

        # Limit to UTF-8 and Windows-1251
        if encoding and encoding.lower() in ["utf-8", "windows-1251"]:
            return raw_data.decode(encoding, errors="replace"), encoding
        else:
            # Fallback to Windows-1251 if encoding is unrecognized or unsupported
            return raw_data.decode("windows-1251", errors="replace"), "windows-1251"

def extract_contact_name(soup, chat_dir):
    """Extract the contact's name from the HTML soup and add UID if "DELETED"."""
    crumbs = soup.select_one(".page_block_header_inner")
    if crumbs:
        contact_name = crumbs.find_all("div", class_="ui_crumb")[-1].text.strip()
        if contact_name == "DELETED":
            uid = os.path.basename(chat_dir)  # Get the folder name as UID
            contact_name = f"DELETED_{uid}"
        return contact_name
    return "Unknown Contact"


def parse_date_en(date_text):
    """Parse English date format."""
    try:
        return datetime.strptime(date_text, "%d %b %Y at %I:%M:%S %p")
    except ValueError:
        return None


def parse_date_ru(date_text):
    """Parse Russian date format."""
    try:
        months = {
            "янв": "Jan", "фев": "Feb", "мар": "Mar", "апр": "Apr", "мая": "May", "июн": "Jun",
            "июл": "Jul", "авг": "Aug", "сен": "Sep", "окт": "Oct", "ноя": "Nov", "дек": "Dec"
        }
        for ru, en in months.items():
            date_text = date_text.replace(ru, en)
        return datetime.strptime(date_text, "%d %b %Y в %H:%M:%S")
    except ValueError:
        return None


def extract_attachments(soup):
    """Extract attachments and their corresponding dates from the HTML soup."""
    attachments = set()
    for message in soup.select(".message, .item"):
        header = message.select_one(".message__header")
        if header:
            date_text = header.text.strip()
            # Remove sender's name if present
            if "," in date_text:
                date_text = date_text.rsplit(",", 1)[-1].strip()
            # Remove '(ред.)' if present
            date_text = re.sub(r"\(ред\.\)", "", date_text).strip()

            message_date = parse_date_en(date_text) or parse_date_ru(date_text)
            if not message_date:
                continue

            formatted_date = message_date.strftime("%Y-%m-%d %H:%M:%S")
            attachment_link = message.select_one(".attachment__link")
            if attachment_link:
                url = attachment_link["href"]
                # Skip non-image links
                if not re.search(r"\.(jpe?g|png|gif)(\?.*)?$", url, re.IGNORECASE):
                    continue
                attachments.add((url, formatted_date))
    return list(attachments)


def download_attachment(url, save_path, allowed_mime_types=None):
    """Download an attachment from a URL with MIME type validation and save it to the specified path."""
    if allowed_mime_types is None:
        allowed_mime_types = ['image/jpeg', 'image/png', 'image/gif']

    try:
        response = requests.get(url, headers=HEADERS, stream=True, timeout=10)
        if 400 <= response.status_code < 500:
            print(f"Skipping {url}: HTTP {response.status_code} - Client error, will not retry.")
            return False

        response.raise_for_status()

        # Check MIME type
        content_type = response.headers.get('Content-Type', '')
        if content_type not in allowed_mime_types:
            print(f"Skipping {url}: MIME type '{content_type}' not allowed.")
            return False

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
        print(f"Failed to download {url}: {e}")
        return False


def sanitize_filename(name):
    """Sanitize the filename to make it valid for all file systems."""
    name = re.sub(r'[<>:"/\\|?*]', '_', name)  # Replace invalid characters
    name = re.sub(r'\.+$', '', name)  # Remove trailing dots
    return name[:255]  # Limit the length to 255 characters


def download_with_retries(url, save_path, retries=3, delay=5, allowed_mime_types=None, force=False):
    """Download a file with retries if the initial attempt fails."""
    if not force and os.path.exists(save_path):
        print(f"File already exists, skipping: {save_path}")
        return True

    for attempt in range(retries):
        if download_attachment(url, save_path, allowed_mime_types=allowed_mime_types):
            return True  # Download succeeded
        print(f"Attempt {attempt + 1} failed for {url}. Retrying...")
        time.sleep(delay)
    print(f"Failed to download {url} after {retries} attempts.")
    return False


def process_chat(chat_dir, download_dir, force):
    """Process all paginated message files in a chat directory."""
    first_file = os.path.join(chat_dir, "messages0.html")
    if not os.path.exists(first_file):
        return

    soup = BeautifulSoup(read_file_with_encoding(first_file)[0], "html.parser")
    contact_name = extract_contact_name(soup, chat_dir)
    sanitized_name = sanitize_filename(contact_name)

    # Create a directory for the contact
    contact_dir = os.path.join(download_dir, sanitized_name)
    os.makedirs(contact_dir, exist_ok=True)

    # Process all paginated message files
    for filename in os.listdir(chat_dir):
        if filename.startswith("messages") and filename.endswith(".html"):
            file_path = os.path.join(chat_dir, filename)
            soup = BeautifulSoup(read_file_with_encoding(file_path)[0], "html.parser")
            attachments = extract_attachments(soup)

            # Download all attachments
            for url, date in attachments:
                file_name = sanitize_filename(f"{date}.jpg")  # Only sanitize the filename
                save_path = os.path.join(contact_dir, file_name)  # Keep the directory structure intact
                if download_with_retries(url, save_path, retries=3, delay=5,
                                         allowed_mime_types=['image/jpeg', 'image/png'], force=force):
                    print(f"File is processed successfully: {save_path}")


def main():
    """Main function to process all chat directories."""
    parser = argparse.ArgumentParser(description="Download VK message attachments.")
    parser.add_argument("--root-dir", type=str, required=True, help="Path to the root directory of VK messages.")
    parser.add_argument("--download-dir", type=str, required=True,
                        help="Path to the directory where attachments will be downloaded.")
    parser.add_argument("--force", action="store_true", help="Force re-download of existing files.")
    args = parser.parse_args()

    root_dir = args.root_dir
    download_dir = args.download_dir

    chat_dirs = [
        os.path.join(root_dir, folder)
        for folder in os.listdir(root_dir)
        if os.path.isdir(os.path.join(root_dir, folder))
    ]

    for chat_dir in chat_dirs:
        print(f"Processing chat: {chat_dir}")
        process_chat(chat_dir, download_dir, force=args.force)


if __name__ == "__main__":
    main()
