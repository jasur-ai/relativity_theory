import os
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from PIL import Image, ImageDraw, ImageFont

# Bot tokeni
BOT_TOKEN = "8594820977:AAHZdOUAm52HI1ZI-lUFDkxo_qSZZkYv9i8"

# SIZNING TELEGRAM ID'INGIZ
ADMIN_ID = 8004724563  # Jasur's Telegram ID

# Ma'lumotlar bazasi fayli
DATABASE_FILE = "registered_users.json"

# Conversation states
CHOOSING, ENTERING_NICKNAME, ENTERING_NAME, ENTERING_NAME_NEW, CHOOSING_TYPE, ENTERING_PARTNER_NAME, CHOOSING_PARTNER_TYPE, ENTERING_PARTNER_NICKNAME = range(8)

def load_database():
    """Ma'lumotlar bazasini yuklash"""
    if os.path.exists(DATABASE_FILE):
        with open(DATABASE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_database(db):
    """Ma'lumotlar bazasini saqlash"""
    with open(DATABASE_FILE, 'w', encoding='utf-8') as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def is_registered(user_id):
    """Foydalanuvchi ro'yxatdan o'tganmi tekshirish"""
    db = load_database()
    return str(user_id) in db

def register_user(user_id, name, nickname=None, partner_name=None, partner_nickname=None):
    """Foydalanuvchini ro'yxatga olish"""
    db = load_database()
    db[str(user_id)] = {
        'name': name,
        'nickname': nickname,
        'partner_name': partner_name,
        'partner_nickname': partner_nickname
    }
    save_database(db)
    return len(db)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start komandasi"""
    user_id = update.effective_user.id
    
    # Agar ro'yxatdan o'tgan bo'lsa
    if is_registered(user_id):
        context.user_data['is_new'] = False
        keyboard = [
            [InlineKeyboardButton("Qayta ro'yxatdan o'tish", callback_data='start_registration')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Assalomu alaykum!",
            reply_markup=reply_markup
        )
        return CHOOSING
    
    # Yangi foydalanuvchi
    context.user_data['is_new'] = True
    keyboard = [
        [InlineKeyboardButton("Ro'yxatdan o'tish", callback_data='start_registration')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Assalomu alaykum!",
        reply_markup=reply_markup
    )
    return CHOOSING

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Tugma bosilganda ishlaydi"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start_registration':
        # Ro'yxatdan o'tishni boshlash
        keyboard = [
            [InlineKeyboardButton("School21danman", callback_data='existing')],
            [InlineKeyboardButton("School21ga endi qo'shilaman", callback_data='new')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "School21 posteringizni yaratish uchun quyidagilardan birini tanlang:",
            reply_markup=reply_markup
        )
        return CHOOSING
        
    elif query.data == 'existing':
        # School21dan bo'lsa - nickname so'raydi
        context.user_data['user_type'] = 'existing'
        await query.edit_message_text("Nickname ingizni kiriting:")
        return ENTERING_NICKNAME
        
    elif query.data == 'new':
        # Yangi bo'lsa - faqat ism so'raydi
        context.user_data['user_type'] = 'new'
        await query.edit_message_text("Ismingizni kiriting:")
        return ENTERING_NAME_NEW

async def receive_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Nickname qabul qiladi"""
    context.user_data['nickname'] = update.message.text.strip()
    await update.message.reply_text("Endi ismingizni kiriting:")
    return ENTERING_NAME

async def receive_name_existing(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ism qabul qiladi (School21dan bo'lganlar uchun)"""
    name = update.message.text.strip().capitalize()
    context.user_data['name'] = name
    
    # Juftlik/Yakka tugmalar
    keyboard = [
        [InlineKeyboardButton("Juftlik", callback_data='couple')],
        [InlineKeyboardButton("Yakka", callback_data='single')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Juftlik yoki yakka?",
        reply_markup=reply_markup
    )
    return CHOOSING_TYPE

async def receive_name_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ism qabul qiladi (Yangi qo'shilganlar uchun)"""
    name = update.message.text.strip().capitalize()
    context.user_data['name'] = name
    
    # Juftlik/Yakka tugmalar
    keyboard = [
        [InlineKeyboardButton("Juftlik", callback_data='couple')],
        [InlineKeyboardButton("Yakka", callback_data='single')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Juftlik yoki yakka?",
        reply_markup=reply_markup
    )
    return CHOOSING_TYPE

async def type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Juftlik/Yakka tanlash"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'single':
        # Yakka bo'lsa - poster yaratish
        context.user_data['type'] = 'single'
        await create_and_send_poster(query, context)
        return ConversationHandler.END
        
    elif query.data == 'couple':
        # Juftlik bo'lsa - sherik School21danmi deb so'rash
        context.user_data['type'] = 'couple'
        keyboard = [
            [InlineKeyboardButton("School21dan", callback_data='partner_existing')],
            [InlineKeyboardButton("School21dan tashqaridan", callback_data='partner_new')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            "Sherigingiz School21danmi yoki tashqaridanmi?",
            reply_markup=reply_markup
        )
        return CHOOSING_PARTNER_TYPE

async def partner_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sherik School21danmi yoki yo'qmi"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'partner_existing':
        # Sherik School21dan bo'lsa - avval ismini so'raymiz
        context.user_data['partner_type'] = 'existing'
        await query.edit_message_text("Sherigingizning ismini kiriting:")
        return ENTERING_PARTNER_NAME
        
    elif query.data == 'partner_new':
        # Sherik School21dan emas - faqat ismini so'raymiz
        context.user_data['partner_type'] = 'new'
        await query.edit_message_text("Sherigingizning ismini kiriting:")
        return ENTERING_PARTNER_NAME

async def receive_partner_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sherik ismini qabul qilish"""
    partner_name = update.message.text.strip().capitalize()
    context.user_data['partner_name'] = partner_name
    
    # Agar sherik School21dan bo'lsa, nickname so'raymiz
    if context.user_data.get('partner_type') == 'existing':
        await update.message.reply_text("Sherigingizning nickname ini kiriting:")
        return ENTERING_PARTNER_NICKNAME
    else:
        # Sherik School21dan emas bo'lsa, poster yaratamiz
        await create_and_send_poster(update, context, is_message=True)
        return ConversationHandler.END

async def receive_partner_nickname(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Sherik nickname ini qabul qilish"""
    partner_nickname = update.message.text.strip()
    context.user_data['partner_nickname'] = partner_nickname
    
    # Poster yaratish
    await create_and_send_poster(update, context, is_message=True)
    return ConversationHandler.END

async def create_and_send_poster(update_or_query, context: ContextTypes.DEFAULT_TYPE, is_message=False):
    """Poster yaratish va yuborish"""
    user_data = context.user_data
    name = user_data.get('name', '')
    nickname = user_data.get('nickname', '')
    user_type = user_data.get('user_type', 'new')
    type_choice = user_data.get('type', 'single')
    partner_name = user_data.get('partner_name', '')
    partner_nickname = user_data.get('partner_nickname', '')
    partner_type = user_data.get('partner_type', 'new')
    
    # Poster uchun matn yaratish
    if type_choice == 'couple':
        # O'zining ma'lumotlari
        if user_type == 'existing':
            user_text = f"{name} ({nickname})"
        else:
            user_text = name
        
        # Sherik ma'lumotlari
        if partner_type == 'existing':
            partner_text = f"{partner_name} ({partner_nickname})"
        else:
            partner_text = partner_name
        
        text = f"{user_text} & {partner_text}"
    else:
        # Yakka
        if user_type == 'existing':
            text = f"{name} ({nickname})"
        else:
            text = name
    
    # Foydalanuvchini ro'yxatga olish
    if is_message:
        user_id = update_or_query.effective_user.id
        username = update_or_query.effective_user.username or "Username yo'q"
        chat = update_or_query.message  # .message qo'shamiz
    else:
        user_id = update_or_query.from_user.id
        username = update_or_query.from_user.username or "Username yo'q"
        chat = update_or_query.message
    
    is_new_user = context.user_data.get('is_new', True)
    total_users = register_user(user_id, name, nickname, partner_name, partner_nickname)
    
    # Poster yaratish
    poster_path = create_poster(text, user_id)
    
    # Posterni yuborish
    await chat.reply_photo(
        photo=open(poster_path, 'rb'),
        caption=f"Ro'yxatdan muvaffaqiyatli o'tdingiz! ✅"
    )
    
    # Adminga xabar yuborish
    try:
        if is_new_user:
            admin_message = f"🆕 Yangi ro'yxatdan o'tish!\n\n"
        else:
            admin_message = f"🔄 Qayta ro'yxatdan o'tish!\n\n"
        
        admin_message += f"🆔 ID: {user_id}\n"
        admin_message += f"📝 Username: @{username}\n"
        admin_message += f"👤 Ism: {name}"
        if nickname:
            admin_message += f" ({nickname})"
        if partner_name:
            admin_message += f"\n💑 Sherik: {partner_name}"
            if partner_nickname:
                admin_message += f" ({partner_nickname})"
        admin_message += f"\n\n📊 Jami ro'yxatdan o'tganlar: {total_users}"
        
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_message
        )
    except Exception as e:
        print(f"Adminga xabar yuborishda xatolik: {e}")
    
    # Faylni o'chirish
    os.remove(poster_path)

def create_poster(text, user_id):
    """Poster yaratish funksiyasi"""
    template_path = "template.png"
    
    if os.path.exists(template_path):
        image = Image.open(template_path)
        width, height = image.size
        draw = ImageDraw.Draw(image)
        print(f"✅ Template rasm topildi: {width}x{height}")
    else:
        print("⚠️ OGOHLANTIRISH: template.png topilmadi! Oddiy dizayn yaratilmoqda...")
        width, height = 800, 600
        image = Image.new('RGB', (width, height), color='#1a1a2e')
        draw = ImageDraw.Draw(image)
        
        # Gradient effekt
        for i in range(height):
            color_value = int(26 + (46 - 26) * (i / height))
            draw.rectangle([(0, i), (width, i + 1)], fill=(color_value, color_value, 46))
    
    # Fontni yuklash
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 50)
    except:
        try:
            font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 50)
        except:
            font = ImageFont.load_default()
    
    # Matnni markazga joylash
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = height - 150
    
    # Matn uchun orqa fon
    padding = 20
    draw.rectangle(
        [(x - padding, y - padding), (x + text_width + padding, y + text_height + padding)],
        fill=(0, 0, 0)
    )
    
    # Matnni yozish
    draw.text((x, y), text, fill='white', font=font)
    
    # Faylni saqlash
    filename = f"poster_{user_id}.png"
    image.save(filename)
    return filename

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bekor qilish"""
    await update.message.reply_text("Bekor qilindi. /start dan qayta boshlashingiz mumkin.")
    return ConversationHandler.END

def main():
    """Bot ishga tushirish"""
    application = Application.builder().token(BOT_TOKEN).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            CHOOSING: [CallbackQueryHandler(button_callback)],
            ENTERING_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_nickname)],
            ENTERING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name_existing)],
            ENTERING_NAME_NEW: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name_new)],
            CHOOSING_TYPE: [CallbackQueryHandler(type_callback)],
            CHOOSING_PARTNER_TYPE: [CallbackQueryHandler(partner_type_callback)],
            ENTERING_PARTNER_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_partner_name)],
            ENTERING_PARTNER_NICKNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_partner_nickname)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )
    
    application.add_handler(conv_handler)
    
    print("Bot ishga tushdi...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()