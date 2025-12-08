import feedparser, requests, re, time, os
from googletrans import Translator
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
translator = Translator()

def log(msg): print("LOG:", msg)

def translate(text):
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
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    try:
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "photo": photo,
            "caption": caption[:1000],
            "parse_mode": "HTML"
        }, timeout=20)
    except:
        pass

# 开头问好
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
    "chat_id": CHAT_ID,
    "text": "晚上好！今晚最热科技新闻来啦",
    "parse_mode": "HTML"
})

count = 0
MAX = 10

RSS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://arstechnica.com/feed/",
    "https://feeds.feedburner.com/mittrchinese",
    "https://rsshub.app/36kr/newsflashes",
    "https://www.ifanr.com/feed",
    "https://sspai.com/feed",
]

seen = set()

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
            img = get_image(link) or "https://s1.ax1x.com/2025/03/18/pEFd0fI.jpg"  # 备用图

            zh_title = translate(title)

            caption = f"""<b>{zh_title}</b>

来源：{feed.feed.get('title', '科技新闻').split(' - ')[0].split('|')[0]}

<a href="{link}">阅读全文</a>"""

            send(img, caption)
            count += 1
            log(f"成功 #{count}: {zh_title[:30]}")
            time.sleep(4.5)
    except Exception as e:
        log(f"错误: {e}")

# 结尾
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage", data={
    "chat_id": CHAT_ID,
    "text": f"今晚科技精选 {count} 条已全部送达\n晚安",
    "parse_mode": "HTML"
})
