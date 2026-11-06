import os
import asyncio
import subprocess
import math
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

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
        "👋 أهلاً بك في بوت تحميل الميديا الخارق!\n\n"
        "📥 أرسل أي رابط فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك) وسأقوم بتحميله بالصيغة والدقة المطلوبة.\n"
        "⚡ يدعم البوت الآن تقطيع الفيديوهات الطويلة تلقائياً لإرسالها بالكامل دون قيود الـ 50 ميغابايت!\n\n"
        "💬 للدعم الفني أو الاستفسار، تواصل مع المطور:\n"
        "👉 @ulx717"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith(("http://", "https://")):
        return

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

def get_video_duration(filename):
    try:
        cmd = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nocreepy=1 "{filename}"'
        output = subprocess.check_output(cmd, shell=True).decode().strip()
        return float(output)
    except:
        return 0

def split_video(filename, duration, chunk_size=300):
    num_chunks = math.ceil(duration / chunk_size)
    chunks = []
    base, ext = os.path.splitext(filename)
    
    for i in range(num_chunks):
        start_time = i * chunk_size
        output_chunk = f"{base}_part{i+1}{ext}"
        cmd = f'ffmpeg -ss {start_time} -i "{filename}" -t {chunk_size} -c copy "{output_chunk}" -y'
        subprocess.call(cmd, shell=True)
        if os.path.exists(output_chunk):
            chunks.append(output_chunk)
            
    return chunks

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # 👍 تم التصحيح الجذري هنا لقراءة المصفوفة بشكل برمي صحيح
    data = query.data.split('|')
    choice = data[0]
    url = data[1]

    status_msg = await query.message.reply_text("⏳ جاري سحب الميديا ومعالجتها، يرجى الانتظار...")

    if choice == "vid_best":
        ydl_opts = {'format': 'best', 'outtmpl': 'downloaded_file.%(ext)s'}
    elif choice == "vid_low":
        ydl_opts = {'format': 'worst', 'outtmpl': 'downloaded_file.%(ext)s'}
    elif choice == "aud_only":
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloaded_file.%(ext)s',
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
            if choice == "aud_only" and not filename.endswith(".mp3"):
                filename = os.path.splitext(filename)[0] + ".mp3"

        filesize = os.path.getsize(filename)

        if choice != "aud_only" and filesize > 50 * 1024 * 1024:
            await status_msg.edit_text("✂️ حجم الفيديو أكبر من 50 ميغابايت، جاري تقطيعه إلى أجزاء...")
            duration = get_video_duration(filename)
            chunks = split_video(filename, duration)
            
            await status_msg.edit_text(f"🚀 جاري رفع {len(chunks)} أجزاء إلى تليجرام بالتتالي...")
            for idx, chunk in enumerate(chunks):
                with open(chunk, 'rb') as video_part:
                    await query.message.reply_video(video=video_part, caption=f"✨ الجزء ({idx+1} من {len(chunks)})")
                os.remove(chunk)
            
            os.remove(filename)
        else:
            await status_msg.edit_text("🚀 جاري رفع الملف إلى تليجرام...")
            with open(filename, 'rb') as file_to_send:
                if choice == "aud_only":
                    await query.message.reply_audio(audio=file_to_send, caption="✨ تم تحميل الصوت بنجاح!")
                else:
                    await query.message.reply_video(video=file_to_send, caption="✨ تم تحميل الفيديو بنجاح!")
            os.remove(filename)

        await status_msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، تعذر معالجة هذا الرابط. تأكد من أن الحساب عام والاتصال مستقر.")

def main():
    server_thread = Thread(target=run_flask)
    server_thread.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("⚡ البوت الخارق يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
