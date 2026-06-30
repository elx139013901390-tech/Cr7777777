import os
import asyncio
import requests
import matplotlib.pyplot as plt

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

# ===================== DATA =====================
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
    "Switzerland 🇨🇭":"CHF",
    "India 🇮🇳":"INR",
    "Russia 🇷🇺":"RUB",
    "Korea 🇰🇷":"KRW",
    "UAE 🇦🇪":"AED",
    "Saudi 🇸🇦":"SAR",
    "Brazil 🇧🇷":"BRL",
    "Mexico 🇲🇽":"MXN",
    "Sweden 🇸🇪":"SEK",
    "Norway 🇳🇴":"NOK",
    "New Zealand 🇳🇿":"NZD"
}

last = {"usd": None, "btc": None, "gold": None}
users = set()

# ===================== FX =====================
def fx(base, target):
    return requests.get(
        f"https://api.frankfurter.app/latest?from={base}&to={target}"
    ).json()["rates"][target]

# ===================== CRYPTO =====================
def crypto(c):
    return requests.get(
        f"https://api.coingecko.com/api/v3/simple/price?ids={c}&vs_currencies=usd"
    ).json()[c]["usd"]

# ===================== GOLD (IRR CONVERTED) =====================
def gold_irr():
    d = requests.get("https://api.metals.live/v1/spot").json()[0]
    gold_usd = d["gold"]

    usd_to_irr = fx("USD","IRR")
    return gold_usd * usd_to_irr

# ===================== CHART =====================
def chart():
    data = [fx("USD","IRR") for _ in range(6)]
    plt.plot(data)
    plt.title("USD/IRR LIVE")
    path = "chart.png"
    plt.savefig(path)
    plt.close()
    return path

# ===================== MENU =====================
menu = ReplyKeyboardMarkup(
    [
        ["💱 ارز","₿ کریپتو"],
        ["🥇 طلا (ریال)","🌍 کشورها (ریال)"],
        ["📊 نمودار","🧠 پیش‌بینی"],
        ["🔔 وضعیت"]
    ],
    resize_keyboard=True
)

# ===================== START =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_chat.id)
    await update.message.reply_text(
        "🚀 GOD MODE 2 REAL FIXED\n👤 امیر علی فروزان اصل",
        reply_markup=menu
    )

# ===================== HANDLE =====================
async def handle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global last
    text = update.message.text

    # 💱 FX (REAL IRR OUTPUT)
    if text == "💱 ارز":
        out = []
        for c in FX_LIST:
            try:
                rate = fx("USD", c)
                if c == "IRR":
                    rate = fx("USD","IRR")
                out.append(f"USD→{c} = {rate}")
            except:
                pass
        await update.message.reply_text("\n".join(out))

    # ₿ CRYPTO (USD)
    elif text == "₿ کریپتو":
        out = []
        for c in CRYPTO[:15]:
            out.append(f"{c.upper()} = ${crypto(c)}")
        await update.message.reply_text("\n".join(out))

    # 🥇 GOLD (IRR REAL)
    elif text == "🥇 طلا (ریال)":
        g_irr = gold_irr()
        await update.message.reply_text(f"🥇 Gold (IRR): {g_irr:,.0f}")

    # 🌍 COUNTRIES (IRR VALUE)
    elif text == "🌍 کشورها (ریال)":
        usd_to_irr = fx("USD","IRR")

        out = []
        for name, code in COUNTRIES.items():
            try:
                rate = fx("USD", code) * usd_to_irr
                out.append(f"{name} = {rate:,.0f} IRR")
            except:
                pass

        await update.message.reply_text("\n".join(out))

    # 📊 CHART
    elif text == "📊 نمودار":
        path = chart()
        await update.message.reply_photo(photo=open(path,"rb"))

    # 🧠 AI
    elif text == "🧠 پیش‌بینی":
        price = fx("USD","IRR")

        trend = "📈" if last["usd"] and price > last["usd"] else "📉"
        future = price * (1.03 if trend=="📈" else 0.97)

        await update.message.reply_text(
            f"🧠 AI\nالان: {price}\nروند: {trend}\nپیش‌بینی: {future:.0f}"
        )

        last["usd"] = price

    # 🔔 STATUS
    elif text == "🔔 وضعیت":

        usd = fx("USD","IRR")
        btc = crypto("bitcoin")
        gold = gold_irr()

        msg = "📊 وضعیت بازار\n"

        if last["usd"]:
            msg += f"USD: {'📈' if usd>last['usd'] else '📉'}\n"
        if last["btc"]:
            msg += f"BTC: {'📈' if btc>last['btc'] else '📉'}\n"
        if last["gold"]:
            msg += f"GOLD: {'📈' if gold>last['gold'] else '📉'}\n"

        last["usd"], last["btc"], last["gold"] = usd, btc, gold

        await update.message.reply_text(msg)

# ===================== AUTO ALERT =====================
async def watcher(app):
    global last

    while True:
        try:
            usd = fx("USD","IRR")
            btc = crypto("bitcoin")
            gold = gold_irr()

            msg = None

            if last["usd"] and usd != last["usd"]:
                msg = f"🔔 USD تغییر کرد: {usd:,.0f} IRR"

            if last["btc"] and btc != last["btc"]:
                msg = f"🔔 BTC تغییر کرد: {btc}"

            if last["gold"] and gold != last["gold"]:
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

print("GOD MODE 2 FIXED RUNNING...")
app.run_polling()
