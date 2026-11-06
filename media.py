import os
import asyncio
import subprocess
import math
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

TOKEN = "9297995160:AAH2JrVLD2VBN-gDqnyN2KYs1wrp6uLLC_8"

# قاموس لحفظ روابط المستخدمين مؤقتاً بالذاكرة
user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الميديا المستقر والمطور!\n\n"
        "📥 أرسل أي رابط فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك) وسأقوم بخدمتك فوراً.\n"
        "⚡ يدعم البوت تقطيع الفيديوهات الطويلة تلقائياً لتخطي قيود الحجم!\n\n"
        "💬 للدعم الفني أو الاستفسار، تواصل مع المطور:\n"
        "👉 @ulx717"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.message.from_user.id

    # أولاً: إذا أرسل المستخدم رابطاً جديداً
    if text.startswith(("http://", "https://")):
        user_urls[user_id] = text
        await update.message.reply_text(
            "⚙️ تم استلام الرابط بنجاح! من فضلك أرسل الآن أحد الكلمات التالية لتحديد الصيغة:\n\n"
            "◀️ اكتب كلمة ( **فيديو** ) لتحميل الفيديو بالكامل.\n"
            "◀️ اكتب كلمة ( **صوت** ) لتحميل الصوت فقط بصيغة MP3."
        )
        return

    # ثانياً: إذا أرسل المستخدم خيار التحميل (فيديو أو صوت)
    if user_id in user_urls:
        url = user_urls[user_id]
        choice = text

        if choice not in ["فيديو", "صوت"]:
            await update.message.reply_text("⚠️ خيار غير صحيح! من فضلك اكتب كلمة (فيديو) أو (صوت) فقط.")
            return

        status_msg = await update.message.reply_text("⏳ جاري سحب الميديا ومعالجتها من السحاب، يرجى الانتظار...")
        import yt_dlp

        if choice == "فيديو":
            ydl_opts = {'format': 'best', 'outtmpl': f'video_{user_id}.%(ext)s'}
        elif choice == "صوت":
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'audio_{user_id}.%(ext)s',
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
                if choice == "صوت" and not filename.endswith(".mp3"):
                    filename = os.path.splitext(filename)[0] + ".mp3"

            filesize = os.path.getsize(filename)

            # ميزة التقطيع التلقائي للفيديوهات الكبيرة
            if choice == "فيديو" and filesize > 50 * 1024 * 1024:
                await status_msg.edit_text("✂️ حجم الفيديو أكبر من 50 ميغابايت، جاري تقطيعه تلقائياً...")
                
                # جلب مدة الفيديو عبر ffprobe
                cmd_dur = f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nocreepy=1 "{filename}"'
                duration = float(subprocess.check_output(cmd_dur, shell=True).decode().strip())
                
                chunk_size = 300
                num_chunks = math.ceil(duration / chunk_size)
                base, ext = os.path.splitext(filename)
                
                await status_msg.edit_text(f"🚀 جاري رفع {num_chunks} أجزاء إلى تليجرام بالتتالي...")
                
                for i in range(num_chunks):
                    start_time = i * chunk_size
                    chunk_file = f"{base}_part{i+1}{ext}"
                    cmd_split = f'ffmpeg -ss {start_time} -i "{filename}" -t {chunk_size} -c copy "{chunk_file}" -y'
                    subprocess.call(cmd_split, shell=True)
                    
                    if os.path.exists(chunk_file):
                        with open(chunk_file, 'rb') as vf:
                            await update.message.reply_video(video=vf, caption=f"✨ الجزء ({i+1} من {num_chunks})")
                        os.remove(chunk_file)
                
                os.remove(filename)
            else:
                await status_msg.edit_text("🚀 جاري رفع الملف إلى تليجرام...")
                with open(filename, 'rb') as file_to_send:
                    if choice == "صوت":
                        await update.message.reply_audio(audio=file_to_send, caption="✨ تم تحميل الصوت بنجاح!")
                    else:
                        await update.message.reply_video(video=file_to_send, caption="✨ تم تحميل الفيديو بنجاح!")
                os.remove(filename)

            del user_urls[user_id]
            await status_msg.delete()

        except Exception as e:
            print(f"Error: {e}")
            await status_msg.edit_text("❌ عذراً، تعذر معالجة هذا الرابط. تأكد من أن الحساب عام والاتصال مستقر.")
            if user_id in user_urls:
                del user_urls[user_id]
    else:
        await update.message.reply_text("ℹ️ من فضلك أرسل رابط فيديو أولاً لكي أقوم بتحميله لك.")

def main():
    server_thread = Thread(target=run_flask)
    server_thread.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("⚡ البوت المستقر يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
