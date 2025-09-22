# delete the URL from the history

import json
import os

# Define the path to the JSON file (one directory up)
base_dir = os.getcwd()
file_path = os.path.join(base_dir, "..", "history-samples", "sessions-2025-09-22T17-15-09-070Z.json")
file_path = os.path.normpath(file_path)

# Load the JSON data
with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# Remove the "url" key from each item in each session
for session in data:
    for item in session["items"]:
        if "url" in item:
            del item["url"]
        if "visit_time" in item:
            del item["visit_time"]
        if "visit_count" in item:
            del item["visit_count"]
        if "typed_count" in item:
            del item["typed_count"]

# Save the modified data back to the file (overwrite)
with open(file_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"History modified and saved to {file_path}")