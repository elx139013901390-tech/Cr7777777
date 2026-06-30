import os
import asyncio
import requests
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# ===================== REAL DATA SOURCES =====================

FX_LIST = ["USD", "EUR", "GBP", "JPY", "TRY", "CAD", "AUD", "CHF", "CNY", "IRR"]

CRYPTO = [
    "bitcoin","ethereum","tether","bnb","solana","xrp","dogecoin","cardano",
    "tron","litecoin","polkadot","avalanche-2","chainlink","stellar",
    "shiba-inu","near","matic-network","uniswap","aptos","arbitrum",
    "kaspa","okb","fantom","algorand","leo-token"
]

# ذخیره قیمت‌ها برای AI + هشدار
last = {"usd": None, "btc": None, "gold": None}

subscribers = set()

# ===================== FX (REAL - FRANKFURTER API) =====================
def fx(base, target):
    url = f"https://api.frankfurter.app/latest?from={base}&to={target}"
    data = requests.get(url).json()
    return data["rates"][target]

# ===================== CRYPTO (REAL - COINGECKO) =====================
def crypto_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    return requests.get(url).json()[coin]["usd"]

# ===================== METALS (REAL) =====================
def metals():
    url = "https://api.metals.live/v1/spot"
    d = requests.get(url).json()[0]
    return d["gold"], d["silver"]

# ===================== OIL (REAL-ish) =====================
def oil():
    return requests.get("https://api.metals.live/v1/spot").json()[0]["oil"]

# ===================== CHART =====================
def chart_usd():
    prices = [fx("USD","IRR") for _ in range(6)]

    plt.plot(prices)
    plt.title("USD/IRR Live Chart")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ===================== MENU =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز", "₿ کریپتو"],
        ["🥇 طلا", "🛢 نفت"],
        ["📊 نمودار", "🌍 کشورها"],
        ["🧠 پیش‌بینی", "🔔 وضعیت"]
    ],
    resize_keyboard=True
)

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    subscribers.add(update.effective_chat.id)

    await update.message.reply_text(
        "📊 ربات مالی واقعی و حرفه‌ای\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )

# ===================== HANDLER =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last
    text = update.message.text

    # 💱 FX
    if text == "💱 ارز":
        out = []
        for c in FX_LIST:
            try:
                rate = fx("USD", c)
                out.append(f"USD → {c} = {rate}")
            except:
                pass
        await update.message.reply_text("\n".join(out))

    # ₿ CRYPTO
    elif text == "₿ کریپتو":
        out = []
        for c in CRYPTO[:15]:
            try:
                out.append(f"{c.upper()} = ${crypto_price(c)}")
            except:
                pass
        await update.message.reply_text("\n".join(out))

    # 🥇 GOLD
    elif text == "🥇 طلا":
        g, s = metals()
        await update.message.reply_text(f"🥇 Gold: {g}\n🥈 Silver: {s}")

    # 🛢 OIL
    elif text == "🛢 نفت":
        await update.message.reply_text(f"🛢 Oil: {oil()}")

    # 📊 CHART
    elif text == "📊 نمودار":
        path = chart_usd()
        await update.message.reply_photo(photo=open(path, "rb"))

    # 🌍 COUNTRIES
    elif text == "🌍 کشورها":
        await update.message.reply_text(
            "USD 🇺🇸\nEUR 🇪🇺\nGBP 🇬🇧\nJPY 🇯🇵\nIRR 🇮🇷\nCNY 🇨🇳\nTRY 🇹🇷"
        )

    # 🧠 AI PREDICTION (REAL TREND BASED)
    elif text == "🧠 پیش‌بینی":

        price_now = fx("USD","IRR")

        if last["usd"]:
            trend = "📈 صعودی" if price_now > last["usd"] else "📉 نزولی"
        else:
            trend = "📊 شروع داده"

        prediction = price_now * (1.02 if trend == "📈 صعودی" else 0.98)

        await update.message.reply_text(
            f"""
🧠 AI تحلیل واقعی

الان: {price_now}
روند: {trend}
پیش‌بینی: {prediction:.0f}
"""
        )

        last["usd"] = price_now

    # 🔔 STATUS (multi alert)
    elif text == "🔔 وضعیت":

        usd = fx("USD","IRR")
        btc = crypto_price("bitcoin")
        gold,_ = metals()

        msg = "📊 وضعیت بازار\n"

        if last["usd"]:
            msg += f"USD: {'📈' if usd>last['usd'] else '📉'}\n"

        if last["btc"]:
            msg += f"BTC: {'📈' if btc>last['btc'] else '📉'}\n"

        if last["gold"]:
            msg += f"GOLD: {'📈' if gold>last['gold'] else '📉'}\n"

        last["usd"], last["btc"], last["gold"] = usd, btc, gold

        await update.message.reply_text(msg)

# ===================== AUTO ALERT SYSTEM =====================
async def watcher(app):
    global last

    while True:
        try:
            usd = fx("USD","IRR")
            btc = crypto_price("bitcoin")
            gold,_ = metals()

            msg = None

            if last["usd"] and usd != last["usd"]:
                msg = f"🔔 USD تغییر کرد: {usd}"

            if last["btc"] and btc != last["btc"]:
                msg = f"🔔 BTC تغییر کرد: {btc}"

            if last["gold"] and gold != last["gold"]:
                msg = f"🔔 GOLD تغییر کرد: {gold}"

            last["usd"], last["btc"], last["gold"] = usd, btc, gold

            if msg:
                for c in subscribers:
                    await app.bot.send_message(c, msg)

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
