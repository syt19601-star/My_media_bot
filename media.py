import os
import asyncio
import subprocess
import math
from threading import Thread
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes

flask_app = Flask('')

@flask_app.route('/')
def home():
    return "Bot is alive!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    flask_app.run(host='0.0.0.0', port=port)

TOKEN = "9297995160:AAH2JrVLD2VBN-gDqnyN2KYs1wrp6uLLC_8"

# قاموس لحفظ الروابط مؤقتاً لتجنب كسر قيود حجم أزرار تليجرام
user_urls = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك في بوت تحميل الميديا الخارق والمقاوم للحظر!\n\n"
        "📥 أرسل أي رابط فيديو من (تيك توك، إنستغرام، يوتيوب، فيسبوك) وسأقوم بخدمتك فوراً بالأزرار الذكية.\n"
        "⚡ يدعم البوت تقطيع الفيديوهات الطويلة تلقائياً لتخطي قيود الحجم!\n\n"
        "💬 للدعم الفني أو الاستفسار، تواصل مع المطور:\n"
        "👉 @ulx717\n\n"
        "🤖 الإصدار: v1.0"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        return

    user_id = update.message.from_user.id
    user_urls[user_id] = url # حفظ الرابط بالذاكرة مؤقتاً

    # تصميم الأزرار التفاعلية دون وضع الرابط داخل الـ callback لعدم كسر القيد
    keyboard = [
        [
            InlineKeyboardButton("🎬 فيديو أعلى دقة", callback_data="vid_best"),
            InlineKeyboardButton("📉 فيديو دقة منخفضة", callback_data="vid_low")
        ],
        [
            InlineKeyboardButton("🎵 صوت فقط (MP3)", callback_data="aud_only")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("⚙️ اختر صيغة ودقة التحميل المطلوبة المنبثقة أدناه:", reply_markup=reply_markup)

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    choice = query.data

    if user_id not in user_urls:
        await query.message.reply_text("⚠️ انتهت صلاحية الطلب، يرجى إرسال رابط الفيديو مجدداً.")
        return

    url = user_urls[user_id]
    status_msg = await query.message.reply_text("⏳ جاري اختراق الحماية وسحب الميديا من السحاب، يرجى الانتظار...")
    import yt_dlp

    # إعدادات متطورة لتخطي حظر السيرفرات السحابية في Render وتغيير هوية المتصفح
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'referer': 'https://google.com',
        'nocheckcertificate': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }

    if choice == "vid_best":
        ydl_opts = {**common_opts, 'format': 'best', 'outtmpl': f'video_{user_id}.%(ext)s'}
    elif choice == "vid_low":
        ydl_opts = {**common_opts, 'format': 'worst', 'outtmpl': f'video_{user_id}.%(ext)s'}
    elif choice == "aud_only":
        ydl_opts = {
            **common_opts,
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
            if choice == "aud_only" and not filename.endswith(".mp3"):
                filename = os.path.splitext(filename)[0] + ".mp3"

        filesize = os.path.getsize(filename)

        # التحقق من حجم الفيديو وبدء ميزة التقطيع التلقائي الذكية
        if choice != "aud_only" and filesize > 50 * 1024 * 1024:
            await status_msg.edit_text("✂️ حجم الفيديو أكبر من 50 ميغابايت، جاري تقطيعه تلقائياً...")
            
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
                        await query.message.reply_video(video=vf, caption=f"✨ الجزء ({i+1} من {num_chunks})")
                    os.remove(chunk_file)
            
            os.remove(filename)
        else:
            await status_msg.edit_text("🚀 جاري رفع الملف إلى تليجرام...")
            with open(filename, 'rb') as file_to_send:
                if choice == "aud_only":
                    await query.message.reply_audio(audio=file_to_send, caption="✨ تم تحميل الصوت بنجاح!")
                else:
                    await query.message.reply_video(video=file_to_send, caption="✨ تم تحميل الفيديو بنجاح!")
            os.remove(filename)

        del user_urls[user_id]
        await status_msg.delete()

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، واجه السيرفر حظراً مؤقتاً أو تلفاً بالرابط. يرجى تجربة رابط آخر أو المحاولة لاحقاً.")
        if user_id in user_urls:
            del user_urls[user_id]

def main():
    server_thread = Thread(target=run_flask)
    server_thread.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("⚡ البوت الخارق v1.0 يعمل الآن بنجاح...")
    app.run_polling()

if __name__ == '__main__':
    main()
