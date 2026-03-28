import os, anthropic, feedparser, requests, schedule, time, logging
from datetime import datetime

ANTHROPIC_API_KEY  = os.environ.get("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

SOURCES = [
    {"name": "Vitalik",      "url": "https://nitter.poast.org/VitalikButerin/rss"},
    {"name": "Saylor",       "url": "https://nitter.poast.org/saylor/rss"},
    {"name": "CoinDesk",     "url": "https://www.coindesk.com/arc/outboundfeeds/rss/"},
    {"name": "CoinTelegraph","url": "https://cointelegraph.com/rss"},
]

seen = set()

def fetch():
    items = []
    for s in SOURCES:
        try:
            feed = feedparser.parse(s["url"])
            for e in feed.entries[:2]:
                t = e.get("title","").strip()
                if t and t not in seen:
                    seen.add(t)
                    items.append(f"[{s['name']}] {t}")
        except:
            pass
    return "\n".join(items[:12])

def generate(news):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    r = client.messages.create(
        model="claude-sonnet-4-20250514", max_tokens=300,
        system="你是顶级加密货币分析师，只输出评论正文，中文，不超过140字，包含一个市场洞察。",
        messages=[{"role":"user","content":f"最新动态：\n{news}\n\n写一条140字以内的加密市场评论。"}],
    )
    return r.content[0].text.strip()

def push(text):
    now = datetime.now().strftime("%m-%d %H:%M")
    msg = f"⚡ <b>币圈速报 · {now}</b>\n\n{text}\n\n<i>— Claude 自动生成</i>"
    requests.post(
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
        json={"chat_id":TELEGRAM_CHAT_ID,"text":msg,"parse_mode":"HTML"},
        timeout=10
    )
    log.info("推送成功")

def run():
    news = fetch()
    if not news:
        return
    push(generate(news))

run()
schedule.every(30).minutes.do(run)
while True:
    schedule.run_pending()
    time.sleep(60)
