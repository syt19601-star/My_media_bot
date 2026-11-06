import os
import asyncio
import aiohttp
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
    status_msg = await query.message.reply_text("⏳ جاري استخراج الميديا عبر السيرفر السحابي المطور...")

    # 🚀 الـ API المباشر والقوي المفتوح للسيرفرات بدون حظر
    api_url = f"https://allinonerepo.com{url}"

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # البحث عن رابط التحميل المباشر داخل استجابة الـ API
                    download_url = None
                    if "links" in result and len(result["links"]) > 0:
                        for link in result["links"]:
                            if choice == "audio" and (link.get("type") == "audio" or "mp3" in link.get("quality", "")):
                                download_url = link["url"]
                                break
                            elif choice == "video" and link.get("type") == "video":
                                download_url = link["url"]
                                break
                        
                        if not download_url:
                            download_url = result["links"][0]["url"]

                    if download_url:
                        await status_msg.edit_text("🚀 جاري سحب الملف ورفعه إلى تليجرام...")
                        
                        async with session.get(download_url) as file_resp:
                            if file_resp.status == 200:
                                file_data = await file_resp.read()
                                filename = f"download_{user_id}.mp3" if choice == "audio" else f"download_{user_id}.mp4"
                                
                                with open(filename, "wb") as f:
                                    f.write(file_data)
                                    
                                with open(filename, "rb") as file_to_send:
                                    if choice == "audio":
                                        await query.message.reply_audio(audio=file_to_send, caption="✨ تم تحميل الصوت بنجاح! \n🤖 v1.0")
                                    else:
                                        await query.message.reply_video(video=file_to_send, caption="✨ تم تحميل الفيديو بنجاح! \n🤖 v1.0")
                                
                                os.remove(filename)
                                await status_msg.delete()
                                del user_urls[user_id]
                                return
                                
                    raise Exception("No downloadable link found")
                else:
                    raise Exception("API Connection Error")

    except Exception as e:
        print(f"Error: {e}")
        await status_msg.edit_text("❌ عذراً، تعذر سحب الفيديو. تأكد من أن الفيديو عام وغير محذوف وحاول مجدداً.")
        if user_id in user_urls:
            del user_urls[user_id]

def main():
    server_thread = Thread(target=run_flask)
    server_thread.start()

    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_click))
    
    print("⚡ البوت يعمل بنظام الـ API المستقر...")
    app.run_polling()

if __name__ == '__main__':
    main()
