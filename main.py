import os
import requests

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes
)

TOKEN = os.getenv("BOT_TOKEN")


# ===================== FIAT CURRENCY =====================
def get_fx(base, target):

    url = f"https://fxapi.app/api/{base}/{target}.json"
    res = requests.get(url)
    data = res.json()

    return data["rate"]


# ===================== CRYPTO =====================
def get_crypto(coin):

    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"

    res = requests.get(url)
    data = res.json()

    return data[coin]["usd"]


# ===================== COMMAND: CURRENCY =====================
async def currency(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        _, base, target, amount = update.message.text.split()

        rate = get_fx(base.lower(), target.lower())
        result = float(amount) * rate

        await update.message.reply_text(
            f"""
💱 تبدیل ارز

{amount} {base.upper()} = {result:.2f} {target.upper()}

📊 نرخ: {rate}

سازنده:
امیر علی فروزان اصل
"""
        )

    except:
        await update.message.reply_text(
            "❌ فرمت درست:\n/cur usd eur 100"
        )


# ===================== COMMAND: CRYPTO =====================
async def crypto(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        _, coin = update.message.text.split()

        price = get_crypto(coin.lower())

        await update.message.reply_text(
            f"""
₿ قیمت ارز دیجیتال

{coin.upper()} = ${price}

سازنده:
امیر علی فروزان اصل
"""
        )

    except:
        await update.message.reply_text(
            "❌ فرمت درست:\n/crypto bitcoin"
        )


# ===================== HELP =====================
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
📌 دستورات ربات:

💱 تبدیل ارز:
/cur usd eur 100
/cur usd irr 50

₿ کریپتو:
/crypto bitcoin
/crypto ethereum

🌍 ارزهای قابل استفاده:
usd | eur | gbp | jpy | irr | try

🔥 ساخته شده توسط:
امیر علی فروزان اصل
"""
    )


# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        """
👋 به ربات مالی خوش آمدی

📌 /help برای راهنما
💱 /cur برای تبدیل ارز
₿ /crypto برای قیمت ارز دیجیتال
"""
    )


# ===================== APP =====================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_cmd))
app.add_handler(CommandHandler("cur", currency))
app.add_handler(CommandHandler("crypto", crypto))

print("Bot is running...")
app.run_polling()
