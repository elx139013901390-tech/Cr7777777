import os
import asyncio
import requests
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# ===================== REAL LISTS =====================
FX = ["USD","EUR","GBP","JPY","TRY","CAD","AUD","CHF","CNY"]

CRYPTO = [
    "bitcoin","ethereum","bnb","solana","xrp","dogecoin",
    "cardano","tron","litecoin","polkadot",
    "chainlink","stellar","shiba-inu","near","matic-network"
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

# ===================== APIs (REAL ONLY) =====================
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
        return requests.get("https://api.metals.live/v1/spot").json()[0]
    except:
        return {"gold":0,"silver":0,"oil":0}

def usd_to_irr():
    v = fx("USD","IRR")
    return v if v else 0

# ===================== GOLD IRR ONLY =====================
def gold_irr():
    g = metals()["gold"]
    return g * usd_to_irr()

# ===================== CHART =====================
def chart():
    data = []
    for _ in range(6):
        v = fx("USD","IRR")
        if v:
            data.append(v)

    plt.plot(data)
    plt.title("USD → IRR REAL")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ===================== UI =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز جهانی","₿ کریپتو"],
        ["🥇 طلا (IRR)","🌍 کشورها (IRR)"],
        ["📊 نمودار","🔔 وضعیت بازار"]
    ],
    resize_keyboard=True
)

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_chat.id)

    await update.message.reply_text(
        "🚀 REAL FINANCE PRO BOT\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )

# ===================== HANDLER =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last
    text = update.message.text

    # 💱 FX → IRR
    if text == "💱 ارز جهانی":
        irr = usd_to_irr()
        out = []

        for c in FX:
            v = fx("USD", c)
            if v and irr:
                out.append(f"USD→{c} = {v * irr:,.0f} IRR")

        await update.message.reply_text("\n".join(out))

    # ₿ CRYPTO REAL
    elif text == "₿ کریپتو":
        out = []
        for c in CRYPTO[:12]:
            v = crypto(c)
            if v:
                out.append(f"{c.upper()} = ${v}")
        await update.message.reply_text("\n".join(out))

    # 🥇 GOLD ONLY IRR (IMPORTANT FIX YOU WANTED)
    elif text == "🥇 طلا (IRR)":
        await update.message.reply_text(
            f"🥇 Gold (IRR): {gold_irr():,.0f}"
        )

    # 🌍 COUNTRIES IRR
    elif text == "🌍 کشورها (IRR)":
        irr = usd_to_irr()

        out = []
        for name, code in COUNTRIES.items():
            v = fx("USD", code)
            if v and irr:
                out.append(f"{name} = {v * irr:,.0f} IRR")

        await update.message.reply_text("\n".join(out))

    # 📊 CHART
    elif text == "📊 نمودار":
        path = chart()
        await update.message.reply_photo(photo=open(path,"rb"))

    # 🔔 STATUS + SIMPLE AI
    elif text == "🔔 وضعیت بازار":
        usd = usd_to_irr()
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

# ===================== LIVE ALERT SYSTEM (5 MIN FIXED) =====================
async def watcher(app):
    global last

    while True:
        try:
            usd = usd_to_irr()
            btc = crypto("bitcoin")
            gold = gold_irr()

            msg = None

            if last["usd"] and usd and usd != last["usd"]:
                msg = f"🔔 دلار تغییر کرد: {usd:,.0f} IRR"

            if last["btc"] and btc and btc != last["btc"]:
                msg = f"🔔 بیت‌کوین تغییر کرد: ${btc}"

            if last["gold"] and gold and gold != last["gold"]:
                msg = f"🔔 طلا تغییر کرد: {gold:,.0f} IRR"

            last["usd"], last["btc"], last["gold"] = usd, btc, gold

            if msg:
                for u in users:
                    await app.bot.send_message(u, msg)

        except:
            pass

        # ⏱ هر 5 دقیقه (طبق خواسته تو)
        await asyncio.sleep(300)

# ===================== RUN =====================
app = Application.builder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle))

async def post_init(app):
    asyncio.create_task(watcher(app))

app.post_init = post_init

print("🚀 FINAL REAL BOT RUNNING...")
app.run_polling()
