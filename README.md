# Engrave it — Chrome History Search (v0.1)

A minimal Chrome extension to search your browsing history quickly.

## Features
- Search by page title or URL (case-insensitive)
- Clean results list: favicon, title, visit day, and an open-in-new-tab button
- Local processing and storage using `chrome.history` and `chrome.storage`

## Install
1. Open Chrome → More tools → Extensions
2. Enable Developer mode (top-right)
3. Click “Load unpacked” and select the `extension/` folder

## Use
1. Click the extension icon “Engrave it”
2. Type your query and press Enter or click “Chercher”
3. Click the ↗ icon to open a result in a new tab

## Permissions
- `history`, `storage`, `tabs`