import os
import asyncio
import requests
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# ===================== REAL DATA =====================
FX_LIST = ["USD","EUR","GBP","JPY","TRY","CAD","AUD","CHF","CNY","IRR"]

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

# ===================== SAFE API =====================
def fx(base, target):
    try:
        r = requests.get(
            f"https://api.frankfurter.app/latest?from={base}&to={target}"
        ).json()
        return r["rates"][target]
    except:
        return None

def crypto(c):
    try:
        r = requests.get(
            f"https://api.coingecko.com/api/v3/simple/price?ids={c}&vs_currencies=usd"
        ).json()
        return r[c]["usd"]
    except:
        return None

def metals():
    try:
        r = requests.get("https://api.metals.live/v1/spot").json()[0]
        return r["gold"], r["silver"], r["oil"]
    except:
        return 0,0,0

def usd_to_irr():
    v = fx("USD","IRR")
    return v if v else 0

def gold_irr():
    g,_,_ = metals()
    return g * usd_to_irr()

# ===================== CHART =====================
def chart():
    data = []
    for _ in range(6):
        v = fx("USD","IRR")
        if v:
            data.append(v)

    plt.plot(data)
    plt.title("USD → IRR (REAL)")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ===================== MENU =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز جهانی","₿ کریپتو"],
        ["🥇 طلا و نفت","🌍 کشورها (IRR)"],
        ["📊 نمودار","🔔 وضعیت بازار"]
    ],
    resize_keyboard=True
)

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_chat.id)

    await update.message.reply_text(
        "🚀 GOD MODE PRO REAL SYSTEM\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )

# ===================== MAIN HANDLER =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last
    text = update.message.text

    # 💱 FX REAL
    if text == "💱 ارز جهانی":
        out = []
        for c in FX_LIST:
            v = fx("USD", c)
            if v:
                if c == "IRR":
                    v = usd_to_irr()
                out.append(f"USD → {c} = {v}")
        await update.message.reply_text("\n".join(out))

    # ₿ CRYPTO REAL (USD)
    elif text == "₿ کریپتو":
        out = []
        for c in CRYPTO[:15]:
            v = crypto(c)
            if v:
                out.append(f"{c.upper()} = ${v}")
        await update.message.reply_text("\n".join(out))

    # 🥇 GOLD + OIL (IRR)
    elif text == "🥇 طلا و نفت":
        g, s, o = metals()
        irr = usd_to_irr()

        msg = (
            f"🥇 Gold: {g * irr:,.0f} IRR\n"
            f"🥈 Silver: {s * irr:,.0f} IRR\n"
            f"🛢 Oil: {o * irr:,.0f} IRR"
        )

        await update.message.reply_text(msg)

    # 🌍 COUNTRIES → IRR
    elif text == "🌍 کشورها (IRR)":
        irr = usd_to_irr()

        out = []
        for name, code in COUNTRIES.items():
            v = fx("USD", code)
            if v:
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

# ===================== LIVE SYSTEM =====================
async def watcher(app):
    global last

    while True:
        try:
            usd = usd_to_irr()
            btc = crypto("bitcoin")
            gold = gold_irr()

            msg = None

            if last["usd"] and usd and usd != last["usd"]:
                msg = f"🔔 USD تغییر کرد: {usd:,.0f} IRR"

            if last["btc"] and btc and btc != last["btc"]:
                msg = f"🔔 BTC تغییر کرد: ${btc}"

            if last["gold"] and gold and gold != last["gold"]:
                msg = f"🔔 GOLD تغییر کرد: {gold:,.0f} IRR"

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

print("🚀 PRO REAL BOT RUNNING...")
app.run_polling()
