import feedparser, requests, re, time, os
from googletrans import Translator
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
translator = Translator()

def translate(text):
    if not text: return ""
    try:
        time.sleep(0.7)
        return translator.translate(text.strip(), dest='zh-cn').text
    except:
        return text.strip()

def get_image(link):
    try:
        r = requests.get(link, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'lxml')
        img = soup.find("meta", property="og:image")
        return img["content"] if img else None
    except:
        return None

def send(photo, caption):
    requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto", data={
        "chat_id": CHAT_ID,
        "photo": photo,
        "caption": caption[:1000],
        "parse_mode": "HTML"
    }, timeout=20)

# 开头
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
    "chat_id": CHAT_ID,
    "text": "晚上好！今晚科技头条摘要版"
})

count = 0
MAX = 10
seen = set()

RSS = [
    "https://feeds.bbci.co.uk/news/technology/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/Technology.xml",
    "https://cn.nytimes.com/rss/tech/",
    "https://www.theguardian.com/us/technology/rss/",
    "https://rss.cnn.com/rss/edition_technology.rss",
    "https://www.aljazeera.com/xml/rss/sciencetech.xml",
    "https://www.wired.com/feed/rss",
]

for url in RSS:
    if count >= MAX: break
    try:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if count >= MAX: break
            
            title = re.sub('<[^>]+>', '', e.title)
            if title in seen: continue
            seen.add(title)
            
            link = e.link
            img = get_image(link) or "https://s1.ax1x.com/2025/03/18/pEFd0fI.jpg"

            # 取摘要（优先 summary → description → content）
            raw_summary = getattr(e, 'summary', '') or getattr(e, 'description', '') or ''
            summary = re.sub('<[^>]+>', '', raw_summary).strip()
            if len(summary) > 180:
                summary = summary[:180] + "…"
            if summary:
                summary = translate(summary)

            zh_title = translate(title)

            caption = f"<b>{zh_title}</b>\n"
            if summary:
                caption += f"\n{summary}\n"
            caption += f"\n来源：{feed.feed.get('title','科技新闻').split(' - ')[0].split('|')[0]}\n"
            caption += f"<a href='{link}'>查看完整报道 ›</a>"

            send(img, caption)
            count += 1
            time.sleep(4.5)
    except:
        continue

# 结尾
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
    "chat_id": CHAT_ID,
    "text": f"今晚科技摘要 {count} 条已送达\n晚安"
})
