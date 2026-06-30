import os
import asyncio
import requests

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
FX_LIST = ["usd", "eur", "gbp", "jpy", "try", "cad", "aud", "chf", "cny", "irr"]

CRYPTO = [
    "bitcoin", "ethereum", "tether", "bnb", "solana",
    "xrp", "dogecoin", "cardano", "tron", "litecoin",
    "polkadot", "avalanche-2", "chainlink", "stellar",
    "shiba-inu", "near", "matic-network", "uniswap",
    "aptos", "arbitrum", "kaspa", "okb", "fantom",
    "algorand", "leo-token"
]

COUNTRIES = {
    "USA": "USD",
    "EU": "EUR",
    "UK": "GBP",
    "Japan": "JPY",
    "Iran": "IRR",
    "China": "CNY",
    "Turkey": "TRY"
}

# ===================== STATE =====================
last_usd = None
subscribers = set()


# ===================== FX =====================
def fx(base, target):
    url = f"https://fxapi.app/api/{base}/{target}.json"
    return requests.get(url).json()["rate"]


# ===================== CRYPTO =====================
def crypto_price(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    return requests.get(url).json()[coin]["usd"]


# ===================== MENU =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز", "₿ کریپتو"],
        ["📊 لیست", "🌍 کشورها"],
        ["🧠 پیش‌بینی", "🔔 وضعیت"]
    ],
    resize_keyboard=True
)


# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    subscribers.add(update.effective_chat.id)

    await update.message.reply_text(
        "📊 ربات مالی حرفه‌ای\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )


# ===================== HANDLER =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global last_usd

    text = update.message.text


    # ---------------- FX ----------------
    if text == "💱 ارز":

        out = []
        for c in FX_LIST:
            try:
                out.append(f"USD → {c.upper()} = {fx('usd', c)}")
            except:
                pass

        await update.message.reply_text("\n".join(out))


    # ---------------- CRYPTO ----------------
    elif text == "₿ کریپتو":

        out = []
        for c in CRYPTO:
            try:
                out.append(f"{c.upper()} = ${crypto_price(c)}")
            except:
                pass

        await update.message.reply_text("\n".join(out))


    # ---------------- LIST ----------------
    elif text == "📊 لیست":

        await update.message.reply_text(
            "💱 USD EUR GBP JPY IRR CNY TRY\n"
            "₿ BTC ETH SOL XRP DOGE +25"
        )


    # ---------------- COUNTRIES ----------------
    elif text == "🌍 کشورها":

        msg = "\n".join([f"{k}: {v}" for k, v in COUNTRIES.items()])
        await update.message.reply_text(msg)


    # ---------------- PREDICTION ----------------
    elif text == "🧠 پیش‌بینی":

        rate = fx("usd", "irr")

        trend = "📈 صعودی" if last_usd and rate > last_usd else "📉 نزولی"

        future = rate * 1.02 if trend == "📈 صعودی" else rate * 0.98

        await update.message.reply_text(
            f"""
🧠 AI تحلیل

الان: {rate}
روند: {trend}
پیش‌بینی: {future:.0f}
"""
        )


    # ---------------- STATUS ----------------
    elif text == "🔔 وضعیت":

        rate = fx("usd", "irr")

        msg = f"📊 دلار: {rate}"

        if last_usd:
            if rate > last_usd:
                msg += "\n📈 بالا رفت"
            elif rate < last_usd:
                msg += "\n📉 پایین آمد"
            else:
                msg += "\n⏸ بدون تغییر"

        last_usd = rate

        await update.message.reply_text(msg)


# ===================== AUTO ALERT =====================
async def watcher(app):

    global last_usd

    while True:

        try:
            rate = fx("usd", "irr")

            if last_usd is not None:

                if rate != last_usd:

                    msg = f"""
🔔 تغییر قیمت دلار

قبلی: {last_usd}
جدید: {rate}
"""

                    for chat_id in subscribers:
                        await app.bot.send_message(chat_id, msg)

            last_usd = rate

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
