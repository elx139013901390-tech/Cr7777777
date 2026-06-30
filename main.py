import os
import asyncio
import requests
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)

TOKEN = os.getenv("BOT_TOKEN")

# ===================== DATA =====================
FX_LIST = ["usd","eur","gbp","jpy","try","cad","aud","chf","cny","irr"]

CRYPTO = [
    "bitcoin","ethereum","tether","bnb","solana","xrp","dogecoin","cardano",
    "tron","litecoin","polkadot","avalanche-2","chainlink","stellar",
    "shiba-inu","near","matic-network","uniswap","aptos","arbitrum",
    "kaspa","okb","fantom","algorand","leo-token"
]

METALS = {
    "gold": "XAU",
    "silver": "XAG",
    "oil": "WTI"
}

COUNTRIES = {
    "USA":"USD","EU":"EUR","UK":"GBP","Japan":"JPY",
    "Iran":"IRR","China":"CNY","Turkey":"TRY"
}

# ===================== STATE =====================
last = {"usd": None, "btc": None, "gold": None}
subs = set()

# ===================== FX =====================
def fx(base, target):
    return requests.get(f"https://fxapi.app/api/{base}/{target}.json").json()["rate"]

# ===================== CRYPTO =====================
def crypto(c):
    return requests.get(
        f"https://api.coingecko.com/api/v3/simple/price?ids={c}&vs_currencies=usd"
    ).json()[c]["usd"]

# ===================== METALS =====================
def metals():
    url = "https://api.metals.live/v1/spot"
    d = requests.get(url).json()[0]
    return d["gold"], d["silver"]

# ===================== CHART =====================
def chart():
    prices = [fx("usd","irr") for _ in range(6)]
    plt.plot(prices)
    plt.title("USD/IRR")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ===================== MENU =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز","₿ کریپتو"],
        ["🥇 طلا","📊 نمودار"],
        ["🌍 کشورها","🧠 پیش‌بینی"],
        ["🔔 وضعیت"]
    ],
    resize_keyboard=True
)

# ===================== START =====================
async def start(update:Update, context:ContextTypes.DEFAULT_TYPE):
    subs.add(update.effective_chat.id)
    await update.message.reply_text(
        "📊 ربات مالی حرفه‌ای واقعی\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )

# ===================== HANDLE =====================
async def handle(update:Update, context:ContextTypes.DEFAULT_TYPE):
    global last

    text = update.message.text

    # 💱 FX
    if text == "💱 ارز":
        out=[]
        for c in FX_LIST:
            out.append(f"USD→{c.upper()} = {fx('usd',c)}")
        await update.message.reply_text("\n".join(out))

    # ₿ CRYPTO
    elif text == "₿ کریپتو":
        out=[]
        for c in CRYPTO[:15]:
            out.append(f"{c.upper()} = ${crypto(c)}")
        await update.message.reply_text("\n".join(out))

    # 🥇 METALS
    elif text == "🥇 طلا":
        g,s = metals()
        await update.message.reply_text(
            f"🥇 Gold: {g}\n🥈 Silver: {s}"
        )

    # 📊 CHART
    elif text == "📊 نمودار":
        path = chart()
        await update.message.reply_photo(photo=open(path,"rb"))

    # 🌍 COUNTRIES
    elif text == "🌍 کشورها":
        await update.message.reply_text(
            "\n".join([f"{k}:{v}" for k,v in COUNTRIES.items()])
        )

    # 🧠 AI PREDICTION
    elif text == "🧠 پیش‌بینی":
        rate = fx("usd","irr")
        trend = "📈" if last["usd"] and rate>last["usd"] else "📉"
        future = rate*1.03 if trend=="📈" else rate*0.97

        await update.message.reply_text(
            f"""
🧠 AI تحلیل

الان: {rate}
روند: {trend}
پیش‌بینی: {future:.0f}
"""
        )

    # 🔔 STATUS
    elif text == "🔔 وضعیت":

        usd = fx("usd","irr")
        btc = crypto("bitcoin")
        gold,_ = metals()

        msg="📊 وضعیت بازار\n"

        if last["usd"]:
            msg += "USD: " + ("📈" if usd>last["usd"] else "📉") + "\n"

        if last["btc"]:
            msg += "BTC: " + ("📈" if btc>last["btc"] else "📉") + "\n"

        if last["gold"]:
            msg += "GOLD: " + ("📈" if gold>last["gold"] else "📉") + "\n"

        last["usd"]=usd
        last["btc"]=btc
        last["gold"]=gold

        await update.message.reply_text(msg)

# ===================== AUTO ALERT =====================
async def watcher(app):
    global last

    while True:
        try:
            usd = fx("usd","irr")
            btc = crypto("bitcoin")
            gold,_ = metals()

            msg=None

            if last["usd"] and usd!=last["usd"]:
                msg=f"🔔 USD تغییر کرد: {usd}"

            if last["btc"] and btc!=last["btc"]:
                msg=f"🔔 BTC تغییر کرد: {btc}"

            if last["gold"] and gold!=last["gold"]:
                msg=f"🔔 GOLD تغییر کرد: {gold}"

            last["usd"]=usd
            last["btc"]=btc
            last["gold"]=gold

            if msg:
                for c in subs:
                    await app.bot.send_message(c,msg)

        except:
            pass

        await asyncio.sleep(60)

# ===================== APP =====================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

async def post_init(app):
    asyncio.create_task(watcher(app))

app.post_init = post_init

print("Bot running...")
app.run_polling()
