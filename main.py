import os
import asyncio
import requests
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# ===================== REAL DATA =====================
FX = ["USD","EUR","GBP","JPY","TRY","CAD","AUD","CHF","CNY","IRR"]

CRYPTO = [
    "bitcoin","ethereum","bnb","solana","xrp","dogecoin","cardano","tron",
    "litecoin","polkadot","avalanche-2","chainlink","stellar","shiba-inu",
    "near","matic-network","uniswap","aptos","arbitrum","kaspa",
    "okb","fantom","algorand","leo-token","tether"
]

COUNTRIES = {
    "Iran 🇮🇷":"IRR",
    "Turkey 🇹🇷":"TRY",
    "USA 🇺🇸":"USD",
    "EU 🇪🇺":"EUR",
    "UK 🇬🇧":"GBP",
    "Japan 🇯🇵":"JPY",
    "China 🇨🇳":"CNY",
    "Canada 🇨🇦":"CAD",
    "Australia 🇦🇺":"AUD",
    "Switzerland 🇨🇭":"CHF"
}

users = set()
last = {"usd": None, "btc": None, "gold": None}

# ===================== API REAL =====================
def fx(base, target):
    try:
        return requests.get(
            f"https://api.frankfurter.app/latest?from={base}&to={target}"
        ).json()["rates"][target]
    except:
        return None

def crypto(c):
    try:
        return requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={c}&vs_currencies=usd"
        ).json()[c]["usd"]
    except:
        return None

def metals():
    try:
        d = requests.get("https://api.metals.live/v1/spot").json()[0]
        return d["gold"], d["silver"], d["oil"]
    except:
        return 0,0,0

def gold_irr():
    g,_,_ = metals()
    usd_irr = fx("USD","IRR")
    if usd_irr:
        return g * usd_irr
    return 0

# ===================== CHART =====================
def chart():
    data = []
    for _ in range(6):
        v = fx("USD","IRR")
        if v:
            data.append(v)

    plt.plot(data)
    plt.title("USD/IRR REAL")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ===================== UI =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز","₿ کریپتو"],
        ["🥇 طلا","🌍 کشورها"],
        ["📊 نمودار","🔔 وضعیت"]
    ],
    resize_keyboard=True
)

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_chat.id)
    await update.message.reply_text(
        "🚀 GOD MODE PRO REAL\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )

# ===================== HANDLE =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last
    text = update.message.text

    # 💱 FX REAL
    if text == "💱 ارز":
        out = []
        for c in FX:
            r = fx("USD", c)
            if r:
                out.append(f"USD→{c} = {r}")
        await update.message.reply_text("\n".join(out))

    # ₿ CRYPTO REAL
    elif text == "₿ کریپتو":
        out = []
        for c in CRYPTO[:15]:
            p = crypto(c)
            if p:
                out.append(f"{c.upper()} = ${p}")
        await update.message.reply_text("\n".join(out))

    # 🥇 GOLD REAL (IRR)
    elif text == "🥇 طلا":
        await update.message.reply_text(
            f"🥇 Gold (IRR): {gold_irr():,.0f}"
        )

    # 🌍 COUNTRIES REAL → IRR
    elif text == "🌍 کشورها":
        usd_irr = fx("USD","IRR")

        out = []
        for name, code in COUNTRIES.items():
            r = fx("USD", code)
            if r and usd_irr:
                out.append(f"{name} = {r * usd_irr:,.0f} IRR")

        await update.message.reply_text("\n".join(out))

    # 📊 CHART REAL
    elif text == "📊 نمودار":
        path = chart()
        await update.message.reply_photo(photo=open(path,"rb"))

    # 🔔 STATUS + SIMPLE AI
    elif text == "🔔 وضعیت":
        usd = fx("USD","IRR")
        btc = crypto("bitcoin")
        gold = gold_irr()

        msg = "📊 MARKET STATUS\n"

        if last["usd"] and usd:
            msg += f"USD: {'📈' if usd > last['usd'] else '📉'}\n"
        if last["btc"] and btc:
            msg += f"BTC: {'📈' if btc > last['btc'] else '📉'}\n"
        if last["gold"] and gold:
            msg += f"GOLD: {'📈' if gold > last['gold'] else '📉'}\n"

        last["usd"], last["btc"], last["gold"] = usd, btc, gold

        await update.message.reply_text(msg)

# ===================== LIVE ALERT SYSTEM =====================
async def watcher(app):
    global last

    while True:
        try:
            usd = fx("USD","IRR")
            btc = crypto("bitcoin")
            gold = gold_irr()

            msg = None

            if last["usd"] and usd and usd != last["usd"]:
                msg = f"🔔 USD: {usd:,.0f} IRR"

            if last["btc"] and btc and btc != last["btc"]:
                msg = f"🔔 BTC: {btc}"

            if last["gold"] and gold and gold != last["gold"]:
                msg = f"🔔 GOLD: {gold:,.0f} IRR"

            last["usd"], last["btc"], last["gold"] = usd, btc, gold

            if msg:
                for u in users:
                    await app.bot.send_message(u, msg)

        except:
            pass

        await asyncio.sleep(60)

# ===================== RUN =====================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

async def post_init(app):
    asyncio.create_task(watcher(app))

app.post_init = post_init

print("🚀 GOD MODE PRO RUNNING...")
app.run_polling()
