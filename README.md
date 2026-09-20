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

You need a Meta (Facebook) Developer app connected to an Instagram
**Professional** (Business or Creator) account. None of this can be done by
Claude on your behalf — it requires your own Meta login.

1. **Make sure the Instagram account is a Professional account** and is
   linked to a Facebook Page you manage (Instagram app → Settings →
   Account type and tools → Switch to professional account, then link/create
   a Facebook Page from the same flow if it asks).
2. **Create a Meta app**: go to https://developers.facebook.com/apps →
   Create App → type "Business". Add the **Instagram Graph API** product to it.
3. **Generate a User access token** with these scopes, using the
   [Graph API Explorer](https://developers.facebook.com/tools/explorer/):
   `instagram_basic`, `instagram_content_publish`, `pages_show_list`,
   `pages_read_engagement`, `business_management`.
   - While the app is in Development mode, this works as long as your own
     Meta account is added as an Admin/Developer/Tester on the app — no App
     Review needed for posting to your own account.
4. **Exchange it for a long-lived token** (~60 days):
   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token
     ?grant_type=fb_exchange_token
     &client_id=<APP_ID>
     &client_secret=<APP_SECRET>
     &fb_exchange_token=<SHORT_LIVED_TOKEN>
   ```
5. **Find your Instagram Business Account ID**:
   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token=<TOKEN>
   ```
   take the Page ID from the result, then:
   ```
   GET https://graph.facebook.com/v21.0/<PAGE_ID>?fields=instagram_business_account&access_token=<TOKEN>
   ```
   the `id` in the response is your `IG_USER_ID`.
6. **Add two repo secrets** (Settings → Secrets and variables → Actions →
   New repository secret) on `charada123/kenzoM4-instagram-`:
   - `IG_ACCESS_TOKEN` — the long-lived token from step 4
   - `IG_USER_ID` — the ID from step 5

**The long-lived token expires after ~60 days.** Repeat step 4 before it
expires and update the `IG_ACCESS_TOKEN` secret, or posting will silently
stop (check the Actions tab for a failed run).

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
