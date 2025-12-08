import feedparser, requests, re, time, os, hashlib

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# 今天已经发过的链接（简单内存去重，防止早晚重复）
SENT_TODAY = set()

def send(photo, caption):
    try:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendPhoto",
                      data={"chat_id": CHAT, "photo": photo, "caption": caption[:900], "parse_mode": "HTML"},
                      timeout=15)
    except:
        requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
                      data={"chat_id": CHAT, "text": caption, "parse_mode": "HTML", "disable_web_page_preview": False})

def md5(s): return hashlib.md5(s.encode()).hexdigest()[:10]

# 纯科技源（和早上的全球新闻几乎零重叠）
TECH_RSS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://arstechnica.com/feed/",
    "https://www.engadget.com/rss.xml",
    "https://feeds.feedburner.com/mittrchinese",           # MIT科技评论中文
    "https://rsshub.app/36kr/newsflashes",                # 36氪
    "https://rsshub.app/tmtpost/news",                    # 钛媒体
    "https://rsshub.app/ifanr/news",                      # 爱范儿
    "https://rsshub.app/huxiu/article",                   # 虎嗅
]

requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
              data={"chat_id": CHAT, "text": "晚上好！今晚科技圈新鲜事"})

count = 0
for url in TECH_RSS:
    try:
        feed = feedparser.parse(url)
        for e in feed.entries[:12]:
            if count >= 15: break
            link = e.link.strip()
            key = md5(link)
            if key in SENT_TODAY: continue
            SENT_TODAY.add(key)

            title = re.sub('<[^>]+>', '', e.title)
            img = None
            try:
                r = requests.get(link, timeout=7)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(r.text, 'lxml')
                og = soup.find("meta", property="og:image")
                if og: img = og["content"]
            except: pass

            cap = f"<b>{title}</b>\n\n来源：{feed.feed.get('title','科技新闻').split(' - ')[0]}\n<a href='{link}'>阅读全文</a>"
            if img and img.startswith('http'):
                send(img, cap)
            else:
                send(None, cap)
            count += 1
            time.sleep(4.5)
    except: continue
    if count >= 15: break

requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/
