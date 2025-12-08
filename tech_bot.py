import feedparser
import requests
import re
import time
import os
from googletrans import Translator
from bs4 import BeautifulSoup

# ================== 配置 ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
MAX_COUNT = 12                     # 每天最多发12条

# 2025年还能正常使用的科技类RSS（亲测可用）
RSS_FEEDS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://arstechnica.com/feed/",
    "https://feeds.feedburner.com/mittrchinese",        # MIT科技评论中文
    "https://rsshub.app/36kr/newsflashes",              # 36氪
    "https://www.ifanr.com/feed",                       # 爱范儿
    "https://rsshub.app/timeline/apple",                  # 少数派 + 苹果
]

translator = Translator()

def translate(text):
    if not text:
        return ""
    try:
        time.sleep(0.7)      # 防Google风控
        return translator.translate(text.strip(), dest='zh-cn').text
    except:
        return text.strip()

def get_og_image(url):
    try:
        r = requests.get(url, timeout=10)
        soup = BeautifulSoup(r.text, 'lxml')
        tag = soup.find("meta", property="og:image")
        if tag and tag.get("content"):
            return tag["content"]
    except:
        pass
    return None

def send_message(text):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
        data={"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"},
        timeout=15
    )

def send_photo(photo_url, caption):
    requests.post(
        f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
        data={
            "chat_id": CHAT_ID,
            "photo": photo_url,
            "caption": caption[:1000],
            "parse_mode": "HTML"
        },
        timeout=20
    )

# =============== 开始推送 ===============
send_message("晚上好！今晚最热科技新闻来啦")

count = 0
for rss in RSS_FEEDS:
    if count >= MAX_COUNT:
        break
    try:
        feed = feedparser.parse(rss)
        for entry in feed.entries[:10]:
            if count >= MAX_COUNT:
                break

            title = re.sub(r'<[^>]+>', '', entry.title)
            link  = entry.link

            zh_title = translate(title)

            img = get_og_image(link)

            caption = f"<b>{zh_title}</b>\n\n来源：{feed.feed.get('title', '科技新闻')[:30]}\n<a href=\"{link}\">阅读全文</a>"

            if img:
                send_photo(img, caption)
            else:
                send_message(caption)

            count += 1
            time.sleep(4)        # 防风控
    except Exception as e:
        print(f"抓取失败 {rss}: {e}")
        continue

# 收尾
send_message(f"今晚科技精选 {count} 条已全部送达\n祝你晚安")
print(f"科技新闻推送完成，共 {count} 条")
