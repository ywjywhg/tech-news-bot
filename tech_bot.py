import feedparser, requests, re, time, os
from googletrans import Translator
from bs4 import BeautifulSoup

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
translator = Translator()

RSS = [
    "https://www.theverge.com/rss/index.xml",           # The Verge
    "https://techcrunch.com/feed/",                     # TechCrunch
    "https://www.wired.com/feed/rss",                   # Wired
    "https://arstechnica.com/feed/",                    # Ars Technica
    "https://feeds.feedburner.com/mittrchinese",        # MIT 科技评论中文
    "https://rsshub.app/36kr/newsflashes",              # 36氪快讯
]

def translate(text):
    try:
        time.sleep(0.8)
        return translator.translate(text, dest='zh-cn').text
    except:
        return text

def get_img(link):
    try:
        r = requests.get(link, timeout=8)
        soup = BeautifulSoup(r.text, 'lxml')
        img = soup.find("meta", property="og:image")
        return img["content"] if img else None
    except:
        return None

def send(photo, caption):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto"
    requests.post(url, data={"chat_id": CHAT_ID, "photo": photo, "caption": caption[:1000], "parse_mode": "HTML"}, timeout=20)

requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
              data={"chat_id": CHAT_ID, "text": "晚上好！今晚最热科技新闻来啦"})

count = 0
for url in RSS:
    feed = feedparser.parse(url)
    for e in feed.entries[:8]:
        if count >= 12: break
        title = re.sub('<[^>]+>', '', e.title)
        link = e.link
        img = get_img(link)
        zh = translate(title)
        cap = f"<b>{zh}</b>\n\n来源：{feed.feed.get('title','科技新闻')}\n<a href='{link}'>阅读全文</a>"
        if img:
            send(img, cap)
        count += 1
        time.sleep(4)

requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
              data={"chat_id": CHAT_ID, "text": f"今晚科技精选 {count} 条已送达\n晚安"})