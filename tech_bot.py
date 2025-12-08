import feedparser, requests, re, time, os, hashlib
from googletrans import Translator
from bs4 import BeautifulSoup

# ================== 配置 ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")
MAX_COUNT = 10

# 科技类 RSS（2025 年全部可用）
RSS_FEEDS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://www.wired.com/feed/rss",
    "https://arstechnica.com/feed/",
    "https://feeds.feedburner.com/mittrchinese",        # MIT 科技评论中文
    "https://rsshub.app/36kr/newsflashes",              # 36氪
    "https://www.ifanr.com/feed",                       # 爱范儿
    "https://sspai.com/feed",                           # 少数派
]

translator = Translator(service_urls=['translate.google.com'])

# 简单去重：用标题的 md5 存当天已发记录
seen = set()

def md5(s): 
    return hashlib.md5(s.encode()).hexdigest()

def log(msg):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def translate(text):
    if not text: return ""
    try:
        time.sleep(0.7)
        return translator.translate(text.strip(), dest='zh-cn').text
    except Exception as e:
        log(f"翻译失败: {e}")
        return text.strip()

def get_image(link):
    try:
        r = requests.get(link, timeout=9, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'lxml')
        img = soup.find("meta", property="og:image")
        return img["content"] if img else None
    except:
        return None

def send(photo_url=None, caption=""):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/{'sendPhoto' if photo_url else 'sendMessage'}"
    data = {"chat_id": CHAT_ID, "parse_mode": "HTML", "disable_web_page_preview": False}
    if photo_url:
        data["photo"] = photo_url
        data["caption"] = caption[:1000]
    else:
        data["text"] = caption

    for i in range(3):
        try:
            r = requests.post(url, data=data, timeout=15)
            if r.json().get("ok"):
                return True
        except:
            time.sleep(2)
    log("发送失败")
    return False

# =============== 开始 ===============
log("科技新闻机器人启动")

send(caption="晚上好！今晚最热科技新闻来啦")

count = 0
for url in _FEEDS:
    if count >= MAX_COUNT: break
    log(f"抓取 {url}")
    try:
        feed = feedparser.parse(url)
        for e in feed.entries:
            if count >= MAX_COUNT: break
            title = re.sub('<[^>]+>', '', e.title)
            key = md5(title)
            if key in seen: 
                continue
            seen.add(key)

            link = e.link
            img = get_image(link)

            zh_title = translate(title)
            caption = f"<b>{zh_title}</b>\n\n来源：{feed.feed.get('title','科技新闻')}\n<a href='{link}'>阅读全文</a>"

            if send(img, caption):
                count += 1
                log(f"成功 #{count}: {zh_title[:30]}")
            time.sleep(4.5)  # 防风控
    except Exception as e:
        log(f"抓取失败: {e}")

# 收尾
send(caption=f"今晚科技精选 {count} 条已全部送达\n祝你晚安")
log("全部完成")
