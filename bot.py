import cloudscraper
from bs4 import BeautifulSoup
import requests
import re

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

BOT_TOKEN = "8376186992:AAEu-Xc4yoX9iae0BmUnKnNsNaGVaN-bChI"
CHANNEL_ID = "-1003858166428"

WP_URL = "https://promanga.wuaze.com"
WP_USER = "boss"
WP_PASS = "cfkD s7wH YUmW cCiE mjEp YRPn"

scraper = cloudscraper.create_scraper()

# =========================
# سحب بيانات من Lekmanga
# =========================
def get_manga_data(url):
    html = scraper.get(url).text
    soup = BeautifulSoup(html, "html.parser")

    title = soup.find("h1").text.strip()

    cover = soup.find("div", class_="summary_image")
    cover = cover.find("img")["src"]

    story = soup.find("div", class_="summary__content").text.strip()

    chapters = []
    for a in soup.select(".wp-manga-chapter a"):
        chapters.append(a["href"])

    return title, cover, story, chapters


# =========================
# رفع صورة للقناة (CDN تلغرام)
# =========================
async def upload_to_telegram(url, context):
    msg = await context.bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=url
    )
    return msg.photo[-1].file_id


# =========================
# إنشاء مانغا في Madara
# =========================
def create_manga(title, cover_id, story):
    data = {
        "title": title,
        "content": story,
        "status": "publish",
        "meta": {
            "_wp_manga_cover": cover_id
        }
    }

    r = requests.post(
        f"{WP_URL}/wp-json/wp/v2/manga",
        json=data,
        auth=(WP_USER, WP_PASS)
    )

    return r.json()["id"]


# =========================
# إضافة فصل
# =========================
def add_chapter(manga_id, title, images):
    data = {
        "post": manga_id,
        "chapter_name": title,
        "storage": "telegram",
        "images": images
    }

    requests.post(
        f"{WP_URL}/wp-json/madara/v1/chapter",
        json=data,
        auth=(WP_USER, WP_PASS)
    )


# =========================
# أمر البوت
# =========================
async def leech(update: Update, context: ContextTypes.DEFAULT_TYPE):

    url = context.args[0]

    await update.message.reply_text("⏳ جاري السحب...")

    title, cover, story, chapters = get_manga_data(url)

    cover_id = await upload_to_telegram(cover, context)

    manga_id = create_manga(title, cover_id, story)

    for ch in chapters:
        html = scraper.get(ch).text
        soup = BeautifulSoup(html, "html.parser")

        images = []
        for img in soup.select(".reading-content img"):
            file_id = await upload_to_telegram(img["src"], context)
            images.append(file_id)

        name = soup.find("h1").text.strip()

        add_chapter(manga_id, name, images)

    await update.message.reply_text("✅ تم الرفع بنجاح للموقع")


# =========================
# تشغيل البوت
# =========================
app = Application.builder().token(BOT_TOKEN).build()

app.add_handler(CommandHandler("leech", leech))

print("Bot is running...")
app.run_polling()
