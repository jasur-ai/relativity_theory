"""
Bu bot sizning Telegram ID'ingizni topish uchun.
Faqat bir marta ishlatiladi.
"""
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

BOT_TOKEN = "8594820977:AAHZdOUAm52HI1ZI-lUFDkxo_qSZZkYv9i8"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or "Username yo'q"
    first_name = update.effective_user.first_name or ""
    
    message = f"""
📱 Sizning Telegram ma'lumotlaringiz:

🆔 ID: {user_id}
👤 Ism: {first_name}
📝 Username: @{username}

Bu ID'ni school21_bot.py faylida ADMIN_ID = {user_id} qilib qo'ying!
"""
    
    await update.message.reply_text(message)

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler('start', start))
    
    print("Bot ishga tushdi. /start ni yuboring.")
    application.run_polling()

if __name__ == '__main__':
    main()