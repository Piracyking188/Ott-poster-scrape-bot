# OTT Poster Bot

Telegram bot that fetches OTT posters via the AnimeCall Botz Posters API.

## 1. Get a bot token
Message [@BotFather](https://t.me/BotFather) on Telegram:
- If "OTT Poster Scrape" already exists, send `/mybots` → select it → **API Token**
- If not, send `/newbot` and follow the prompts

Copy the token it gives you (looks like `123456789:ABCdefGhIJKlmNoPQRsTUvwXYz`).

## 2. Push this code to GitHub
Create a new repo and push `bot.py`, `requirements.txt`, and this README to it.

## 3. Deploy on Render
1. New → Web Service → connect (or paste) your new repo
2. Environment: **Python 3**
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `python bot.py`
5. Add these Environment Variables:
   | Key | Value |
   |---|---|
   | `BOT_TOKEN` | the token from BotFather |
   | `API_BASE_URL` | `https://animecall-ott-poster-scraper.onrender.com` |
   | `API_TOKEN` | same value you set on the scraper API's `API_TOKEN` |
6. Deploy

Render automatically sets `RENDER_EXTERNAL_URL` and `PORT` for you — the bot uses
these to register a Telegram webhook, so no extra setup is needed there.

## 4. Test it
Open your bot in Telegram, send `/start`, then send a supported OTT link
(e.g. a Netflix or MX Player URL). It should reply with the poster image.

## If the poster doesn't show up
The scraper API's exact response shape (field names for the poster URL) wasn't
documented in its OpenAPI spec. If `find_image_url()` in `bot.py` can't locate
an image URL automatically, the bot will show you the raw JSON response instead —
use that to see the real key name and adjust the `IMAGE_KEY_HINTS` tuple or
`find_image_url()` function accordingly.
