#!/usr/bin/env python3
"""Publish the next unposted item in queue/queue.json to Instagram.

Reads IG_ACCESS_TOKEN and IG_USER_ID from the environment (set as GitHub
Actions secrets). Images are served to the Instagram Graph API via their
raw.githubusercontent.com URL, so this repo must stay public (or the token
must belong to an app with access to a private-repo proxy) for Instagram to
be able to fetch them.
"""
import json
import os
import sys
import time
from pathlib import Path

import requests

REPO = "charada123/kenzom4-instagram-"
BRANCH = "main"
QUEUE_FILE = Path("queue/queue.json")
GRAPH_HOST = "https://graph.instagram.com"
GRAPH_VERSION = "v21.0"
POLL_ATTEMPTS = 20
POLL_DELAY_SECONDS = 5


def main() -> None:
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_USER_ID"]

    if not QUEUE_FILE.exists():
        print("No queue/queue.json found, nothing to do.")
        return

    queue = json.loads(QUEUE_FILE.read_text())
    post = next((p for p in queue if not p.get("posted")), None)
    if post is None:
        print("Queue is empty or every post has already gone out. Nothing to do.")
        return

    image_url = f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/queue/images/{post['image']}"
    caption = post.get("caption", "")
    print(f"Posting {post['id']}: {image_url}")

    creation_id = _create_media_container(image_url, caption, ig_user_id, token)
    _wait_until_finished(creation_id, token)
    media_id = _publish(creation_id, ig_user_id, token)

    post["posted"] = True
    post["posted_at"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    post["media_id"] = media_id
    QUEUE_FILE.write_text(json.dumps(queue, indent=2) + "\n")
    print(f"Published post {post['id']} as media {media_id}")


def _create_media_container(image_url: str, caption: str, ig_user_id: str, token: str) -> str:
    resp = requests.post(
        f"{GRAPH_HOST}/{GRAPH_VERSION}/{ig_user_id}/media",
        data={"image_url": image_url, "caption": caption, "access_token": token},
        timeout=60,
    )
    _raise_with_body(resp)
    return resp.json()["id"]


def _wait_until_finished(creation_id: str, token: str) -> None:
    for _ in range(POLL_ATTEMPTS):
        resp = requests.get(
            f"{GRAPH_HOST}/{GRAPH_VERSION}/{creation_id}",
            params={"fields": "status_code", "access_token": token},
            timeout=30,
        )
        resp.raise_for_status()
        status = resp.json().get("status_code")
        if status == "FINISHED":
            return
        if status == "ERROR":
            print("Instagram failed to process the media container.", file=sys.stderr)
            sys.exit(1)
        time.sleep(POLL_DELAY_SECONDS)
    print("Timed out waiting for the media container to finish processing.", file=sys.stderr)
    sys.exit(1)


def _publish(creation_id: str, ig_user_id: str, token: str) -> str:
    resp = requests.post(
        f"{GRAPH_HOST}/{GRAPH_VERSION}/{ig_user_id}/media_publish",
        data={"creation_id": creation_id, "access_token": token},
        timeout=60,
    )
    _raise_with_body(resp)
    return resp.json()["id"]


def _raise_with_body(resp: requests.Response) -> None:
    if resp.ok:
        return
    print(f"Instagram API error {resp.status_code}: {resp.text}", file=sys.stderr)
    resp.raise_for_status()


if __name__ == "__main__":
    main()
