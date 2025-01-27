# VK Downloader
[Инструкция и описание на русском языке](https://github.com/desuex/vk-downloader/blob/main/README_RU.md)

A set of Python scripts to extract and download data from a VK archive without requiring any authentication data or API tokens. These scripts process locally downloaded HTML files from your exported VK archive.

## Overview

This repository includes:

1. **VK Message Attachments Downloader (`download_messages.py`)**: Downloads image attachments from your VK messages.
2. **VK Photo Albums Downloader (`download_albums.py`)**: Downloads all images from your VK photo albums.

---

## Features

### Common Features
- **No Authentication Required**: No API keys, tokens, or login credentials needed.
- **Custom User-Agent**: Mimics a modern browser to avoid detection.
- **Retry Logic**: Retries downloads in case of temporary issues.
- **Validation**: Skips invalid URLs, unsupported MIME types, and files that already exist (unless forced).

### VK Message Attachments Downloader
- Processes message attachments and organizes them by contact name.
- Handles paginated message files and skips non-image links.

### VK Photo Albums Downloader
- Extracts and downloads all images from VK photo albums.
- Organizes images by album name.

---

## Prerequisites

### How to Get Your VK Archive
Follow these steps to download your VK data:
1. **Request your archive**:
   - Go to **Settings → Privacy → Download your data** ([Direct Link](https://vk.com/data_protection?section=rules&scroll_to_archive=1)).
   - Select the data types to include (e.g., messages, photos).
   - Confirm the request.
2. **Wait for the archive to be prepared**:
   - This may take a few days, depending on the amount of data requested.
3. **Download your archive**:
   - Follow the link provided in your VK messages.
   - Save and extract the `.zip` file to your computer.

---

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/desuex/vk-downloader.git
   cd vk-downloader
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Usage

### VK Message Attachments Downloader

```bash
python download_messages.py --root-dir <PATH_TO_MESSAGES> --download-dir <PATH_TO_OUTPUT> [--force]
```

- **`--root-dir`**: Path to the `messages` directory in your VK archive.
- **`--download-dir`**: Directory where message attachments will be saved.
- **`--force`**: (Optional) Force re-download of existing files.

#### Example:
```bash
python download_messages.py --root-dir "./VK Archive/messages" --download-dir "./downloads/messages"
```

---

### VK Photo Albums Downloader

```bash
python download_albums.py --root-dir <PATH_TO_ALBUMS> --download-dir <PATH_TO_OUTPUT>
```

- **`--root-dir`**: Path to the `photo-albums` directory in your VK archive.
- **`--download-dir`**: Directory where album images will be saved.

#### Example:
```bash
python download_albums.py --root-dir "./VK Archive/photos/photo-albums" --download-dir "./downloads/albums"
```

---

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`:
  ```plaintext
  requests~=2.32.3
  bs4~=4.12.3
  beautifulsoup4~=4.12.3
  charset-normalizer~=3.3.2
  ```


---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---