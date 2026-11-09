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
        "👋 أهلاً بك في بوت تحميل الميديا الذكي | الإصدار v1.0 🚀\n"
        "يسعدني مساعدتك في حفظ مقاطعك المفضلة بسرعة وبأعلى جودة ممكنة!\n"
        "📥 كل ما عليك فعله هو إرسال رابط الفيديو من:\n"
        "• 🎬 تيك توك (TikTok)\n"
        "• 📸 إنستغرام (Instagram)\n"
        "• 👥 فيسبوك (Facebook)\n"
        "✨ مميزات البوت:\n"
        "• ⚡ تحميل فوري ومباشر بمجرد إرسال الرابط.\n"
        "• ⚙️ خيارات متعددة للتحميل (فيديو أو صوت فقط MP3).\n"
        "• 💎 الخدمة مجانية بالكامل وبدون إعلانات مزعجة.\n"
        "💬 للدعم الفني أو الإستفسار، تواصل مع المطور:\n"
        "👨‍💻 @ulx717"
    )

async def handle_message(update
