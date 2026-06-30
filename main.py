```python
import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from datetime import datetime

# ==================== Configuration ====================
TOKEN = os.getenv("BOT_TOKEN")

# ==================== Logging Setup ====================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== Gold Price API ====================
# Using a free gold price API (no authentication required)
GOLD_API_URL = "https://api.metalpriceapi.com/v1/latest"
GOLD_PRICE_FREE_API = "https://www.goldapi.io/api/XAU/USD"

# Alternative free API endpoints
FRANKFURTER_API = "https://api.frankfurter.app/latest"
METALS_API = "https://metals-api.com/api/latest"

async def fetch_gold_price() -> dict:
    """
    Fetch real-time gold prices from free APIs.
    Returns a dict with price information.
    """
    results = {}
    
    # Try multiple free APIs
    try:
        # Method 1: Using exchangerate-api for USD rate + gold calculation
        async with aiohttp.ClientSession() as session:
            # Get gold price in USD per troy ounce from a free source
            # Using metals live data from a public endpoint
            url = "https://data-asg.goldprice.org/GetData/USD-XAU/1"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        # Price per troy ounce in USD
                        price_per_oz = float(data[0].split(',')[0])
                        # 1 troy ounce = 31.1035 grams
                        price_per_gram = price_per_oz / 31.1035
                        results['usd_per_oz'] = price_per_oz
                        results['usd_per_gram'] = price_per_gram
                        results['source'] = 'GoldPrice.org'
                        results['success'] = True
    except Exception as e:
        logger.warning(f"First API attempt failed: {e}")

    if not results.get('success'):
        try:
            async with aiohttp.ClientSession() as session:
                # Alternative: Try another free endpoint
                url = "https://openexchangerates.org/api/latest.json?app_id=free_tier&base=USD"
                # Using a simpler approach with static fallback
                url2 = "https://api.coingecko.com/api/v3/simple/price?ids=tether-gold&vs_currencies=usd"
                async with session.get(url2, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'tether-gold' in data:
                            price = data['tether-gold']['usd']
                            results['usd_per_oz'] = price
                            results['usd_per_gram'] = price / 31.1035
                            results['source'] = 'CoinGecko (XAUT)'
                            results['success'] = True
        except Exception as e:
            logger.warning(f"Second API attempt failed: {e}")

    if not results.get('success'):
        try:
            async with aiohttp.ClientSession() as session:
                # Try metals API
                url = "https://economia.awesomeapi.com.br/json/last/XAU-USD"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'XAUUSD' in data:
                            price = float(data['XAUUSD']['bid'])
                            results['usd_per_oz'] = price
                            results['usd_per_gram'] = price / 31.1035
                            results['source'] = 'AwesomeAPI'
                            results['success'] = True
        except Exception as e:
            logger.warning(f"Third API attempt failed: {e}")

    return results


async def fetch_usd_to_irr() -> dict:
    """
    Fetch USD to IRR (Iranian Rial) exchange rate.
    """
    result = {}
    try:
        async with aiohttp.ClientSession() as session:
            # Try bonbast or navasan for IRR rates
            url = "https://api.navasan.tech/latest/?api=free_PLACEHOLDER&item=usd_buy"
            # Use a free rate tracker
            url2 = "https://bours.netlify.app/api/currency"
            
            # Fallback to approximate rate (update this regularly)
            # As of 2024, 1 USD ≈ 50,000-55,000 IRR (official) or 580,000+ (free market)
            result['usd_to_irr_free_market'] = 580000  # Approximate free market rate
            result['usd_to_irr_official'] = 42000       # Official rate
            result['source'] = 'Approximate (update required)'
            result['success'] = True
            
            try:
                headers = {'User-Agent': 'Mozilla/5.0'}
                async with session.get(
                    "https://bours.netlify.app/api/currency",
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=5)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'usd' in data:
                            result['usd_to_irr_free_market'] = int(data['usd']) * 10  # Toman to Rial
                            result['source'] = 'Bours API'
            except:
                pass
                
    except Exception as e:
        logger.warning(f"IRR fetch failed: {e}")
        result['usd_to_irr_free_market'] = 580000
        result['usd_to_irr_official'] = 42000
        result['success'] = True
    
    return result


async def get_comprehensive_gold_data() -> dict:
    """
    Get comprehensive gold and exchange rate data.
    """
    gold_data = await fetch_gold_price()
    irr_data = await fetch_usd_to_irr()
    
    combined = {
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'gold': gold_data,
        'currency': irr_data
    }
    
    # Calculate IRR prices if we have gold data
    if gold_data.get('success') and irr_data.get('success'):
        usd_per_oz = gold_data.get('usd_per_oz', 0)
        usd_per_gram = gold_data.get('usd_per_gram', 0)
        irr_rate = irr_data.get('usd_to_irr_free_market', 580000)
        
        combined['irr_per_oz'] = usd_per_oz * irr_rate
        combined['irr_per_gram'] = usd_per_gram * irr_rate
        combined['toman_per_oz'] = (usd_per_oz * irr_rate) / 10
        combined['toman_per_gram'] = (usd_per_gram * irr_rate) / 10
        
        # 18k gold (most common in Iran) = 75% pure
        combined['toman_per_gram_18k'] = combined['toman_per_gram'] * 0.75
        # 24k gold
        combined['toman_per_gram_24k'] = combined['toman_per_gram']
        
        # Mithqal (مثقال) = 4.608 grams
        combined['toman_per_mithqal'] = combined['toman_per_gram'] * 4.608
        
    return combined


def format_number(number: float) -> str:
    """Format large numbers with commas."""
    return f"{int(number):,}"


def create_gold_message(data: dict) -> str:
    """
    Create a formatted message with gold price information.
    """
    timestamp = data.get('timestamp', 'N/A')
    gold = data.get('gold', {})
    currency = data.get('currency', {})
    
    if not gold.get('success'):
        return "❌ خطا در دریافت قیمت طلا. لطفاً دوباره تلاش کنید."
    
    usd_per_oz = gold.get('usd_per_oz', 0)
    usd_per_gram = gold.get('usd_per_gram', 0)
    
    msg = f"""
🏅 *قیمت لحظه‌ای طلا*
━━━━━━━━━━━━━━━━━━━━
⏰ *زمان بروزرسانی:* `{timestamp}`

💰 *قیمت جهانی (دلار آمریکا):*
• هر اونس: `${format_number(usd_per_oz)}`
• هر گرم: `${usd_per_gram:.2f}`

💱 *نرخ دلار آزاد:* `{format_number(currency.get('usd_to_irr_free_market', 0))} ریال`
"""

    if 'toman_per_gram' in data:
        msg += f"""
🇮🇷 *قیمت در ایران (تومان):*
• هر گرم طلای ۲۴ عیار: `{format_number(data.get('toman_per_gram_24k', 0))} تومان`
• هر گرم طلای ۱۸ عیار: `{format_number(data.get('toman_per_gram_18k', 0))} تومان`
• هر مثقال طلا: `{format_number(data.get('toman_per_mithqal', 0))} تومان`
• هر اونس: `{format_number(data.get('toman_per_oz', 0))} تومان`
"""

    msg += f"""
━━━━━━━━━━━━━━━━━━━━
📊 *منبع داده:* {gold.get('source', 'N/A')}
⚠️ _قیمت‌ها جنبه اطلاعاتی دارند_
"""
    return msg


def create_currency_keyboard():
    """Create inline keyboard for currency options."""
    keyboard = [
        [
            InlineKeyboardButton("🔄 بروزرسانی", callback_data="refresh_gold"),
            InlineKeyboardButton("📊 تاریخچه", callback_data="gold_history"),
        ],
        [
            InlineKeyboardButton("💰 قیمت دلار", callback_data="usd_price"),
            InlineKeyboardButton("💎 سکه طلا", callback_data="coin_price"),
        ],
        [
            InlineKeyboardButton("📈 نمودار قیمت", callback_data="gold_chart"),
            InlineKeyboardButton("ℹ️ راهنما", callback_data="help_info"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)


# ==================== Command Handlers ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /start command."""
    user = update.effective_user
    welcome_msg = f"""
🌟 *سلام {user.first_name} عزیز!*

به ربات قیمت طلا خوش آمدید! 🏅

این ربات قیمت‌های لحظه‌ای طلا را از منابع معتبر جهانی دریافت و برای شما نمایش می‌دهد.

📌 *امکانات ربات:*
• قیمت لحظه‌ای طلا در بازار جهانی
• نرخ تبدیل به ریال و تومان
• قیمت طلای ۱۸ و ۲۴ عیار
• قیمت مثقال طلا
• نرخ ارز (دلار آزاد)

🔧 *دستورات:*
/gold - قیمت فعلی طلا
/usd - نرخ دلار
/coin - قیمت سکه طلا
/help - راهنمای کامل
/refresh - بروزرسانی قیمت‌ها

⬇️ برای شروع روی دکمه زیر کلیک کنید:
"""
    keyboard = [
        [InlineKeyboardButton("🏅 مشاهده قیمت طلا", callback_data="refresh_gold")],
        [
            InlineKeyboardButton("💱 نرخ ارز", callback_data="usd_price"),
            InlineKeyboardButton("🪙 قیمت سکه", callback_data="coin_price"),
        ],
        [InlineKeyboardButton("ℹ️ راهنما", callback_data="help_info")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_msg,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )


async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /gold command - show current gold prices."""
    # Send loading message
    loading_msg = await update.message.reply_text(
        "⏳ در حال دریافت قیمت‌های لحظه‌ای طلا...",
        parse_mode='Markdown'
    )
    
    try:
        data = await get_comprehensive_gold_data()
        message = create_gold_message(data)
        keyboard = create_currency_keyboard()
        
        await loading_msg.edit_text(
            message,
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error in gold_command: {e}")
        await loading_msg.edit_text(
            "❌ خطا در دریافت اطلاعات. لطفاً دوباره تلاش کنید.\n\n/gold",
            parse_mode='Markdown'
        )


async def usd_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /usd command - show USD exchange rates."""
    loading_msg = await update.message.reply_text("⏳ در حال دریافت نرخ ارز...")
    
    try:
        irr_data = await fetch_usd_to_irr()
        
        free_market = irr_data.get('usd_to_irr_free_market', 0)
        official = irr_data.get('usd_to_irr_official', 0)
        
        msg = f"""
💵 *نرخ دلار آمریکا*
━━━━━━━━━━━━━━━━━━━━
⏰ *زمان:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

💱 *نرخ آزاد:* `{format_number(free_market)} ریال`
           `{format_number(free_market // 10)} تومان`

🏦 *نرخ رسمی:* `{format_number(official)} ریال`
           `{format_number(official // 10)} تومان`

━━━━━━━━━━━━━━━━━━━━
⚠️ _نرخ‌ها تقریبی هستند_
"""
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="usd_price")],
            [InlineKeyboardButton("🏅 قیمت طلا", callback_data="refresh_gold")],
        ]
        await loading_msg.edit_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in usd_command: {e}")
        await loading_msg.edit_text("❌ خطا در دریافت نرخ ارز.")


async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /coin command - show gold coin prices."""
    loading_msg = await update.message.reply_text("⏳ در حال محاسبه قیمت سکه...")
    
    try:
        data = await get_comprehensive_gold_data()
        
        if not data.get('gold', {}).get('success'):
            await loading_msg.edit_text("❌ خطا در دریافت اطلاعات.")
            return
        
        # Iranian gold coin weights
        # Emami coin = 8.136 grams of 900 fineness gold
        # Half coin = 4.068 grams
        # Quarter coin = 2.034 grams
        # Gerami coin = 1 gram (approximate)
        
        toman_per_gram_24k = data.get('toman_per_gram_24k', 0)
        toman_per_gram_900 = toman_per_gram_24k * 0.9  # 900 fineness
        
        emami_gold_value = toman_per_gram_900 * 8.136
        half_gold_value = toman_per_gram_900 * 4.068
        quarter_gold_value = toman_per_gram_900 * 2.034
        gerami_gold_value = toman_per_gram_900 * 1.0
        
        # Add manufacturing premium (حق ضرب) - approximately 3-8%
        premium = 1.05  # 5% premium
        
        msg = f"""
🪙 *قیمت سکه طلا (محاسباتی)*
━━━━━━━━━━━━━━━━━━━━
⏰ *زمان:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

🥇 *سکه امامی (تمام سکه):*
   ارزش طلای خالص: `{format_number(emami_gold_value)} تومان`
   با احتساب حق ضرب: `{format_number(emami_gold_value * premium)} تومان`

🥈 *نیم سکه:*
   ارزش طلای خالص: `{format_number(half_gold_value)} تومان`
   با احتساب حق ضرب: `{format_number(half_gold_value * premium)} تومان`

🥉 *ربع سکه:*
   ارزش طلای خالص: `{format_number(quarter_gold_value)} تومان`
   با احتساب حق ضرب: `{format_number(quarter_gold_value * premium)} تومان`

💫 *سکه گرمی:*
   ارزش طلای خالص: `{format_number(gerami_gold_value)} تومان`

━━━━━━━━━━━━━━━━━━━━
📝 _سکه امامی: ۸.۱۳۶ گرم طلای ۹۰۰_
⚠️ _قیمت‌ها محاسباتی و تقریبی هستند_
"""
        keyboard = [
            [InlineKeyboardButton("🔄 بروزرسانی", callback_data="coin_price")],
            [
                InlineKeyboardButton("🏅 قیمت طلا", callback_data="refresh_gold"),
                InlineKeyboardButton("💵 نرخ دلار", callback_data="usd_price"),
            ],
        ]
        
        await loading_msg.edit_text(
            msg,
            parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    except Exception as e:
        logger.error(f"Error in coin_command: {e}")
        await loading_msg.edit_text("❌ خطا در محاسبه قیمت سکه.")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /help command."""
    help_msg = """
ℹ️ *راهنمای ربات قیمت طلا*
━━━━━━━━━━━━━━━━━━━━

📌 *دستورات اصلی:*

/start - شروع و صفحه اصلی
/gold - قیمت لحظه‌ای طلا
/usd - نرخ دلار آمریکا
/coin - قیمت انواع سکه طلا
/refresh - بروزرسانی همه قیمت‌ها
/help - این راهنما

━━━━━━━━━━━━━━━━━━━━

📊 *اطلاعات نمایش داده شده:*

🏅 *طلا:*
• قیمت جهانی به دلار (هر اونس و هر گرم)
• قیمت طلای ۲۴ عیار به تومان
• قیمت طلای ۱۸ عیار به تومان
• قیمت مثقال طلا

💵 *ارز:*
• نرخ دلار آزاد
• نرخ دلار رسمی

🪙 *سکه:*
• قیمت سکه امامی
• قیمت نیم سکه
• قیمت ربع سکه
• قیمت سکه گرمی

━━━━━━━━━━━━━━━━━━━━

⚠️ *توجه:*
قیمت‌های نمایش داده شده از منابع اینترنتی دریافت می‌شوند و جنبه اطلاعاتی دارند. برای معاملات مهم به صرافی‌های معتبر مراجعه کنید.
"""
    keyboard = [
        [InlineKeyboardButton("🏅 قیمت طلا", callback_data="refresh_gold")],
        [
            InlineKeyboardButton("💵 نرخ دلار", callback_data="usd_price"),
            InlineKeyboardButton("🪙 سکه طلا", callback_data="coin_price"),
        ],
    ]
    
    await update.message.reply_text(
        help_msg,
        parse_mode='Markdown',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def refresh_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler for /refresh command."""
    await gold_command(update, context)


# ==================== Callback Query Handler ====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle inline keyboard button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    try:
        if data == "refresh_gold":
            # Show loading
            await query.edit_message_text(
                "⏳ در حال دریافت قیمت‌های لحظه‌ای طلا...",
                parse_mode='Markdown'
            )
            
            gold_data = await get_comprehensive_gold_data()
            message = create_gold_message(gold_data)
            keyboard = create_currency_keyboard()
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=keyboard
            )
            
        elif data == "usd_price":
            await query.edit_message_text("⏳ در حال دریافت نرخ ارز...")
            
            irr_data = await fetch_usd_to_irr()
            free_market = irr_data.get('usd_to_irr_free_market', 0)
            official = irr_data.get('usd_to_irr_official', 0)
            
            msg = f"""
💵 *نرخ دلار آمریکا*
━━━━━━━━━━━━━━━━━━━━
⏰ *زمان:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

💱 *نرخ آزاد:* `{format_number(free_market)} ریال`
           `{format_number(free_market // 10)} تومان`

🏦 *نرخ رسمی:* `{format_number(official)} ریال`
           `{format_number(official // 10)} تومان`

━━━━━━━━━━━━━━━━━━━━
⚠️ _نرخ‌ها تقریبی هستند_
"""
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="usd_price")],
                [
                    InlineKeyboardButton("🏅 قیمت طلا", callback_data="refresh_gold"),
                    InlineKeyboardButton("🪙 سکه طلا", callback_data="coin_price"),
                ],
            ]
            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif data == "coin_price":
            await query.edit_message_text("⏳ در حال محاسبه قیمت سکه...")
            
            gold_data = await get_comprehensive_gold_data()
            
            if not gold_data.get('gold', {}).get('success'):
                await query.edit_message_text("❌ خطا در دریافت اطلاعات.")
                return
            
            toman_per_gram_24k = gold_data.get('toman_per_gram_24k', 0)
            toman_per_gram_900 = toman_per_gram_24k * 0.9
            
            emami = toman_per_gram_900 * 8.136 * 1.05
            half = toman_per_gram_900 * 4.068 * 1.05
            quarter = toman_per_gram_900 * 2.034 * 1.05
            gerami = toman_per_gram_900 * 1.0
            
            msg = f"""
🪙 *قیمت سکه طلا (محاسباتی)*
━━━━━━━━━━━━━━━━━━━━
⏰ *زمان:* `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

🥇 *سکه امامی:* `{format_number(emami)} تومان`
🥈 *نیم سکه:* `{format_number(half)} تومان`
🥉 *ربع سکه:* `{format_number(quarter)} تومان`
💫 *سکه گرمی:* `{format_number(gerami)} تومان`

━━━━━━━━━━━━━━━━━━━━
⚠️ _قیمت‌ها محاسباتی و تقریبی هستند_
"""
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="coin_price")],
                [
                    InlineKeyboardButton("🏅 قیمت طلا", callback_data="refresh_gold"),
                    InlineKeyboardButton("💵 نرخ دلار", callback_data="usd_price"),
                ],
            ]
            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
        elif data == "gold_history":
            msg = """
📊 *تاریخچه قیمت طلا*
━━━━━━━━━━━━━━━━━━━━

برای مشاهده نمودارها و تاریخچه قیمت طلا به سایت‌های زیر مراجعه کنید:

🌐 *منابع معتبر:*
• [GoldPrice.org](https://goldprice.org)
• [Kitco.com](https://kitco.com)
• [BullionVault](https://www.bullionvault.com)
• [TradingEconomics](https://tradingeconomics.com/commodity/gold)

━━━━━━━━━━━━━━━━━━━━
"""
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_gold")],
            ]
            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            
        elif data == "gold_chart":
            msg = """
📈 *نمودار قیمت طلا*
━━━━━━━━━━━━━━━━━━━━

برای مشاهده نمودار زنده قیمت طلا:

📊 *نمودار ۲۴ ساعته:* [مشاهده](https://goldprice.org/gold-price-charts/24-hour-gold-price-chart)

📊 *نمودار هفتگی:* [مشاهده](https://goldprice.org/gold-price-charts/7-day-gold-price-chart)

📊 *نمودار ماهانه:* [مشاهده](https://goldprice.org/gold-price-charts/30-day-gold-price-chart)

━━━━━━━━━━━━━━━━━━━━
"""
            keyboard = [
                [InlineKeyboardButton("🔙 بازگشت", callback_data="refresh_gold")],
            ]
            await query.edit_message_text(
                msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard),
                disable_web_page_preview=True
            )
            
        elif data == "help_info":
            help_msg = """
ℹ️ *راهنمای ربات قیمت طلا*
━━━━━━━━━━━━━━━━━━━━

📌 *دستورات:*
/gold - قیمت طلا
/usd - نرخ دلار
/coin - قیمت سکه
/help - راهنما

━━━━━━━━━━━━━━━━━━━━

📊 *واحدهای اندازه‌گیری:*
• اونس تروی = ۳۱.۱ گرم
• مثقال = ۴.۶۰۸ گرم
• ۱ تومان = ۱۰ ریال

⚠️ _قیمت‌ها اطلاعاتی هستند_
"""
            keyboard = [
                [InlineKeyboardButton("🏅 قیمت طلا", callback_data="refresh_gold")],
                [
                    InlineKeyboardButton("💵 نرخ دلار", callback_data="usd_price"),
                    InlineKeyboardButton("🪙 سکه طلا", callback_data="coin_price"),
                ],
            ]
            await query.edit_message_text(
                help_msg,
                parse_mode='Markdown',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            
    except Exception as e:
        logger.error(f"Error in button_callback: {e}")
        try:
            await query.edit_message_text(
                "❌ خطایی رخ داد. لطفاً دوباره تلاش کنید.\n\n/start",
                parse_mode='Markdown'
            )
        except:
            pass


# ==================== Error Handler ====================

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle errors occurring in the dispatcher."""
    logger.error(f"Exception while handling an update: {context.error}")
    
    if isinstance(update, Update) and update.effective_message:
        await update.effective_message.reply_text(
            "❌ متأسفانه خطایی رخ داد. لطفاً دوباره تلاش کنید.\n\n"
            "در صورت تکرار مشکل با پشتیبانی تماس بگیرید."
        )


# ==================== Main Function ====================

def main() -> None:
    """Set up and run the bot."""
    logger.info("Starting Gold Price Bot...")
    
    # Create the Application instance
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("gold", gold_command))
    application.add_handler(CommandHandler("usd", usd_command))
    application.add_handler(CommandHandler("coin", coin_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("refresh", refresh_command))
    
    # Register callback query handler for inline buttons
    application.add_handler(CallbackQueryHandler(button_callback))
    
    # Register error handler
    application.add_error_handler(error_handler)
    
    logger.info("Bot is running. Press Ctrl+C to stop.")
    
    # Run the bot using polling
    application.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
```
