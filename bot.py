```python
#!/usr/bin/env python3
"""
ربات قیمت طلا و سکه 📡
سازنده: امیر علی فروزان اصل
این ربات قیمت لحظه‌ای طلا، سکه، ارزهای دیجیتال و پول کشورها را نمایش می‌دهد
"""

import asyncio
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import httpx
import json

# ===== تنظیمات اصلی =====
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")


# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# نرخ دلار به تومان (می‌تواند از API دریافت شود)
USD_TO_TOMAN = 85000  # نرخ تقریبی - در نسخه واقعی از API دریافت می‌شود

# ===== نگاشت نام‌های فارسی به ID ارزهای دیجیتال =====
CRYPTO_NAMES_FA = {
    "بیت کوین": "bitcoin",
    "بیتکوین": "bitcoin",
    "بیت‌کوین": "bitcoin",
    "btc": "bitcoin",
    "اتریوم": "ethereum",
    "اتر": "ethereum",
    "eth": "ethereum",
    "تتر": "tether",
    "usdt": "tether",
    "بی‌ان‌بی": "binancecoin",
    "bnb": "binancecoin",
    "سولانا": "solana",
    "sol": "solana",
    "ریپل": "ripple",
    "xrp": "ripple",
    "دوج کوین": "dogecoin",
    "دوج": "dogecoin",
    "doge": "dogecoin",
    "کاردانو": "cardano",
    "ada": "cardano",
    "پالیگان": "matic-network",
    "ماتیک": "matic-network",
    "matic": "matic-network",
    "اوالانچ": "avalanche-2",
    "avax": "avalanche-2",
    "شیبا": "shiba-inu",
    "شیبا اینو": "shiba-inu",
    "shib": "shiba-inu",
    "ترون": "tron",
    "trx": "tron",
    "لایت کوین": "litecoin",
    "ltc": "litecoin",
    "چین لینک": "chainlink",
    "link": "chainlink",
    "پولکادات": "polkadot",
    "dot": "polkadot",
    "یونی سواپ": "uniswap",
    "uni": "uniswap",
    "اتم": "cosmos",
    "cosmos": "cosmos",
    "مونرو": "monero",
    "xmr": "monero",
    "اپتیمیزم": "optimism",
    "op": "optimism",
    "آربیتروم": "arbitrum",
    "arb": "arbitrum",
    "پپه": "pepe",
    "pepe": "pepe",
    "فلوکی": "floki",
    "floki": "floki",
    "notcoin": "notcoin",
    "ناتکوین": "notcoin",
    "تن کوین": "the-open-network",
    "تون": "the-open-network",
    "ton": "the-open-network",
}

# ===== نگاشت نام‌های فارسی به کد ارزهای فیات =====
FIAT_NAMES_FA = {
    "دلار": "USD",
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
    "وون": "KRW",
    "روپیه": "INR",
    "ریال سعودی": "SAR",
    "کرون": "SEK",
}

# ===== نگاشت نام‌های فارسی به کالاها =====
COMMODITY_NAMES_FA = {
    "طلا": "gold",
    "نقره": "silver",
    "نفت": "oil",
    "مس": "copper",
    "پلاتین": "platinum",
}

# ===== نام‌های سکه فارسی =====
COIN_NAMES_FA = {
    "سکه": "coin_emami",
    "سکه امامی": "coin_emami",
    "نیم سکه": "coin_half",
    "ربع سکه": "coin_quarter",
    "سکه گرمی": "coin_gram",
    "مثقال": "mithqal",
}

# ===== صرافی‌های پیشنهادی برای ارزهای دیجیتال =====
EXCHANGES = {
    "bitcoin": [
        ("Toobit", "https://www.toobit.com"),
        ("LBank", "https://www.lbank.com"),
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("تو‌اکسیر 🇮🇷", "https://toosexir.com"),
        ("XT", "https://www.xt.com"),
    ],
    "ethereum": [
        ("Toobit", "https://www.toobit.com"),
        ("LBank", "https://www.lbank.com"),
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("تو‌اکسیر 🇮🇷", "https://toosexir.com"),
        ("Binance", "https://www.binance.com"),
    ],
    "default": [
        ("نوبیتکس 🇮🇷", "https://nobitex.ir"),
        ("Toobit", "https://www.toobit.com"),
        ("LBank", "https://www.lbank.com"),
        ("XT", "https://www.xt.com"),
        ("تو‌اکسیر 🇮🇷", "https://toosexir.com"),
    ]
}


def format_number(num: float) -> str:
    """فرمت کردن اعداد با جداکننده هزارگان"""
    if num >= 1:
        return f"{num:,.0f}"
    elif num >= 0.01:
        return f"{num:.4f}"
    elif num >= 0.0001:
        return f"{num:.6f}"
    else:
        return f"{num:.8f}"


def get_exchanges_for_crypto(crypto_id: str) -> list:
    """دریافت صرافی‌های مناسب برای یک ارز دیجیتال"""
    return EXCHANGES.get(crypto_id, EXCHANGES["default"])


async def get_crypto_price(crypto_id: str) -> dict:
    """دریافت قیمت ارز دیجیتال از CoinGecko API"""
    try:
        url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}"
        params = {
            "localization": "false",
            "tickers": "false",
            "market_data": "true",
            "community_data": "false",
            "developer_data": "false",
        }
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                market_data = data.get("market_data", {})
                
                current_price = market_data.get("current_price", {}).get("usd", 0)
                price_change_24h = market_data.get("price_change_percentage_24h", 0) or 0
                price_change_usd = market_data.get("price_change_24h", 0) or 0
                
                symbol = data.get("symbol", "").upper()
                name = data.get("name", "")
                
                toman_price = current_price * USD_TO_TOMAN
                profit_toman = price_change_usd * USD_TO_TOMAN
                
                return {
                    "success": True,
                    "type": "crypto",
                    "name": name,
                    "symbol": symbol,
                    "price_usd": current_price,
                    "price_toman": toman_price,
                    "change_24h": price_change_24h,
                    "change_usd": price_change_usd,
                    "change_toman": profit_toman,
                    "crypto_id": crypto_id,
                }
            else:
                return {"success": False, "error": "ارز مورد نظر یافت نشد"}
    except Exception as e:
        logger.error(f"Error fetching crypto price: {e}")
        return {"success": False, "error": str(e)}


async def get_fiat_price(fiat_code: str) -> dict:
    """دریافت قیمت ارزهای فیات"""
    try:
        # استفاده از Exchange Rate API رایگان
        url = f"https://api.exchangerate-api.com/v4/latest/USD"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                rates = data.get("rates", {})
                
                if fiat_code in rates:
                    # قیمت ارز نسبت به دلار
                    rate = rates[fiat_code]
                    price_in_usd = 1 / rate if rate != 0 else 0
                    
                    # برای دلار
                    if fiat_code == "USD":
                        price_in_usd = 1.0
                    
                    toman_price = price_in_usd * USD_TO_TOMAN
                    
                    return {
                        "success": True,
                        "type": "fiat",
                        "symbol": fiat_code,
                        "price_usd": price_in_usd,
                        "price_toman": toman_price,
                        "change_24h": 0,  # نیاز به API پرمیوم
                        "change_usd": 0,
                        "change_toman": 0,
                    }
                else:
                    return {"success": False, "error": "ارز مورد نظر یافت نشد"}
            else:
                return {"success": False, "error": "خطا در دریافت اطلاعات"}
    except Exception as e:
        logger.error(f"Error fetching fiat price: {e}")
        return {"success": False, "error": str(e)}


async def get_gold_price() -> dict:
    """دریافت قیمت طلا"""
    try:
        # استفاده از API رایگان برای قیمت طلا
        url = "https://api.metals.live/v1/spot/gold"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                price_usd = data[0].get("price", 0) if isinstance(data, list) else data.get("price", 0)
                toman_price = price_usd * USD_TO_TOMAN
                
                return {
                    "success": True,
                    "type": "gold",
                    "symbol": "XAU",
                    "name": "طلا (هر اونس)",
                    "price_usd": price_usd,
                    "price_toman": toman_price,
                    "change_24h": 0,
                    "change_usd": 0,
                    "change_toman": 0,
                }
            else:
                # مقدار پیش‌فرض در صورت خطای API
                return await get_gold_fallback()
    except Exception as e:
        logger.error(f"Error fetching gold price: {e}")
        return await get_gold_fallback()


async def get_gold_fallback() -> dict:
    """مقدار پیش‌فرض برای طلا در صورت خطای API"""
    try:
        # تلاش با API دیگر
        url = "https://api.coingecko.com/api/v3/simple/price?ids=tether-gold&vs_currencies=usd&include_24hr_change=true"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                if "tether-gold" in data:
                    price_usd = data["tether-gold"].get("usd", 2000)
                    change = data["tether-gold"].get("usd_24h_change", 0) or 0
                    toman_price = price_usd * USD_TO_TOMAN
                    change_usd = price_usd * change / 100
                    
                    return {
                        "success": True,
                        "type": "gold",
                        "symbol": "XAU",
                        "name": "طلا (هر اونس)",
                        "price_usd": price_usd,
                        "price_toman": toman_price,
                        "change_24h": change,
                        "change_usd": change_usd,
                        "change_toman": change_usd * USD_TO_TOMAN,
                    }
    except Exception as e:
        logger.error(f"Gold fallback error: {e}")
    
    # مقدار ثابت در صورت عدم دسترسی به API
    return {
        "success": True,
        "type": "gold",
        "symbol": "XAU",
        "name": "طلا (هر اونس)",
        "price_usd": 2350,
        "price_toman": 2350 * USD_TO_TOMAN,
        "change_24h": 0,
        "change_usd": 0,
        "change_toman": 0,
        "note": "⚠️ قیمت تقریبی - API در دسترس نیست"
    }


async def search_crypto_by_name(query: str) -> dict:
    """جستجوی ارز دیجیتال با نام"""
    try:
        url = f"https://api.coingecko.com/api/v3/search?query={query}"
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.get(url)
            if response.status_code == 200:
                data = response.json()
                coins = data.get("coins", [])
                if coins:
                    return {"success": True, "id": coins[0]["id"], "name": coins[0]["name"]}
    except Exception as e:
        logger.error(f"Error searching crypto: {e}")
    return {"success": False}


def format_price_message(data: dict, original_query: str) -> tuple:
    """فرمت کردن پیام قیمت"""
    if not data.get("success"):
        return None, None
    
    price_type = data.get("type", "")
    symbol = data.get("symbol", "")
    price_usd = data.get("price_usd", 0)
    price_toman = data.get("price_toman", 0)
    change_24h = data.get("change_24h", 0)
    change_usd = data.get("change_usd", 0)
    change_toman = data.get("change_toman", 0)
    note = data.get("note", "")
    
    # انتخاب آیکون بر اساس نوع
    if price_type == "crypto":
        icon = "💰"
        tag = f"#{symbol}"
    elif price_type == "fiat":
        icon = "💰"
        tag = f"#{original_query}"
    elif price_type == "gold":
        icon = "⚜️"
        tag = "#طلا"
    else:
        icon = "💰"
        tag = f"#{symbol}"
    
    # فرمت تغییر قیمت
    if change_24h > 0:
        change_icon = "🔺"
        profit_icon = "🟢"
        change_label = "افزایش قیمت"
        profit_label = "میزان سود"
    elif change_24h < 0:
        change_icon = "🔻"
        profit_icon = "🔴"
        change_label = "کاهش قیمت"
        profit_label = "میزان ضرر"
        change_24h = abs(change_24h)
        change_usd = abs(change_usd)
        change_toman = abs(change_toman)
    else:
        change_icon = "➡️"
        profit_icon = "⚪️"
        change_label = "تغییر قیمت"
        profit_label = "میزان سود"
    
    # ساخت پیام اصلی
    message = f"{icon} 1 {tag} = {format_number(price_usd)}$\n"
    message += f"💶 {format_number(price_toman)} Toman\n\n"
    message += f"{change_icon} {change_label}: {change_24h:.2f}%\n"
    message += f"{profit_icon} {profit_label}: {format_number(change_usd)}$ [{format_number(change_toman)} Toman]\n"
    
    if note:
        message += f"\n{note}\n"
    
    # صرافی‌ها فقط برای ارزهای دیجیتال
    keyboard = None
    if price_type == "crypto":
        crypto_id = data.get("crypto_id", "default")
        exchanges = get_exchanges_for_crypto(crypto_id)
        
        message += f"\n♻️ بهترین صرافی‌ها برای معامله این ارز 📊\n"
        
        # ساخت دکمه‌های inline
        keyboard_buttons = []
        row = []
        for i, (name, url) in enumerate(exchanges[:5]):
            row.append(InlineKeyboardButton(name, url=url))
            if len(row) == 2 or i == len(exchanges[:5]) - 1:
                keyboard_buttons.append(row)
                row = []
        
        if keyboard_buttons:
            keyboard = InlineKeyboardMarkup(keyboard_buttons)
    
    return message, keyboard


async def process_query(query: str) -> tuple:
    """پردازش درخواست کاربر و دریافت قیمت"""
    query_lower = query.lower().strip()
    
    # بررسی طلا
    if query_lower in ["طلا", "gold", "xau"]:
        data = await get_gold_price()
        return data, "gold"
    
    # بررسی سکه (مقادیر تقریبی)
    if query_lower in COIN_NAMES_FA:
        # قیمت سکه بر اساس قیمت طلا
        gold_data = await get_gold_price()
        if gold_data["success"]:
            gold_price = gold_data["price_usd"]
            
            # وزن سکه‌های ایرانی
            coin_weights = {
                "coin_emami": 8.133,  # گرم
                "coin_half": 4.068,
                "coin_quarter": 2.034,
                "coin_gram": 1.0,
                "mithqal": 4.608,
            }
            
            coin_type = COIN_NAMES_FA[query_lower]
            weight = coin_weights.get(coin_type, 8.133)
            
            # قیمت طلا در هر گرم
            gold_per_gram = gold_price / 31.1035
            coin_price_usd = gold_per_gram * weight
            coin_price_toman = coin_price_usd * USD_TO_TOMAN
            
            return {
                "success": True,
                "type": "gold",
                "symbol": "سکه",
                "name": query,
                "price_usd": coin_price_usd,
                "price_toman": coin_price_toman,
                "change_24h": gold_data.get("change_24h", 0),
                "change_usd": gold_data.get("change_usd", 0) * weight / 31.1035,
                "change_toman": gold_data.get("change_toman", 0) * weight / 31.1035,
            }, "coin"
    
    # بررسی ارزهای فیات
    for fa_name, code in FIAT_NAMES_FA.items():
        if query_lower == fa_name or query_lower == code.lower():
            data = await get_fiat_price(code)
            return data, "fiat"
    
    # بررسی ارزهای دیجیتال (فارسی)
    for fa_name, crypto_id in CRYPTO_NAMES_FA.items():
        if query_lower == fa_name or query_lower == crypto_id.lower():
            data = await get_crypto_price(crypto_id)
            return data, "crypto"
    
    # جستجوی انگلیسی در CoinGecko
    if query_lower.isalpha() and len(query_lower) >= 2:
        search_result = await search_crypto_by_name(query)
        if search_result["success"]:
            data = await get_crypto_price(search_result["id"])
            return data, "crypto"
    
    return {"success": False, "error": "متأسفم، این ارز یا کالا را پیدا نکردم! 😔"}, None


# ===== هندلرهای ربات =====

async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /start"""
    user = update.effective_user
    first_name = user.first_name if user.first_name else "کاربر عزیز"
    
    welcome_message = (
        f"ربات قیمت طلا و سکه 📡:\n"
        f"سلام {first_name} جون 😎🙌🏻\n\n"
        f"من قیمت تمام چیزا رو دارم 😎💸\n"
        f"از طلا ⚜️ سکه 🥇 دلار 💰 گرفته تا بیتکوین 💎 و اتریوم ⭐️ "
        f"و حتی ناشناخته‌ترین ارزها 😎🔥\n\n"
        f"فقط کافیه اسمشو واسم بنویسی که قیمت دقیقشو بهت بگم 😃👇🏻\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔹 مثال‌ها:\n"
        f"• دلار\n"
        f"• یورو\n"
        f"• طلا\n"
        f"• سکه\n"
        f"• بیت کوین\n"
        f"• اتریوم\n"
        f"• دوج کوین\n"
        f"• سولانا\n"
        f"• و هر ارز دیجیتال دیگه‌ای...\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👨‍💻 سازنده: امیر علی فروزان اصل"
    )
    
    await update.message.reply_text(welcome_message)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستور /help"""
    help_text = (
        "📖 راهنمای استفاده از ربات:\n\n"
        "💰 ارزهای فیات:\n"
        "دلار | یورو | پوند | ین | یوان | درهم | لیر | روبل\n\n"
        "⚜️ فلزات گرانبها:\n"
        "طلا | نقره | پلاتین\n\n"
        "🥇 سکه:\n"
        "سکه | سکه امامی | نیم سکه | ربع سکه | سکه گرمی\n\n"
        "💎 ارزهای دیجیتال:\n"
        "بیت کوین | اتریوم | تتر | سولانا | ریپل\n"
        "دوج کوین | شیبا | کاردانو | پالیگان | ترون\n"
        "و هزاران ارز دیگر...\n\n"
        "👨‍💻 سازنده: امیر علی فروزان اصل\n"
        "📡 قیمت‌ها لحظه‌ای و از منابع معتبر جهانی"
    )
    await update.message.reply_text(help_text)


async def price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر اصلی برای دریافت قیمت"""
    query = update.message.text.strip()
    
    # نمایش پیام در حال پردازش
    processing_msg = await update.message.reply_text("🔄 در حال دریافت قیمت...")
    
    try:
        # دریافت داده
        data, data_type = await process_query(query)
        
        if not data.get("success"):
            error_msg = (
                f"❌ {data.get('error', 'متأسفم، خطایی رخ داده!')}\n\n"
                f"💡 لطفاً از دستور /help برای مشاهده لیست ارزهای پشتیبانی شده استفاده کنید."
            )
            await processing_msg.edit_text(error_msg)
            return
        
        # فرمت پیام
        message, keyboard = format_price_message(data, query)
        
        if message:
            if keyboard:
                await processing_msg.edit_text(
                    message,
                    reply_markup=keyboard,
                    parse_mode=None
                )
            else:
                await processing_msg.edit_text(message)
        else:
            await processing_msg.edit_text("❌ خطا در پردازش داده‌ها")
            
    except Exception as e:
        logger.error(f"Error in price_handler: {e}")
        await processing_msg.edit_text(
            "❌ متأسفانه در دریافت قیمت خطایی رخ داد!\n"
            "لطفاً چند لحظه دیگر مجدداً تلاش کنید. 🙏"
        )


async def unknown_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """هندلر دستورات ناشناخته"""
    await update.message.reply_text(
        "❓ دستور ناشناخته!\n\n"
        "برای مشاهده راهنما از /help استفاده کنید."
    )


def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    # ساخت اپلیکیشن
    application = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرها
    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("help", help_handler))
    
    # هندلر پیام‌های متنی (برای دریافت قیمت)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, price_handler)
    )
    
    # هندلر دستورات ناشناخته
    application.add_handler(
        MessageHandler(filters.COMMAND, unknown_handler)
    )
    
    # راه‌اندازی ربات
    logger.info("🚀 ربات قیمت طلا و سکه در حال اجرا...")
    logger.info("👨‍💻 سازنده: امیر علی فروزان اصل")
    
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
```
