#!/usr/bin/env python3
"""Add a new post to the Instagram queue.

Usage:
    python scripts/queue_add.py <path-to-image> "<caption text>"

Copies the image into queue/images/, appends an entry to queue/queue.json,
and prints the git commands to commit and push it so the next scheduled
run picks it up.
"""
import json
import shutil
import sys
from pathlib import Path

IMAGES_DIR = Path("queue/images")
QUEUE_FILE = Path("queue/queue.json")


def main() -> None:
    if len(sys.argv) != 3:
        print(f'Usage: python {sys.argv[0]} <path-to-image> "<caption>"', file=sys.stderr)
        sys.exit(1)

    image_path = Path(sys.argv[1])
    caption = sys.argv[2]

    if not image_path.exists():
        print(f"Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    queue = json.loads(QUEUE_FILE.read_text()) if QUEUE_FILE.exists() else []

    post_id = f"{len(queue) + 1:04d}"
    dest_path = IMAGES_DIR / f"{post_id}{image_path.suffix.lower()}"
    shutil.copy(image_path, dest_path)

    queue.append(
        {
            "id": post_id,
            "image": dest_path.name,
            "caption": caption,
            "posted": False,
        }
    )
    QUEUE_FILE.write_text(json.dumps(queue, indent=2) + "\n")

    print(f"Queued post {post_id} -> {dest_path}")
    print()
    print("Commit and push to add it to the posting queue:")
    print(f"  git add {dest_path} {QUEUE_FILE}")
    print(f'  git commit -m "Queue post {post_id}"')
    print("  git push")


if __name__ == "__main__":
    main()
