import os, feedparser, requests, re, time
from googletrans import Translator

# ========= 强制打印每一行，方便你我看日志 =========
def log(msg):
    print("=== " + msg)

log("脚本开始运行")

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID   = os.getenv("CHAT_ID")

if not BOT_TOKEN:
    log("ERROR: BOT_TOKEN 没拿到！去 Secrets 检查名字是不是写错")
    exit(1)
if not CHAT_ID:
    log("ERROR: CHAT_ID 没拿到！")
    exit(1)

log(f"Token 前6位: {BOT_TOKEN[:10]}...")
log(f"Chat ID: {CHAT_ID")

# 先发一句最简单的纯文字测试
def test_send():
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    try:
        r = requests.post(url, data={"chat_id": CHAT_ID, "text": "测试消息：机器人已成功启动！"}, timeout=15)
        result = r.json()
        log(f"测试消息结果 → {result}")
        return result.get("ok", False)
    except Exception as e:
        log(f"测试消息都发不出去 → {e}")
        return False

if not test_send():
    log("连最简单的测试消息都发不出去，99% 是 Token 或 Chat_ID 错了，脚本结束")
    exit(1)

log("测试消息成功！说明 Token 和 Chat_ID 完全正确，开始抓新闻")

translator = Translator()
count = 0
MAX = 8

RSS = [
    "https://www.theverge.com/rss/index.xml",
    "https://techcrunch.com/feed/",
    "https://feeds.feedburner.com/mittrchinese",
]

for url in RSS:
    if count >= MAX: break
    log(f"正在抓取 → {url}")
    try:
        feed = feedparser.parse(url)
        log(f"  拿到 {len(feed.entries)} 条")
        for e in feed.entries[:6]:
            if count >= MAX: break
            title = re.sub('<[^>]+>', '', e.title)
            link = e.link

            # 翻译标题
            try:
                zh = translator.translate(title, dest='zh-cn').text
            except:
                zh = title

            caption = f"<b>{zh}</b>\n\n来源：科技新闻\n<a href='{link}'>阅读全文</a>"

            # 直接发文字消息（先不发图，最简单）
            url_send = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
            r = requests.post(url_send, data={
                "chat_id": CHAT_ID,
                "text": caption,
                "parse_mode": "HTML",
                "disable_web_page_preview": True
            }, timeout=15)

            if r.json().get("ok"):
                count += 1
                log(f"成功发送 #{count}: {zh[:40]}")
            else:
                log(f"发送失败: {r.json()}")

            time.sleep(4)
    except Exception as e:
        log(f"抓取出错: {e}")

log(f"本次共成功发送 {count} 条，结束")
requests.post(f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
              data={"chat_id": CHAT_ID, "text": f"科技新闻推送完毕，共 {count} 条"})
