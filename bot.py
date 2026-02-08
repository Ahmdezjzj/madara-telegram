import cloudscraper
import requests
from bs4 import BeautifulSoup
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== إعداداتك =====
BOT_TOKEN = "8376186992:AAEu-Xc4yoX9iae0BmUnKnNsNaGVaN-bChI"
CHANNEL_ID = "-1003858166428"

WP_URL = "https://promanga.wuaze.com"
WP_USER = "boss"
WP_PASS = "cfkD s7wH YUmW cCiE mjEp YRPn"

scraper = cloudscraper.create_scraper()
session = requests.Session()
session.auth = (WP_USER, WP_PASS)

# ====================

def upload_to_telegram(img_url):
    bot = Bot(BOT_TOKEN)
    img = requests.get(img_url).content

    msg = bot.send_photo(chat_id=CHANNEL_ID, photo=img)
    file = bot.get_file(msg.photo[-1].file_id)

    return f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file.file_path}"


def create_manga(title, desc, cover):
    cover_tg = upload_to_telegram(cover)

    data = {
        "title": title,
        "content": desc,
        "status": "publish"
    }

    r = session.post(f"{WP_URL}/wp-json/wp/v2/manga", json=data)
    return r.json().get("id")


def add_chapter(manga_id, title, images):
    html = ""
    for img in images:
        tg = upload_to_telegram(img)
        html += f'<img src="{tg}" />\n'

    data = {
        "title": title,
        "content": html,
        "status": "publish",
        "meta": {"manga_id": manga_id}
    }

    session.post(f"{WP_URL}/wp-json/wp/v2/chapters", json=data)


def scrape_manga(url):
    soup = BeautifulSoup(scraper.get(url).text, "html.parser")

    title = soup.find("h1").text.strip()
    cover = soup.select_one(".summary_image img")["src"]
    desc = soup.select_one(".summary__content").text.strip()

    chapters = []
    for a in soup.select(".wp-manga-chapter a"):
        chapters.append({
            "title": a.text.strip(),
            "url": a["href"]
        })

    return title, desc, cover, chapters


def scrape_images(url):
    soup = BeautifulSoup(scraper.get(url).text, "html.parser")
    return [i["src"] for i in soup.select(".reading-content img")]


async def leech(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = context.args[0]
    limit = int(context.args[1]) if len(context.args) > 1 else None

    await update.message.reply_text("⏳ جاري سحب المانهوا...")

    title, desc, cover, chapters = scrape_manga(url)

    if limit:
        chapters = chapters[:limit]

    await update.message.reply_text(f"📘 إنشاء: {title}")

    manga_id = create_manga(title, desc, cover)

    for ch in chapters:
        await update.message.reply_text(f"📥 فصل: {ch['title']}")
        imgs = scrape_images(ch["url"])
        add_chapter(manga_id, ch["title"], imgs)

    await update.message.reply_text("✅ تم النشر في موقعك بنجاح!")


app = Application.builder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("leech", leech))

app.run_polling()
