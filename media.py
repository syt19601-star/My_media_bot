import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# التوكن الخاص بك جاهز ومضاف هنا تلقائياً
TOKEN = "9297995160:AAH2JrVLD2VBN-gDqnyN2KYs1wrp6uLLC_8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الميديا المطور!\n\n"
        "📥 أرسل لي أي رابط فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك) وسأقوم بتحميله وإرساله لك فوراً مجاناً."
    )

async def download_and_send(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith(("http://", "https://")):
        return

    status_msg = await update.message.reply_text("⏳ جاري معالجة الرابط وتحميل الفيديو، يرجى الانتظار...")

    # إعدادات مكتبة التحميل
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloaded_video.%(ext)s',
        'max_filesize': 50 * 1024 * 1024, # الحد الأقصى 50 ميجابايت لتليجرام
        'quiet': True,
        'no_warnings': True
    }

    try:
        loop = asyncio.get_event_loop()
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = await loop.run_in_executor(None, lambda: ydl.extract_info(url, download=True))
            filename = ydl.prepare_filename(info)

        await status_msg.edit_text("🚀 جاري رفع الفيديو إلى تليجرام...")
        with open(filename, 'rb') as video:
            await update.message.reply_video(video=video, caption="✨ تم التحميل بنجاح بواسطة بوتك!")
        
        os.remove(filename)
        await status_msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، تعذر تحميل هذا الفيديو. تأكد من أن الحساب عام وليس خاصاً، أو أن حجم الفيديو لا يتجاوز 50 ميجابايت.")
        if os.path.exists('downloaded_video.mp4'):
            os.remove('downloaded_video.mp4')

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_and_send))
    
    print("⚡ البوت يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
  
