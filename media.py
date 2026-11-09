import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# خادم ويب وهمي لإرضاء سيرفرات Render المجانية وتخطي مشكلة الـ Ports
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

TOKEN = "9297995160:AAH2JrVLD2VBN-gDqnyN2KYs1wrp6uLLC_8"

# قاموس لحفظ الروابط مؤقتاً بالذاكرة
user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الميديا السحابي v2.1!\n\n"
        "📥 أرسل أي رابط فيديو من:\n"
        "• 🎥 **يوتيوب والفيديوهات القصيرة Shorts**\n"
        "• 🎵 **تيك توك** (بدون حقوق)\n"
        "• 📸 **إنستغرام وفيس بوك**\n\n"
        "وسأقوم بتحميله فوراً بالأزرار الذكية مجاناً 🚀\n\n"
        "💬 للدعم الفني أو الاستفسار، تواصل مع المطور:\n"
        "👉 @ulx717\n\n"
        "🤖 الإصدار الحالي: v2.1 المحدث والمتطور"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith(("http://", "https://")):
        return

    user_id = update.message.from_user.id
    user_urls[user_id] = url

    # إظهار الأزرار الذكية للمستخدم
    keyboard = [
        [
            InlineKeyboardButton("🎬 تحميل الفيديو", callback_data="video"),
            InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data="audio")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ تم استلام الرابط بنجاح! اختر صيغة التحميل المطلوبة أدناه:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data

    if user_id not in user_urls:
        await query.message.reply_text("⚠️ انتهت صلاحية الطلب، يرجى إرسال رابط الفيديو مجدداً.")
        return

    url = user_urls[user_id]
    status_msg = await query.message.reply_text("⏳ جاري معالجة الرابط وسحب الميديا من السحاب، يرجى الانتظار...")

    # الخيارات المحدثة لتجاوز حظر يوتيوب والـ Shorts وتيك توك
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://www.youtube.com',
        'nocheckcertificate': True,
        'geo_bypass': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
        'socket_timeout': 30,
    }

    if choice == "video":
        ydl_opts = {
            **common_opts, 
            'format': 'best[ext=mp4]/best', 
            'outtmpl': f'download_{user_id}.%(ext)s'
        }
    else:
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
            'outtmpl': f'download_{user_id}.%(ext)s',
            'postprocessors':
