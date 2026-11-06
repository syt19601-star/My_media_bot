import os
import asyncio
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# خادم ويب وهمي لإرضاء سيرفرات Render المجانية
flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

TOKEN = "9297995160:AAH2JrVLD2VBN-gDqnyN2KYs1wrp6uLLC_8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الميديا المطور!\n\n"
        "📥 أرسل لي أي رابط فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك) وسأقوم بتحميله بالصيغة والدقة التي تختارها مجاناً.\n\n"
        "💬 للدعم الفني أو إذا واجهتك أي مشكلة، تواصل مع المطور مباشرة هنا:\n"
        "👉 @ulx717"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith(("http://", "https://")):
        return

    # إنشاء الأزرار التفاعلية للمستخدم
    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو أعلى دقة", callback_data=f"vid_best|{url}"),
            InlineKeyboardButton("📉 فيديو دقة منخفضة", callback_data=f"vid_low|{url}")
        ],
        [
            InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data=f"aud_only|{url}")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ اختر صيغة ودقة التحميل المطلوبة المنبثقة أدناه:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data.split('|')
    choice = data[0]
    url = data[1]

    status_msg = await query.message.reply_text("⏳ جاري معالجة طلبك والتحميل من السيرفر، يرجى الانتظار...")

    # تحديد خيارات التحميل بناءً على زر المستخدم
    if choice == "vid_best":
        ydl_opts = {'format': 'best', 'outtmpl': 'video_best.%(ext)s', 'max_filesize': 50 * 1024 * 1024}
    elif choice == "vid_low":
        ydl_opts = {'format': 'worst', 'outtmpl': 'video_low.%(ext)s', 'max_filesize': 50 * 1024 * 1024}
    elif choice == "aud_only":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'audio.%(ext)s',
            'max_filesize': 50 * 1024 * 1024,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)
            if choice == "aud_only":
                filename = os.path.splitext(filename)[0] + ".mp3"

        await status_msg.edit_text("🚀 جاري رفع الملف إلى تليجرام...")
        
        with open(filename, 'rb') as file_to_send:
            if choice == "aud_only":
                await query.message.reply_audio(audio=file_to_send, caption="✨ تم تحميل الصوت بنجاح!")
            else:
                await query.message.reply_video(video=file_to_send, caption="✨ تم تحميل الفيديو بنجاح!")

        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، تعذر تحميل هذا الملف. تأكد من أن الحساب عام أو أن الحجم لا يتجاوز 50 ميجابايت.")

def main():
    server_thread = Thread(target=run_flask)
    server_thread.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("⚡ البوت المطور يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
