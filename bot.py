#!/usr/bin/env python3
"""
ربات قیمت طلا و ارز
سازنده: امیر علی فروزان اصل
"""

import logging
import asyncio
import aiohttp
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# ==================== تنظیمات اصلی ====================
import os

BOT_TOKEN = os.getenv("BOT_TOKEN")

# تنظیم لاگ
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== توابع دریافت قیمت ====================

async def get_gold_prices():
    """دریافت قیمت طلا، سکه و ارز از API واقعی"""
    try:
        # استفاده از API تبدیل برای دریافت قیمت‌های واقعی
        async with aiohttp.ClientSession() as session:
            # دریافت قیمت طلا از API
            url = "https://brsapi.ir/FreeTsetmcBrsApi/Api_Free_Gold_Currency_v2.json"
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return None
    except Exception as e:
        logger.error(f"خطا در دریافت قیمت: {e}")
        return None

async def get_prices_navasan():
    """دریافت قیمت از API navasan"""
    try:
        async with aiohttp.ClientSession() as session:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            url = "https://api.navasan.tech/latest/?api_key=free&item=usd,eur,gbp,aed,gold18,gold24,sekke_emami,sekke_bahar,nim_sekke,rob_sekke,ons_tala"
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                else:
                    return None
    except Exception as e:
        logger.error(f"خطا در دریافت از navasan: {e}")
        return None

def format_price(price):
    """فرمت‌بندی قیمت با جداکننده هزارگان"""
    try:
        if isinstance(price, str):
            price = float(price.replace(',', ''))
        return f"{int(price):,}"
    except:
        return str(price)

# ==================== هندلرها ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /start - پیام خوشامدگویی"""
    user = update.effective_user
    first_name = user.first_name if user.first_name else "کاربر عزیز"
    
    welcome_message = f"""
🌟 *سلام {first_name} عزیز!* 🌟

خوش آمدید به *ربات قیمت طلا و ارز*

━━━━━━━━━━━━━━━━━━━━
💎 این ربات به شما امکان می‌دهد:
• 📊 قیمت لحظه‌ای طلا
• 💰 قیمت سکه
• 💵 نرخ ارزها
• 🏆 قیمت انواع طلا

را به صورت *لحظه‌ای* مشاهده کنید!
━━━━━━━━━━━━━━━━━━━━

👨‍💻 *سازنده:* امیر علی فروزان اصل

از دکمه‌های زیر استفاده کنید 👇
    """
    
    keyboard = [
        [
            InlineKeyboardButton("🥇 قیمت طلا", callback_data="gold"),
            InlineKeyboardButton("🪙 قیمت سکه", callback_data="coin")
        ],
        [
            InlineKeyboardButton("💵 قیمت ارز", callback_data="currency"),
            InlineKeyboardButton("📊 همه قیمت‌ها", callback_data="all")
        ],
        [
            InlineKeyboardButton("🔄 بروزرسانی قیمت‌ها", callback_data="refresh")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        welcome_message,
        parse_mode='Markdown',
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دستور /help"""
    help_text = """
📖 *راهنمای ربات*

━━━━━━━━━━━━━━━━━━━━
🔧 *دستورات موجود:*

/start - شروع ربات و پیام خوشامدگویی
/gold - قیمت طلا
/coin - قیمت سکه  
/currency - قیمت ارز
/all - تمام قیمت‌ها
/help - راهنما

━━━━━━━━━━━━━━━━━━━━
👨‍💻 *سازنده:* امیر علی فروزان اصل
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def gold_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /gold - قیمت طلا"""
    await send_gold_prices(update, context, from_callback=False)

async def coin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /coin - قیمت سکه"""
    await send_coin_prices(update, context, from_callback=False)

async def currency_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /currency - قیمت ارز"""
    await send_currency_prices(update, context, from_callback=False)

async def all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دستور /all - تمام قیمت‌ها"""
    await send_all_prices(update, context, from_callback=False)

async def send_gold_prices(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=True):
    """ارسال قیمت طلا"""
    
    if from_callback:
        await update.callback_query.edit_message_text("⏳ در حال دریافت قیمت‌های طلا...")
    else:
        msg = await update.message.reply_text("⏳ در حال دریافت قیمت‌های طلا...")
    
    data = await get_prices_navasan()
    
    if data:
        try:
            gold18 = data.get('gold18', {})
            gold24 = data.get('gold24', {})
            ons = data.get('ons_tala', {})
            
            gold_text = f"""
🥇 *قیمت طلا - لحظه‌ای*
━━━━━━━━━━━━━━━━━━━━

💛 *طلای ۱۸ عیار (گرمی):*
└ {format_price(gold18.get('value', 'N/A'))} تومان

💎 *طلای ۲۴ عیار (گرمی):*
└ {format_price(gold24.get('value', 'N/A'))} تومان

⭐ *انس جهانی طلا:*
└ {format_price(ons.get('value', 'N/A'))} تومان

━━━━━━━━━━━━━━━━━━━━
⏰ آخرین بروزرسانی: همین لحظه
👨‍💻 سازنده: امیر علی فروزان اصل
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="gold"),
                 InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if from_callback:
                await update.callback_query.edit_message_text(
                    gold_text, parse_mode='Markdown', reply_markup=reply_markup
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=gold_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except Exception as e:
            error_msg = f"❌ خطا در پردازش داده‌ها: {e}"
            if from_callback:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=error_msg
                )
    else:
        error_msg = "❌ خطا در دریافت قیمت‌ها. لطفاً دوباره تلاش کنید."
        if from_callback:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=msg.message_id,
                text=error_msg
            )

async def send_coin_prices(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=True):
    """ارسال قیمت سکه"""
    
    if from_callback:
        await update.callback_query.edit_message_text("⏳ در حال دریافت قیمت‌های سکه...")
    else:
        msg = await update.message.reply_text("⏳ در حال دریافت قیمت‌های سکه...")
    
    data = await get_prices_navasan()
    
    if data:
        try:
            emami = data.get('sekke_emami', {})
            bahar = data.get('sekke_bahar', {})
            nim = data.get('nim_sekke', {})
            rob = data.get('rob_sekke', {})
            
            coin_text = f"""
🪙 *قیمت سکه - لحظه‌ای*
━━━━━━━━━━━━━━━━━━━━

👑 *سکه امامی:*
└ {format_price(emami.get('value', 'N/A'))} تومان

🌸 *سکه بهار آزادی:*
└ {format_price(bahar.get('value', 'N/A'))} تومان

🔸 *نیم سکه:*
└ {format_price(nim.get('value', 'N/A'))} تومان

🔹 *ربع سکه:*
└ {format_price(rob.get('value', 'N/A'))} تومان

━━━━━━━━━━━━━━━━━━━━
⏰ آخرین بروزرسانی: همین لحظه
👨‍💻 سازنده: امیر علی فروزان اصل
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="coin"),
                 InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if from_callback:
                await update.callback_query.edit_message_text(
                    coin_text, parse_mode='Markdown', reply_markup=reply_markup
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=coin_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except Exception as e:
            error_msg = f"❌ خطا در پردازش داده‌ها: {e}"
            if from_callback:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=error_msg
                )
    else:
        error_msg = "❌ خطا در دریافت قیمت‌ها. لطفاً دوباره تلاش کنید."
        if from_callback:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=msg.message_id,
                text=error_msg
            )

async def send_currency_prices(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=True):
    """ارسال قیمت ارز"""
    
    if from_callback:
        await update.callback_query.edit_message_text("⏳ در حال دریافت نرخ ارزها...")
    else:
        msg = await update.message.reply_text("⏳ در حال دریافت نرخ ارزها...")
    
    data = await get_prices_navasan()
    
    if data:
        try:
            usd = data.get('usd', {})
            eur = data.get('eur', {})
            gbp = data.get('gbp', {})
            aed = data.get('aed', {})
            
            currency_text = f"""
💵 *نرخ ارز - لحظه‌ای*
━━━━━━━━━━━━━━━━━━━━

🇺🇸 *دلار آمریکا:*
└ {format_price(usd.get('value', 'N/A'))} تومان

🇪🇺 *یورو:*
└ {format_price(eur.get('value', 'N/A'))} تومان

🇬🇧 *پوند انگلیس:*
└ {format_price(gbp.get('value', 'N/A'))} تومان

🇦🇪 *درهم امارات:*
└ {format_price(aed.get('value', 'N/A'))} تومان

━━━━━━━━━━━━━━━━━━━━
⏰ آخرین بروزرسانی: همین لحظه
👨‍💻 سازنده: امیر علی فروزان اصل
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="currency"),
                 InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if from_callback:
                await update.callback_query.edit_message_text(
                    currency_text, parse_mode='Markdown', reply_markup=reply_markup
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=currency_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except Exception as e:
            error_msg = f"❌ خطا در پردازش داده‌ها: {e}"
            if from_callback:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=error_msg
                )
    else:
        error_msg = "❌ خطا در دریافت قیمت‌ها. لطفاً دوباره تلاش کنید."
        if from_callback:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=msg.message_id,
                text=error_msg
            )

async def send_all_prices(update: Update, context: ContextTypes.DEFAULT_TYPE, from_callback=True):
    """ارسال تمام قیمت‌ها"""
    
    if from_callback:
        await update.callback_query.edit_message_text("⏳ در حال دریافت تمام قیمت‌ها...")
    else:
        msg = await update.message.reply_text("⏳ در حال دریافت تمام قیمت‌ها...")
    
    data = await get_prices_navasan()
    
    if data:
        try:
            usd = data.get('usd', {})
            eur = data.get('eur', {})
            gbp = data.get('gbp', {})
            aed = data.get('aed', {})
            gold18 = data.get('gold18', {})
            gold24 = data.get('gold24', {})
            ons = data.get('ons_tala', {})
            emami = data.get('sekke_emami', {})
            bahar = data.get('sekke_bahar', {})
            nim = data.get('nim_sekke', {})
            rob = data.get('rob_sekke', {})
            
            all_text = f"""
📊 *تمام قیمت‌ها - لحظه‌ای*
━━━━━━━━━━━━━━━━━━━━

🥇 *طلا:*
├ طلای ۱۸ عیار: {format_price(gold18.get('value', 'N/A'))} تومان
├ طلای ۲۴ عیار: {format_price(gold24.get('value', 'N/A'))} تومان
└ انس جهانی: {format_price(ons.get('value', 'N/A'))} تومان

🪙 *سکه:*
├ سکه امامی: {format_price(emami.get('value', 'N/A'))} تومان
├ سکه بهار آزادی: {format_price(bahar.get('value', 'N/A'))} تومان
├ نیم سکه: {format_price(nim.get('value', 'N/A'))} تومان
└ ربع سکه: {format_price(rob.get('value', 'N/A'))} تومان

💵 *ارز:*
├ 🇺🇸 دلار: {format_price(usd.get('value', 'N/A'))} تومان
├ 🇪🇺 یورو: {format_price(eur.get('value', 'N/A'))} تومان
├ 🇬🇧 پوند: {format_price(gbp.get('value', 'N/A'))} تومان
└ 🇦🇪 درهم: {format_price(aed.get('value', 'N/A'))} تومان

━━━━━━━━━━━━━━━━━━━━
⏰ آخرین بروزرسانی: همین لحظه
👨‍💻 سازنده: امیر علی فروزان اصل
            """
            
            keyboard = [
                [InlineKeyboardButton("🔄 بروزرسانی", callback_data="all"),
                 InlineKeyboardButton("🏠 منوی اصلی", callback_data="main_menu")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            if from_callback:
                await update.callback_query.edit_message_text(
                    all_text, parse_mode='Markdown', reply_markup=reply_markup
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=all_text,
                    parse_mode='Markdown',
                    reply_markup=reply_markup
                )
        except Exception as e:
            error_msg = f"❌ خطا در پردازش داده‌ها: {e}"
            if from_callback:
                await update.callback_query.edit_message_text(error_msg)
            else:
                await context.bot.edit_message_text(
                    chat_id=update.message.chat_id,
                    message_id=msg.message_id,
                    text=error_msg
                )
    else:
        error_msg = "❌ خطا در دریافت قیمت‌ها. لطفاً دوباره تلاش کنید."
        if from_callback:
            await update.callback_query.edit_message_text(error_msg)
        else:
            await context.bot.edit_message_text(
                chat_id=update.message.chat_id,
                message_id=msg.message_id,
                text=error_msg
            )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر دکمه‌های inline"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "gold":
        await send_gold_prices(update, context, from_callback=True)
    
    elif query.data == "coin":
        await send_coin_prices(update, context, from_callback=True)
    
    elif query.data == "currency":
        await send_currency_prices(update, context, from_callback=True)
    
    elif query.data == "all":
        await send_all_prices(update, context, from_callback=True)
    
    elif query.data == "refresh":
        await send_all_prices(update, context, from_callback=True)
    
    elif query.data == "main_menu":
        user = query.from_user
        first_name = user.first_name if user.first_name else "کاربر عزیز"
        
        welcome_message = f"""
🌟 *سلام {first_name} عزیز!* 🌟

به *ربات قیمت طلا و ارز* خوش آمدید!

━━━━━━━━━━━━━━━━━━━━
💎 امکانات ربات:
• 📊 قیمت لحظه‌ای طلا
• 💰 قیمت سکه
• 💵 نرخ ارزها
• 🏆 قیمت انواع طلا
━━━━━━━━━━━━━━━━━━━━

👨‍💻 *سازنده:* امیر علی فروزان اصل

یکی از گزینه‌ها را انتخاب کنید 👇
        """
        
        keyboard = [
            [
                InlineKeyboardButton("🥇 قیمت طلا", callback_data="gold"),
                InlineKeyboardButton("🪙 قیمت سکه", callback_data="coin")
            ],
            [
                InlineKeyboardButton("💵 قیمت ارز", callback_data="currency"),
                InlineKeyboardButton("📊 همه قیمت‌ها", callback_data="all")
            ],
            [
                InlineKeyboardButton("🔄 بروزرسانی قیمت‌ها", callback_data="refresh")
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await query.edit_message_text(
            welcome_message,
            parse_mode='Markdown',
            reply_markup=reply_markup
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """هندلر خطاها"""
    logger.error(f"خطا: {context.error}")

# ==================== تابع اصلی ====================

def main():
    """تابع اصلی برای راه‌اندازی ربات"""
    # ساخت اپلیکیشن
    app = Application.builder().token(BOT_TOKEN).build()
    
    # اضافه کردن هندلرهای دستور
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("gold", gold_command))
    app.add_handler(CommandHandler("coin", coin_command))
    app.add_handler(CommandHandler("currency", currency_command))
    app.add_handler(CommandHandler("all", all_command))
    
    # اضافه کردن هندلر دکمه‌ها
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # اضافه کردن هندلر خطا
    app.add_error_handler(error_handler)
    
    print("=" * 50)
    print("🤖 ربات قیمت طلا و ارز")
    print("👨‍💻 سازنده: امیر علی فروزان اصل")
    print("=" * 50)
    print("✅ ربات در حال اجرا است...")
    
    # شروع polling
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
