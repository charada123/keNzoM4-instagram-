# kenzoM4 Instagram Poster

Drop an image + caption in the queue, and a scheduled GitHub Action posts the
oldest un-posted one to Instagram once a day.

## How it works

- `queue/queue.json` is an ordered list of posts: `{id, image, caption, posted}`.
- `queue/images/` holds the actual image files.
- Every day, `.github/workflows/post-daily.yml` runs `scripts/post_to_instagram.py`,
  which publishes the **first** entry in `queue.json` where `"posted": false`,
  then marks it posted and commits that change back to the repo.
- Images are handed to Instagram as a public `raw.githubusercontent.com` URL,
  so this repo needs to stay public for the bot to fetch them. Captions and
  images are visible in the repo before they go out — don't queue anything
  you don't want visible in advance if that's a concern.

## One-time setup (required before anything can post)

This uses Meta's **Instagram API with Instagram Login** (not the older
Facebook-Page-based Graph API), set up via a Meta Developer app. The posting
script calls `graph.instagram.com` and expects a token in the `IGAA...`
format that this flow issues.

1. Instagram account must be a **Professional** account (Instagram app →
   Settings → Account type and tools).
2. Create a Meta app at https://developers.facebook.com/apps → **Create App**
   → type **Business** → add use case **"Manage messaging & content on
   Instagram"**.
3. On the app dashboard → **App roles → Roles**, add your own Facebook
   profile with the **Instagram Tester** role. Then, on your phone: Instagram
   app → Settings and privacy → Apps and websites → **Tester Invites** tab →
   confirm the invite is accepted (shows "Authorized by you").
4. Back on the app dashboard → **Use cases → Customize → API setup with
   Instagram login** → step 1, add the `instagram_business_content_publish`
   permission (under "Permissions and features") in addition to the
   defaults. → step 2, click **Add account** and complete the Instagram
   login/authorization prompt. This generates:
   - An **access token** (starts with `IGAA...`) — long-lived, ~60 days.
   - Your **Instagram User ID** — shown on the same screen.
5. **Add two repo secrets** (Settings → Secrets and variables → Actions →
   New repository secret) on `charada123/kenzoM4-instagram-`:
   - `IG_ACCESS_TOKEN` — the token from step 4 (never paste this into chat
     with anyone, including Claude — add it directly in GitHub)
   - `IG_USER_ID` — the ID from step 4

**The token expires after ~60 days.** Before it expires, go back to the same
"API setup with Instagram login" page and regenerate it, then update the
`IG_ACCESS_TOKEN` secret — otherwise posting will silently stop (check the
Actions tab for a failed run).

## Adding a post to the queue

```
python scripts/queue_add.py path/to/photo.jpg "Your caption here #tags"
git add queue/
git commit -m "Queue post 0001"
git push
```

That's it — the next scheduled run will pick it up in order.

## Posting cadence

Currently once a day at 14:00 UTC (`.github/workflows/post-daily.yml`).
Edit the `cron` line to change it. You can also trigger a run immediately
from the Actions tab (`workflow_dispatch`) to test without waiting for the
schedule.

## Limitations

- Images only for now (JPEG/PNG via `image_url`); video/Reels would need a
  small change to use `media_type: REELS` and `video_url`.
- Instagram's Content Publishing API caps you at 25 posts per rolling 24
  hours, so a daily cadence is well within limits.
