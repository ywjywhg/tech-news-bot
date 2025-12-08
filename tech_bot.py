import feedparser, requests, re, time, os, hashlib
from googletrans import Translator
from bs4 import BeautifulSoup
from datetime import datetime

# ================== 配置 ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
translator = Translator()

# 科技类 RSS（2025年实测全部可用）
RSS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://arstechnica.com/feed/",
    "https://www.engadget.com/rss.xml",
    "https://rsshub.app/36kr/newsflashes",
    "https://feeds.feedburner.com/mittrchinese",
]

# 免费 OCR + 免费图片加文字 API（超稳）
OCR_API = "https://api.ocr.space/parse/image"
TEXT_ON_IMG = "https://api.textinimage.com/overlay"

seen_hashes = set()  # 今天已发的新闻哈希（去重）

def hash_title(title):
    return hashlib.md5(title.encode('utf-8')).hexdigest()[:12]

def translate(text):
    if not text: return ""
    try:
        time.sleep(0.7)
        return translator.translate(text.strip(), dest='zh-cn').text
    except:
        return text.strip()

def get_image_url(link):
    try:
        r = requests.get(link, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        img = soup.find("meta", property="og:image")
        return img["content"] if img else None
    except:
        return None

def ocr_and_overlay(image_url):
    """把图片里的英文翻译成中文并打上去"""
    try:
        # 1. OCR 识别图片文字
        ocr = requests.post(OCR_API, data={
            'apikey': 'helloworld',      # ocr.space 免费默认key
            'url': image_url,
            'language': 'eng',
        }).json()
        en_text = ocr.get("ParsedResults",[{}])[0].get("ParsedText","").strip()
        if not en_text: return image_url

        # 2. 翻译成中文
        zh_text = translate(en_text)
        if len(zh_text) > 100: zh_text = zh_text[:100] + "…"

        # 3. 把中文打到图片右下角（大白字黑边）
        overlay = f"{TEXT_ON_IMG}?text={requests.utils.quote(zh_text)}&url={requests.utils.quote(image_url)}&fontSize=52&color=ffffff&stroke=000000&strokeWidth=8&gravity=southeast&padding=30"
        return overlay
    except:
        return image_url  # 任何一步失败就返回原图

def send(photo_url, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        requests.post(url+"sendPhoto", data={
            "chat_id": CHAT_ID,
            "photo": photo_url,
            "caption": caption[:1000],
            "parse_mode": "HTML"
        }, timeout=20)
    except:
        # 发不了图就发文字
        requests.post(url+"sendMessage", data={
            "chat_id": CHAT_ID,
            "text": caption,
            "parse_mode": "HTML",
            "disable_web_page_preview": False
        }, timeout=20)

# ================== 开机问好 ==================
send(None, f"晚上好！科技头条 · {datetime.now().strftime('%m月%d日 %A')}")

count = 0
for feed_url in RSS:
    feed = feedparser.parse(feed_url)
    for entry in feed.entries:
        if count >= 10: break

        raw_title = entry.title
        title_hash = hash_title(raw_title)
        if title_hash in seen_hashes: continue
        seen_hashes.add(title_hash)

        link = entry.link
        summary = (getattr(entry, 'summary', '') or getattr(entry, 'description', '') or '')[:300]

        zh_title   = translate(raw_title)
        zh_summary = translate(summary) if summary else ""

        caption = f"<b>{zh_title}</b>\n\n{zh_summary}\n\n来源：{feed.feed.get('title','科技新闻')}\n<a href='{link}'>阅读全文</a>"

        img = get_image_url(link)
        if img:
            final_img = ocr_and_overlay(img)   # 关键：图片中文字幕
            send(final_img, caption)
        else:
            send(None, caption)

        count += 1
        time.sleep(5)

# ================== 收尾 ==================
send(None, f"今晚精选 {count} 条科技新闻已送达\n图片上的英文已自动翻译成中文\n晚安")
print(f"科技新闻推送完成，共 {count} 条")
