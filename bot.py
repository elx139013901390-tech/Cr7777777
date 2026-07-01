import logging
import aiohttp
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ==================== تنظیمات اصلی ====================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# تنظیم لاگ‌گذاری
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# ==================== نقشه نام‌های فارسی به انگلیسی ====================
PERSIAN_TO_SYMBOL = {
    # ارزهای فیات و طلا
    "دلار": "USD",
    "يورو": "EUR",
    "یورو": "EUR",
    "پوند": "GBP",
    "ین": "JPY",
    "یوان": "CNY",
    "درهم": "AED",
    "لیر": "TRY",
    "روبل": "RUB",
    "فرانک": "CHF",
    "دلار کانادا": "CAD",
    "دلار استرالیا": "AUD",
    "کرون": "SEK",
    "رینگیت": "MYR",
    "روپیه": "INR",
    "ریال سعودی": "SAR",
    "دینار کویت": "KWD",
    "طلا": "XAU",
    "نقره": "XAG",
    "پلاتین": "XPT",
    "سکه": "COIN",  # handled specially
    # کریپتو
    "بیت کوین": "BTC",
    "بیتکوین": "BTC",
    "bitcoin": "BTC",
    "btc": "BTC",
    "اتریوم": "ETH",
    "اتریم": "ETH",
    "ethereum": "ETH",
    "eth": "ETH",
    "تتر": "USDT",
    "تدر": "USDT",
    "usdt": "USDT",
    "بی ان بی": "BNB",
    "bnb": "BNB",
    "ریپل": "XRP",
    "xrp": "XRP",
    "ادا": "ADA",
    "کاردانو": "ADA",
    "ada": "ADA",
    "سولانا": "SOL",
    "sol": "SOL",
    "دوج کوین": "DOGE",
    "دوج": "DOGE",
    "doge": "DOGE",
    "شیبا": "SHIB",
    "shib": "SHIB",
    "پولیگان": "MATIC",
    "ماتیک": "MATIC",
    "matic": "MATIC",
    "اوالانچ": "AVAX",
    "avax": "AVAX",
    "لینک": "LINK",
    "link": "LINK",
    "یونی سواپ": "UNI",
    "uni": "UNI",
    "لایت کوین": "LTC",
    "ltc": "LTC",
    "اتم": "ATOM",
    "کازماس": "ATOM",
    "atom": "ATOM",
    "ترون": "TRX",
    "trx": "TRX",
    "استلار": "XLM",
    "xlm": "XLM",
    "مونرو": "XMR",
    "xmr": "XMR",
    "دش": "DASH",
    "dash": "DASH",
    "زی کش": "ZEC",
    "zec": "ZEC",
    "فایل کوین": "FIL",
    "fil": "FIL",
    "تزوس": "XTZ",
    "xtz": "XTZ",
    "وی چین": "VET",
    "vet": "VET",
    "ایوس": "EOS",
    "eos": "EOS",
    "نئو": "NEO",
    "neo": "NEO",
    "هبار": "HBAR",
    "hbar": "HBAR",
    "الگورند": "ALGO",
    "algo": "ALGO",
    "فلوچین": "FLOW",
    "flow": "FLOW",
    "سندباکس": "SAND",
    "sand": "SAND",
    "دیسنترالند": "MANA",
    "mana": "MANA",
    "اکسی اینفینیتی": "AXS",
    "axs": "AXS",
    "گالا": "GALA",
    "gala": "GALA",
    "چیلیز": "CHZ",
    "chz": "CHZ",
    "انجین": "ENJ",
    "enj": "ENJ",
    "بیت کوین کش": "BCH",
    "btc cash": "BCH",
    "bch": "BCH",
    "اتریوم کلاسیک": "ETC",
    "etc": "ETC",
    "پانکیک سواپ": "CAKE",
    "cake": "CAKE",
    "کرو": "CRV",
    "crv": "CRV",
    "آوه": "AAVE",
    "aave": "AAVE",
    "کامپاند": "COMP",
    "comp": "COMP",
    "میکر": "MKR",
    "mkr": "MKR",
    "ییرن": "YFI",
    "yfi": "YFI",
    "سوشی سواپ": "SUSHI",
    "sushi": "SUSHI",
    "وان اینچ": "1INCH",
    "1inch": "1INCH",
    "اینترنت کامپیوتر": "ICP",
    "icp": "ICP",
    "نیر پروتکل": "NEAR",
    "near": "NEAR",
    "فانتوم": "FTM",
    "ftm": "FTM",
    "هارمونی": "ONE",
    "one": "ONE",
    "زیلیکا": "ZIL",
    "zil": "ZIL",
    "ایوتا": "MIOTA",
    "iota": "MIOTA",
    "نانو": "NANO",
    "nano": "NANO",
    "کوانت": "QNT",
    "qnt": "QNT",
    "فچ": "FET",
    "fetch": "FET",
    "fet": "FET",
    "اوشن": "OCEAN",
    "ocean": "OCEAN",
    "گراف": "GRT",
    "grt": "GRT",
    "ارو": "ARB",
    "آربیتروم": "ARB",
    "arb": "ARB",
    "اپتیمیزم": "OP",
    "op": "OP",
    "اینجکتیو": "INJ",
    "inj": "INJ",
    "سوئی": "SUI",
    "sui": "SUI",
    "آپتوس": "APT",
    "apt": "APT",
    "پپه": "PEPE",
    "pepe": "PEPE",
    "فلوکی": "FLOKI",
    "floki": "FLOKI",
    "بونک": "BONK",
    "bonk": "BONK",
    "دوگ ویف هت": "WIF",
    "wif": "WIF",
    "جوپیتر": "JUP",
    "jup": "JUP",
    "ورم هول": "W",
    "wormhole": "W",
    "رندر": "RNDR",
    "rndr": "RNDR",
    "آکاش": "AKT",
    "akt": "AKT",
    "celsia": "CEL",
    "سلسیوس": "CEL",
    "تون کوین": "TON",
    "تون": "TON",
    "ton": "TON",
    "نات کوین": "NOT",
    "not": "NOT",
    "همستر": "HMSTR",
    "hmstr": "HMSTR",
    "کاتس": "CATS",
    "cats": "CATS",
    "بلوم": "BLUM",
}

# نرخ تبدیل دلار به تومان (به‌روز شده از API)
USD_TO_TOMAN = 174300  # مقدار پیش‌فرض

# ==================== صرافی‌ها برای هر ارز ====================
EXCHANGES = {
    "BTC": [
        ("Toobit", "https://www.toobit.com"),
        ("LBank", "https://www.lbank.com"),
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("تو‌اکیس 🇮🇷", "https://toowex.com"),
        ("XT", "https://www.xt.com"),
    ],
    "ETH": [
        ("Toobit", "https://www.toobit.com"),
        ("Binance", "https://www.binance.com"),
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("تو‌اکیس 🇮🇷", "https://toowex.com"),
        ("Bybit", "https://www.bybit.com"),
    ],
    "USDT": [
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("والکس 🇮🇷", "https://wallex.ir"),
        ("تو‌اکیس 🇮🇷", "https://toowex.com"),
        ("Binance", "https://www.binance.com"),
        ("OKX", "https://www.okx.com"),
    ],
    "DEFAULT_CRYPTO": [
        ("Toobit", "https://www.toobit.com"),
        ("LBank", "https://www.lbank.com"),
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("تو‌اکیس 🇮🇷", "https://toowex.com"),
        ("XT", "https://www.xt.com"),
    ],
    "DEFAULT_FIAT": [
        ("والکس 🇮🇷", "https://wallex.ir"),
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("بانک ملی", "https://www.bmi.ir"),
    ],
    "XAU": [
        ("طلا ۲۴", "https://tala24.com"),
        ("قیمت طلا", "https://qemat-tala.ir"),
        ("گلدیران", "https://goldiran.ir"),
    ],
}

# ==================== توابع کمکی ====================

def format_number(num: float) -> str:
    """فرمت‌بندی اعداد با جداکننده هزار"""
    if num >= 1_000_000:
        return f"{num:,.0f}"
    elif num >= 1000:
        return f"{num:,.0f}"
    elif num >= 1:
        return f"{num:,.4f}"
    else:
        return f"{num:.8f}"


def get_exchanges_for_symbol(symbol: str) -> list:
    """گرفتن صرافی‌های مناسب برای ارز"""
    if symbol in EXCHANGES:
        return EXCHANGES[symbol]
    # بررسی اینکه آیا کریپتو است یا فیات
    fiat_symbols = ["USD", "EUR", "GBP", "JPY", "CNY", "AED", "TRY", "RUB",
                    "CHF", "CAD", "AUD", "SEK", "MYR", "INR", "SAR", "KWD"]
    if symbol in fiat_symbols:
        return EXCHANGES["DEFAULT_FIAT"]
    elif symbol in ["XAU", "XAG", "XPT"]:
        return EXCHANGES["XAU"]
    else:
        return EXCHANGES["DEFAULT_CRYPTO"]


async def get_usd_to_toman() -> float:
    """گرفتن نرخ دلار به تومان"""
    global USD_TO_TOMAN
    try:
        async with aiohttp.ClientSession() as session:
            # استفاده از API برای گرفتن نرخ دلار به تومان
            url = "https://api.coinbase.com/v2/exchange-rates?currency=USD"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # این API نرخ IRR را ارائه می‌دهد
                    irr = float(data.get("data", {}).get("rates", {}).get("IRR", USD_TO_TOMAN * 10))
                    USD_TO_TOMAN = irr / 10  # تبدیل ریال به تومان
                    return USD_TO_TOMAN
    except Exception as e:
        logger.warning(f"خطا در دریافت نرخ دلار: {e}")

    # تلاش با API دیگر
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://open.er-api.com/v6/latest/USD"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    irr = float(data.get("rates", {}).get("IRR", USD_TO_TOMAN * 10))
                    USD_TO_TOMAN = irr / 10
                    return USD_TO_TOMAN
    except Exception as e:
        logger.warning(f"خطا در دریافت نرخ دلار (API دوم): {e}")

    return USD_TO_TOMAN


async def get_crypto_price(symbol: str) -> dict:
    """گرفتن قیمت کریپتو از CoinGecko"""
    coin_id_map = {
        "BTC": "bitcoin", "ETH": "ethereum", "USDT": "tether",
        "BNB": "binancecoin", "XRP": "ripple", "ADA": "cardano",
        "SOL": "solana", "DOGE": "dogecoin", "SHIB": "shiba-inu",
        "MATIC": "matic-network", "AVAX": "avalanche-2", "LINK": "chainlink",
        "UNI": "uniswap", "LTC": "litecoin", "ATOM": "cosmos",
        "TRX": "tron", "XLM": "stellar", "XMR": "monero",
        "DASH": "dash", "ZEC": "zcash", "FIL": "filecoin",
        "XTZ": "tezos", "VET": "vechain", "EOS": "eos",
        "NEO": "neo", "HBAR": "hedera-hashgraph", "ALGO": "algorand",
        "FLOW": "flow", "SAND": "the-sandbox", "MANA": "decentraland",
        "AXS": "axie-infinity", "GALA": "gala", "CHZ": "chiliz",
        "ENJ": "enjincoin", "BCH": "bitcoin-cash", "ETC": "ethereum-classic",
        "CAKE": "pancakeswap-token", "CRV": "curve-dao-token",
        "AAVE": "aave", "COMP": "compound-governance-token",
        "MKR": "maker", "YFI": "yearn-finance", "SUSHI": "sushi",
        "1INCH": "1inch", "ICP": "internet-computer", "NEAR": "near",
        "FTM": "fantom", "ONE": "harmony", "ZIL": "zilliqa",
        "MIOTA": "iota", "NANO": "nano", "QNT": "quant-network",
        "FET": "fetch-ai", "OCEAN": "ocean-protocol", "GRT": "the-graph",
        "ARB": "arbitrum", "OP": "optimism", "INJ": "injective-protocol",
        "SUI": "sui", "APT": "aptos", "PEPE": "pepe",
        "FLOKI": "floki", "BONK": "bonk", "WIF": "dogwifcoin",
        "JUP": "jupiter-exchange-solana", "W": "wormhole",
        "RNDR": "render-token", "AKT": "akash-network",
        "TON": "the-open-network", "NOT": "notcoin",
        "HMSTR": "hamster-kombat", "CATS": "cats-2024",
        "XAU": "gold", "XAG": "silver",
    }

    coin_id = coin_id_map.get(symbol.upper())
    if not coin_id:
        coin_id = symbol.lower()

    try:
        async with aiohttp.ClientSession() as session:
            # گرفتن قیمت فعلی و تغییر 24 ساعته
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if coin_id in data:
                        price = data[coin_id].get("usd", 0)
                        change_24h = data[coin_id].get("usd_24h_change", 0)
                        return {
                            "price_usd": price,
                            "change_24h": change_24h,
                            "symbol": symbol.upper(),
                            "found": True,
                        }
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت کریپتو {symbol}: {e}")

    # تلاش با API دیگر (CryptoCompare)
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://min-api.cryptocompare.com/data/price?fsym={symbol.upper()}&tsyms=USD"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    if "USD" in data:
                        return {
                            "price_usd": data["USD"],
                            "change_24h": 0,
                            "symbol": symbol.upper(),
                            "found": True,
                        }
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت از CryptoCompare {symbol}: {e}")

    return {"found": False, "symbol": symbol.upper()}


async def get_fiat_price(symbol: str) -> dict:
    """گرفتن قیمت ارز فیات"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://open.er-api.com/v6/latest/USD"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    rates = data.get("rates", {})
                    if symbol in rates:
                        # قیمت ارز نسبت به دلار
                        rate = rates[symbol]
                        price_in_usd = 1.0 / rate if rate != 0 else 0
                        return {
                            "price_usd": price_in_usd,
                            "change_24h": 0,
                            "symbol": symbol,
                            "found": True,
                        }
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت فیات {symbol}: {e}")

    # اگر USD بود
    if symbol == "USD":
        return {
            "price_usd": 1.0,
            "change_24h": 0,
            "symbol": "USD",
            "found": True,
        }

    return {"found": False, "symbol": symbol}


async def get_gold_price() -> dict:
    """گرفتن قیمت طلا"""
    # طلا به اونس در برابر دلار
    result = await get_crypto_price("XAU")
    if result.get("found"):
        return result

    # مقدار پیش‌فرض
    return {
        "price_usd": 2350.0,
        "change_24h": 0,
        "symbol": "XAU",
        "found": True,
    }


async def get_iran_coin_price(usd_to_toman: float) -> dict:
    """محاسبه قیمت سکه بهار آزادی"""
    # قیمت سکه بهار آزادی معمولاً حدود 70-80 میلیون تومان است
    # این عدد بر اساس قیمت طلا محاسبه می‌شود
    gold_data = await get_gold_price()
    gold_price_usd = gold_data.get("price_usd", 2350)

    # سکه بهار آزادی = 8.133 گرم طلا ۹۰۰
    coin_weight_grams = 8.133
    gold_purity = 0.900
    gold_per_gram_usd = gold_price_usd / 31.1035  # تبدیل اونس به گرم
    coin_price_usd = coin_weight_grams * gold_purity * gold_per_gram_usd

    return {
        "price_usd": coin_price_usd,
        "change_24h": gold_data.get("change_24h", 0),
        "symbol": "COIN",
        "found": True,
        "name": "سکه بهار آزادی",
    }


async def search_crypto_by_name(query: str) -> dict:
    """جستجوی کریپتو بر اساس نام"""
    try:
        async with aiohttp.ClientSession() as session:
            url = f"https://api.coingecko.com/api/v3/search?query={query}"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    coins = data.get("coins", [])
                    if coins:
                        best_match = coins[0]
                        coin_id = best_match["id"]
                        symbol = best_match["symbol"].upper()

                        # گرفتن قیمت با coin_id
                        price_url = f"https://api.coingecko.com/api/v3/simple/price?ids={coin_id}&vs_currencies=usd&include_24hr_change=true"
                        async with session.get(price_url, timeout=aiohttp.ClientTimeout(total=15)) as price_resp:
                            if price_resp.status == 200:
                                price_data = await price_resp.json()
                                if coin_id in price_data:
                                    price = price_data[coin_id].get("usd", 0)
                                    change_24h = price_data[coin_id].get("usd_24h_change", 0)
                                    return {
                                        "price_usd": price,
                                        "change_24h": change_24h,
                                        "symbol": symbol,
                                        "name": best_match.get("name", symbol),
                                        "found": True,
                                    }
    except Exception as e:
        logger.error(f"خطا در جستجوی کریپتو {query}: {e}")

    return {"found": False, "symbol": query.upper()}


def build_exchange_keyboard(symbol: str) -> InlineKeyboardMarkup:
    """ساخت کیبورد صرافی‌ها"""
    exchanges = get_exchanges_for_symbol(symbol)
    buttons = []
    row = []
    for i, (name, url) in enumerate(exchanges):
        row.append(InlineKeyboardButton(name, url=url))
        if len(row) == 2 or i == len(exchanges) - 1:
            buttons.append(row)
            row = []

    return InlineKeyboardMarkup(buttons) if buttons else None


def format_price_message(
    symbol: str,
    price_usd: float,
    change_24h: float,
    usd_to_toman: float,
    display_name: str = None,
    coin_name: str = None,
) -> str:
    """فرمت‌بندی پیام قیمت"""

    price_toman = price_usd * usd_to_toman
    profit_usd = price_usd * (abs(change_24h) / 100)
    profit_toman = profit_usd * usd_to_toman

    # تعیین نام نمایشی
    if display_name:
        name_str = f"#{display_name}"
    elif coin_name:
        name_str = f"#{coin_name}"
    else:
        name_str = f"#{symbol}"

    # تعیین آیکون تغییر قیمت
    if change_24h > 0:
        change_icon = "🔺"
        change_label = "افزایش قیمت"
        profit_icon = "🟢"
    elif change_24h < 0:
        change_icon = "🔻"
        change_label = "کاهش قیمت"
        profit_icon = "🔴"
    else:
        change_icon = "⚪️"
        change_label = "تغییر قیمت"
        profit_icon = "🟢"

    # فرمت‌بندی قیمت
    if price_usd >= 1:
        price_str = f"{price_usd:,.2f}$"
    elif price_usd >= 0.01:
        price_str = f"{price_usd:,.4f}$"
    else:
        price_str = f"{price_usd:.8f}$"

    toman_str = f"{price_toman:,.0f} Toman"
    change_str = f"{abs(change_24h):.2f}%"

    if profit_usd >= 1:
        profit_str = f"{profit_usd:,.2f}$"
    elif profit_usd >= 0.001:
        profit_str = f"{profit_usd:,.4f}$"
    else:
        profit_str = f"{profit_usd:.8f}$"

    profit_toman_str = f"{profit_toman:,.0f} Toman"

    message = (
        f"💰 1 {name_str} = {price_str}\n"
        f"💶 {toman_str}\n\n"
        f"{change_icon} {change_label}: {change_str}\n"
        f"{profit_icon} میزان سود: {profit_str} [{profit_toman_str}]\n\n"
        f"♻️ بهترین صرافی‌ها برای معامله این ارز 📊"
    )

    return message


# ==================== هندلرهای ربات ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /start"""
    user = update.effective_user
    first_name = user.first_name if user.first_name else "دوست عزیز"

    welcome_message = (
        f"سلام {first_name} جون 😎🙌🏻\n\n"
        f"من قیمت تمام چیزا رو دارم 😎💸\n"
        f"از طلا ⚜️ سکه 🥇 دلار 💰 گرفته تا بیتکوین 💎 و اتریوم ⭐️ و حتی ناشناخته‌ترین ارزها 😎🔥\n\n"
        f"فقط کافیه اسمشو واسم بنویسی که قیمت دقیقشو بهت بگم 😃👇🏻\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 نمونه:\n"
        f"• دلار\n"
        f"• طلا\n"
        f"• سکه\n"
        f"• بیت کوین\n"
        f"• اتریوم\n"
        f"• BTC\n"
        f"• ETH\n"
        f"• DOGE\n"
        f"• ... و هر ارز دیگه‌ای\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"🤖 ساخته شده توسط: امیر علی فروزان اصل"
    )

    await update.message.reply_text(welcome_message)


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /help"""
    help_text = (
        "📚 راهنمای استفاده:\n\n"
        "کافیه نام ارز، طلا یا هر چیزی رو بنویسی!\n\n"
        "💡 مثال‌ها:\n"
        "• دلار - یورو - پوند\n"
        "• طلا - نقره\n"
        "• سکه بهار آزادی\n"
        "• بیت کوین / BTC\n"
        "• اتریوم / ETH\n"
        "• تتر / USDT\n"
        "• دوج کوین / DOGE\n"
        "• و صدها ارز دیگر...\n\n"
        "🤖 ساخته شده توسط: امیر علی فروزان اصل"
    )
    await update.message.reply_text(help_text)


async def price_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /price"""
    if context.args:
        query = " ".join(context.args)
        await process_price_query(update, context, query)
    else:
        await update.message.reply_text(
            "💡 لطفاً نام ارز را وارد کنید.\n"
            "مثال: /price BTC یا /price دلار"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر پیام‌های متنی"""
    if update.message and update.message.text:
        query = update.message.text.strip()
        await process_price_query(update, context, query)


async def process_price_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE, query: str
) -> None:
    """پردازش درخواست قیمت"""

    # نمایش پیام در حال پردازش
    processing_msg = await update.message.reply_text(
        "🔄 در حال دریافت قیمت..."
    )

    try:
        query_lower = query.lower().strip()
        symbol = None
        display_name = None
        coin_name = None
        is_crypto = True

        # بررسی نقشه فارسی به انگلیسی
        for persian_key, eng_symbol in PERSIAN_TO_SYMBOL.items():
            if query_lower == persian_key.lower() or query_lower == eng_symbol.lower():
                symbol = eng_symbol
                display_name = persian_key if any(
                    '\u0600' <= c <= '\u06FF' for c in persian_key
                ) else None
                if not display_name:
                    display_name = eng_symbol
                break

        # اگر پیدا نشد، بررسی مستقیم نماد
        if not symbol:
            symbol = query.upper()
            display_name = query.upper()

        # گرفتن نرخ دلار به تومان
        usd_to_toman = await get_usd_to_toman()

        price_data = None

        # هندل سکه بهار آزادی
        if symbol == "COIN" or query_lower in ["سکه", "سکه بهار آزادی", "coin"]:
            price_data = await get_iran_coin_price(usd_to_toman)
            symbol = "COIN"
            display_name = "سکه"
            coin_name = "سکه بهار آزادی"
            is_crypto = False

        # هندل طلا
        elif symbol == "XAU" or query_lower in ["طلا", "gold", "xau"]:
            price_data = await get_gold_price()
            display_name = "طلا"
            is_crypto = False

        # ارزهای فیات
        elif symbol in ["USD", "EUR", "GBP", "JPY", "CNY", "AED", "TRY", "RUB",
                         "CHF", "CAD", "AUD", "SEK", "MYR", "INR", "SAR", "KWD",
                         "XAG", "XPT"]:
            price_data = await get_fiat_price(symbol)
            is_crypto = False

        else:
            # تلاش برای کریپتو
            price_data = await get_crypto_price(symbol)

            # اگر پیدا نشد، جستجوی پیشرفته
            if not price_data.get("found"):
                price_data = await search_crypto_by_name(query)
                if price_data.get("found"):
                    symbol = price_data.get("symbol", symbol)
                    coin_name = price_data.get("name", symbol)
                    display_name = coin_name

        # بررسی نتیجه
        if price_data and price_data.get("found"):
            price_usd = price_data.get("price_usd", 0)
            change_24h = price_data.get("change_24h", 0)
            if coin_name is None:
                coin_name = price_data.get("name", symbol)

            message = format_price_message(
                symbol=symbol,
                price_usd=price_usd,
                change_24h=change_24h,
                usd_to_toman=usd_to_toman,
                display_name=display_name,
                coin_name=coin_name if not display_name else None,
            )

            # ساخت کیبورد صرافی‌ها
            keyboard = build_exchange_keyboard(symbol)

            await processing_msg.delete()

            if keyboard:
                await update.message.reply_text(
                    message,
                    reply_markup=keyboard,
                )
            else:
                await update.message.reply_text(message)

        else:
            await processing_msg.edit_text(
                f"❌ متأسفانه قیمت '{query}' پیدا نشد!\n\n"
                f"💡 لطفاً نام یا نماد دقیق‌تری وارد کنید.\n"
                f"مثال: BTC، ETH، DOGE، دلار، طلا، سکه..."
            )

    except Exception as e:
        logger.error(f"خطا در پردازش درخواست '{query}': {e}")
        try:
            await processing_msg.edit_text(
                "⚠️ خطایی رخ داد. لطفاً دوباره تلاش کنید."
            )
        except Exception:
            pass


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر خطاهای کلی"""
    logger.error(f"خطا: {context.error}")


# ==================== تابع اصلی ====================

def main() -> None:
    """تابع اصلی برای راه‌اندازی ربات"""

    # ساخت Application
    application = Application.builder().token(BOT_TOKEN).build()

    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("price", price_command))

    # هندلر پیام‌های متنی (فقط پیام‌های غیر دستوری)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    )

    # هندلر خطا
    application.add_error_handler(error_handler)

    logger.info("ربات شروع به کار کرد... 🚀")
    logger.info("ساخته شده توسط: امیر علی فروزان اصل")

    # شروع ربات
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
