#!/usr/bin/env python3
"""Build a daily digest of top/recent posts under niche hashtags.

Reads IG_ACCESS_TOKEN and IG_USER_ID from the environment. Uses the official
Instagram Graph API hashtag-search endpoints (ig_hashtag_search + top_media /
recent_media) to surface posts worth looking at. This only reads public post
metadata — it never likes, comments, follows, or posts anything on another
account. A human (you) decides what to engage with from the digest.

Note: the hashtag endpoints require the "Instagram Public Content Access"
permission, which needs Meta App Review. If the app doesn't have it yet,
each hashtag will fail with a permission error below instead of silently
returning nothing, so it's obvious what's blocking it.
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

GRAPH_HOST = "https://graph.instagram.com"  # test: does hashtag search exist on the instagram-login host?
GRAPH_VERSION = "v21.0"
DIGEST_DIR = Path("digests")
POSTS_PER_HASHTAG = 10

HASHTAGS = [
    "bmw",
    "bmwm",
    "bmwm4",
    "m4",
    "dragrace",
    "streetrace",
]

FIELDS = "id,caption,permalink,like_count,comments_count,timestamp,media_type"


def main() -> None:
    token = os.environ["IG_ACCESS_TOKEN"]
    ig_user_id = os.environ["IG_USER_ID"]

    results = {}
    errors = {}

    for tag in HASHTAGS:
        try:
            hashtag_id = _find_hashtag_id(tag, ig_user_id, token)
            posts = _top_media(hashtag_id, ig_user_id, token)
            results[tag] = posts
            print(f"#{tag}: {len(posts)} posts")
        except requests.HTTPError as exc:
            body = exc.response.text if exc.response is not None else str(exc)
            errors[tag] = body
            print(f"#{tag}: FAILED - {body}", file=sys.stderr)
        time.sleep(1)  # be polite between calls

    DIGEST_DIR.mkdir(exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    out_path = DIGEST_DIR / f"{today}.md"
    out_path.write_text(_render_markdown(today, results, errors))
    print(f"Wrote {out_path}")

    if errors and not results:
        # Every hashtag failed the same way - almost certainly a permissions
        # issue (missing Instagram Public Content Access). Surface that
        # clearly instead of just leaving an empty digest.
        print(
            "All hashtag lookups failed. This is most likely because the app "
            "doesn't have the 'Instagram Public Content Access' permission "
            "yet (requires Meta App Review). See digests/ for the error "
            "bodies.",
            file=sys.stderr,
        )
        sys.exit(1)


def _find_hashtag_id(tag: str, ig_user_id: str, token: str) -> str:
    resp = requests.get(
        f"{GRAPH_HOST}/{GRAPH_VERSION}/ig_hashtag_search",
        params={"user_id": ig_user_id, "q": tag, "access_token": token},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if not data:
        raise RuntimeError(f"No hashtag id returned for #{tag}")
    return data[0]["id"]


def _top_media(hashtag_id: str, ig_user_id: str, token: str) -> list:
    resp = requests.get(
        f"{GRAPH_HOST}/{GRAPH_VERSION}/{hashtag_id}/top_media",
        params={
            "user_id": ig_user_id,
            "fields": FIELDS,
            "access_token": token,
        },
        timeout=30,
    )
    resp.raise_for_status()
    posts = resp.json().get("data", [])
    posts.sort(key=lambda p: p.get("like_count", 0), reverse=True)
    return posts[:POSTS_PER_HASHTAG]


def _render_markdown(today: str, results: dict, errors: dict) -> str:
    lines = [f"# Niche engagement digest - {today}", ""]
    lines.append(
        "Posts to look at and manually like/comment on yourself. Nothing "
        "here has been liked, commented on, or followed automatically."
    )
    lines.append("")

    for tag, posts in results.items():
        lines.append(f"## #{tag}")
        if not posts:
            lines.append("_No posts returned._")
            lines.append("")
            continue
        for p in posts:
            caption = (p.get("caption") or "").replace("\n", " ").strip()
            if len(caption) > 140:
                caption = caption[:137] + "..."
            likes = p.get("like_count", "?")
            comments = p.get("comments_count", "?")
            lines.append(
                f"- [{likes}♥ / {comments}💬]({p['permalink']}) - {caption}"
            )
        lines.append("")

    if errors:
        lines.append("## Lookup errors")
        for tag, body in errors.items():
            lines.append(f"- `#{tag}`: {body}")
        lines.append("")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
