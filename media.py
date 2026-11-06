import os
import asyncio
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

TOKEN = "9297995160:AAH2JrVLD2VBN-gDqnyN2KYs1wrp6uLLC_8"
user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الميديا الخارق v1.0!\n\n"
        "📥 أرسل أي رابط فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك) وسأقوم بتحميله فوراً بالأزرار الذكية مجاناً.\n\n"
        "💬 للدعم الفني أو الاستفسار، تواصل مع المطور:\n"
        "👉 @ulx717\n\n"
        "🤖 الإصدار: v1.0"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        return

    user_id = update.message.from_user.id
    user_urls[user_id] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 تحميل الفيديو", callback_data="video"),
            InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data="audio")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ اختر صيغة التحميل المطلوبة أدناه:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data

    if user_id not in user_urls:
        await query.message.reply_text("⚠️ انتهت صلاحية الطلب، يرجى إرسال رابط الفيديو مجدداً.")
        return

    url = user_urls[user_id]
    status_msg = await query.message.reply_text("⏳ جاري معالجة الرابط وتحميل الميديا من السحاب، يرجى الانتظار...")

    # إعدادات ذكية لتغيير هوية المتصفح وتخطي الحظر الجغرافي بالسحاب
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'referer': 'https://google.com',
        'nocheckcertificate': True
    }

    if choice == "video":
        ydl_opts = {**common_opts, 'format': 'best', 'outtmpl': f'download_{user_id}.%(ext)s'}
    else:
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
            'outtmpl': f'download_{user_id}.%(ext)s',
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
            if choice == "audio" and not filename.endswith(".mp3"):
                filename = os.path.splitext(filename)[0] + ".mp3"

        await status_msg.edit_text("🚀 جاري رفع الملف إلى تليجرام...")
        with open(filename, "rb") as file_to_send:
            if choice == "audio":
                await query.message.reply_audio(audio=file_to_send, caption="✨ تم تحميل الصوت بنجاح! \n🤖 v1.0")
            else:
                await query.message.reply_video(video=file_to_send, caption="✨ تم تحميل الفيديو بنجاح! \n🤖 v1.0")
        
        if os.path.exists(filename):
            os.remove(filename)
        await status_msg.delete()
        del user_urls[user_id]

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، تعذر سحب الفيديو. تأكد من أن الرابط صحيح والحساب عام وحاول مجدداً.")
        if user_id in user_urls:
            del user_urls[user_id]

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("⚡ البوت السحابي المستقر يعمل بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
