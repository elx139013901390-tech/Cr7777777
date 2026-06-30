import os
import requests
import matplotlib.pyplot as plt
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

# ذخیره قیمت قبلی برای هشدار
last_price = {"usd_irr": None}


# ===================== FX =====================
def fx(base, target):
    url = f"https://fxapi.app/api/{base}/{target}.json"
    return requests.get(url).json()["rate"]


# ===================== CRYPTO =====================
def crypto(coin):
    url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin}&vs_currencies=usd"
    return requests.get(url).json()[coin]["usd"]


# ===================== GOLD =====================
def gold():
    url = "https://api.metals.live/v1/spot"
    data = requests.get(url).json()
    return data[0]["gold"], data[0]["silver"]


# ===================== CHART =====================
def make_chart():

    prices = [fx("usd", "irr") for _ in range(5)]  # شبیه‌سازی داده

    plt.plot(prices)
    plt.title("USD/IRR Live Chart")

    path = "chart.png"
    plt.savefig(path)
    plt.close()

    return path


# ===================== AI PREDICT =====================
def predict_price():

    rate = fx("usd", "irr")

    # پیش‌بینی ساده (AI-like)
    prediction_up = rate * 1.03
    prediction_down = rate * 0.97

    return rate, prediction_up, prediction_down


# ===================== ALERT SYSTEM =====================
def check_alert():

    rate = fx("usd", "irr")

    old = last_price["usd_irr"]

    last_price["usd_irr"] = rate

    if old is None:
        return "📊 شروع مانیتور"

    if rate > old:
        return f"📈 دلار بالا رفت: {rate}"
    elif rate < old:
        return f"📉 دلار پایین آمد: {rate}"
    else:
        return "⏸ بدون تغییر"


# ===================== START MENU =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton("💱 ارز", callback_data="fx")],
        [InlineKeyboardButton("₿ کریپتو", callback_data="crypto")],
        [InlineKeyboardButton("🥇 طلا", callback_data="gold")],
        [InlineKeyboardButton("📊 نمودار", callback_data="chart")],
        [InlineKeyboardButton("🧠 پیش‌بینی", callback_data="predict")],
        [InlineKeyboardButton("🔔 وضعیت بازار", callback_data="alert")],
    ]

    await update.message.reply_text(
        "📊 ربات مالی حرفه‌ای (AI)",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ===================== BUTTON HANDLER =====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    data = query.data

    # ---------------- FX ----------------
    if data == "fx":
        rate = fx("usd", "irr")
        await query.edit_message_text(f"💱 دلار: {rate} تومان")

    # ---------------- CRYPTO ----------------
    elif data == "crypto":
        price = crypto("bitcoin")
        await query.edit_message_text(f"₿ Bitcoin: ${price}")

    # ---------------- GOLD ----------------
    elif data == "gold":
        g, s = gold()
        await query.edit_message_text(f"🥇 طلا: {g}$\n🥈 نقره: {s}$")

    # ---------------- CHART ----------------
    elif data == "chart":
        path = make_chart()
        await query.message.reply_photo(photo=open(path, "rb"))

    # ---------------- PREDICT ----------------
    elif data == "predict":

        rate, up, down = predict_price()

        await query.edit_message_text(
            f"""
🧠 AI Prediction

الان: {rate}
📈 بالا: {up:.0f}
📉 پایین: {down:.0f}

⚠️ تخمینی
"""
        )

    # ---------------- ALERT ----------------
    elif data == "alert":

        msg = check_alert()

        await query.edit_message_text(msg)


# ===================== APP =====================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot is running...")
app.run_polling()
