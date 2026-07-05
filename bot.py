import os
import re
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("ott-bot")

# ---------------------------------------------------------------------------
# Config (all read from environment variables set on Render)
# ---------------------------------------------------------------------------
BOT_TOKEN = os.environ["BOT_TOKEN"]                      # from @BotFather
API_BASE_URL = os.environ.get(
    "API_BASE_URL", "https://animecall-ott-poster-scraper.onrender.com"
)
API_TOKEN = os.environ.get("API_TOKEN", "")               # sent as Authorization header
PORT = int(os.environ.get("PORT", "10000"))
# Render sets this automatically for every web service
EXTERNAL_URL = os.environ.get("RENDER_EXTERNAL_URL", "")

# ---------------------------------------------------------------------------
# Domain -> API endpoint mapping
# Add/adjust entries here if a platform isn't detected correctly.
# ---------------------------------------------------------------------------
DOMAIN_MAP = {
    "crunchyroll.com": "crunchyroll",
    "bookmyshow.com": "bms",
    "netflix.com": "nf",
    "iq.com": "iqyi",
    "mxplayer.in": "mxplayer",
    "amazon.": "amazon",
    "primevideo.com": "amazon",
    "airtelxstream.in": "airtel",
    "zee5.com": "zee5",
    "ultra": "ultra",
    "youtube.com": "youtube",
    "youtu.be": "youtube",
    "viki.com": "viki",
    "youku.com": "youku",
    "wetv.vip": "wetv",
    "hulu.com": "hulu",
    "ticketnew.com": "ticketnew",
    "sonyliv.com": "sonyliv",
    "shemaroome.com": "shemaroo",
    "tv.apple.com": "apple",
    "chaupal.tv": "chaupal",
    "aha.video": "aha",
    "vivamax": "viva",
    "plex.tv": "plex",
    "atrangii.com": "atrangii",
    "sunnxt.com": "sunnxt",
    "playflix": "playflix",
    "lionsgateplay.com": "lionsgate",
    "erosnow.com": "erosnow",
    "hungama.com": "hungama",
    "hoichoi.tv": "hoichoi",
    "jojoapp.in": "jojo",
    "ultrajhakaas.com": "ultrajhakaas",
    "mubi.com": "mubi",
    "sainaplay.com": "sainaplay",
    "addatimes.com": "addatimes",
    "aaonxt.com": "aaonxt",
    "viu.com": "viu",
    "dangalplay.com": "dangal",
    "tataplay.com": "tataplay",
    "tubitv.com": "tubi",
}

URL_RE = re.compile(r"https?://\S+")
IMAGE_KEY_HINTS = ("poster", "image", "thumbnail", "img", "url", "cover")
IMAGE_EXT_RE = re.compile(r"\.(jpg|jpeg|png|webp)(\?.*)?$", re.IGNORECASE)


def detect_platform(url: str) -> str | None:
    for domain, endpoint in DOMAIN_MAP.items():
        if domain in url:
            return endpoint
    return None


def find_image_url(data) -> str | None:
    """Walk a JSON-like structure looking for something that looks like an image URL."""
    if isinstance(data, str):
        if data.startswith("http") and (
            IMAGE_EXT_RE.search(data) or "poster" in data.lower() or "image" in data.lower()
        ):
            return data
        return None
    if isinstance(data, dict):
        # Prefer keys that hint at an image
        for key, value in data.items():
            if any(hint in key.lower() for hint in IMAGE_KEY_HINTS):
                found = find_image_url(value)
                if found:
                    return found
        for value in data.values():
            found = find_image_url(value)
            if found:
                return found
    if isinstance(data, list):
        for item in data:
            found = find_image_url(item)
            if found:
                return found
    return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Send me a link from a supported OTT platform (Netflix, Amazon, MX Player, "
        "ZEE5, Crunchyroll, YouTube, and more) and I'll fetch its poster."
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text or ""
    match = URL_RE.search(text)
    if not match:
        await update.message.reply_text("That doesn't look like a link. Send me a valid URL.")
        return

    url = match.group(0)
    endpoint = detect_platform(url)
    if not endpoint:
        await update.message.reply_text(
            "I don't recognize that platform yet. Supported platforms include Netflix, "
            "Amazon, MX Player, ZEE5, Crunchyroll, YouTube, and several others."
        )
        return

    await update.message.reply_chat_action("upload_photo")

    api_url = f"{API_BASE_URL}/posters/{endpoint}"
    headers = {"Authorization": API_TOKEN} if API_TOKEN else {}

    try:
        response = requests.get(api_url, params={"url": url}, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException as exc:
        log.error("API call failed: %s", exc)
        await update.message.reply_text(f"Couldn't fetch that poster. ({exc})")
        return
    except ValueError:
        await update.message.reply_text("The API returned something that wasn't valid JSON.")
        return

    image_url = find_image_url(data)
    if image_url:
        try:
            await update.message.reply_photo(photo=image_url)
            return
        except Exception as exc:  # Telegram couldn't fetch/display that image URL
            log.warning("reply_photo failed: %s", exc)

    # Fallback: show the raw response so you can see the actual shape and adjust
    # find_image_url() above if needed.
    await update.message.reply_text(f"Raw API response:\n{data}")


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    if EXTERNAL_URL:
        # Webhook mode - required for Render's free Web Service tier
        webhook_url = f"{EXTERNAL_URL}/{BOT_TOKEN}"
        log.info("Starting in webhook mode: %s", webhook_url)
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,
            webhook_url=webhook_url,
        )
    else:
        # Fallback for local testing
        log.info("RENDER_EXTERNAL_URL not set - starting in polling mode (local dev only)")
        app.run_polling()


if __name__ == "__main__":
    main()
