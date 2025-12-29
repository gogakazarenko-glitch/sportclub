import os
import threading
import time
import qrcode
from io import BytesIO
from telebot import TeleBot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

# Берём токен и ID из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = TeleBot(BOT_TOKEN, parse_mode="HTML")

subscribers = set()
records = {}
progress = {}

def get_main_keyboard():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("💰 Цена абонемента", "📅 Расписание тренировок")
    markup.add("🗓 Записаться на тренировку", "🏋️ Мой прогресс")
    markup.add("🖼 Галерея зала", "⭐ Отзывы")
    markup.add("🔥 Акции", "❓ Помощь")
    return markup

@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    subscribers.add(chat_id)
    bot.send_message(chat_id,
        "Привет в нашем спортклубе! 🏋️‍♂️\n"
        "Здесь цены, расписание, запись, прогресс, галерея и напоминания.\n"
        "Жми кнопки ниже 👇",
        reply_markup=get_main_keyboard())

@bot.message_handler(func=lambda m: m.text == "💰 Цена абонемента")
def price(message):
    subscribers.add(message.chat.id)
    bot.reply_to(message, "Абонемент — 2000 ₽ в месяц (безлимит)")

@bot.message_handler(func=lambda m: m.text == "📅 Расписание тренировок")
def schedule(message):
    subscribers.add(message.chat.id)
    bot.reply_to(message, "Тренировки: понедельник, четверг, суббота — в 19:00")

@bot.message_handler(func=lambda m: m.text == "🖼 Галерея зала")
def gallery(message):
    media = [
        InputMediaPhoto("https://i.imgur.com/example1.jpg", caption="Тренажёрный зал"),
        InputMediaPhoto("https://i.imgur.com/example2.jpg", caption="Зал для йоги")
    ]
    bot.send_media_group(message.chat.id, media)

@bot.message_handler(func=lambda m: m.text == "⭐ Отзывы")
def reviews(message):
    bot.reply_to(message, "Отзывы:\n• «Лучший зал!» — Иван\n• «Прогресс за месяц!» — Маша")

@bot.message_handler(func=lambda m: m.text == "🔥 Акции")
def promotions(message):
    bot.reply_to(message, "Акция: первый месяц — скидка 50%!")

@bot.message_handler(func=lambda m: m.text == "❓ Помощь")
def help_cmd(message):
    bot.reply_to(message, "Жми кнопки ниже 👇\nВопросы — пиши владельцу клуба")

@bot.message_handler(func=lambda m: m.text == "🗓 Записаться на тренировку")
def booking_sport(message):
    subscribers.add(message.chat.id)
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🏋️ Тренажёрка", callback_data="sport_тренажерка"))
    markup.add(InlineKeyboardButton("🧘 Йога", callback_data="sport_йога"))
    markup.add(InlineKeyboardButton("🥊 Бокс", callback_data="sport_бокс"))
    bot.send_message(message.chat.id, "Выбери вид спорта:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("sport_"))
def booking_day(call):
    sport = call.data.split("_")[1]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Понедельник", callback_data=f"day_{sport}_понедельник"))
    markup.add(InlineKeyboardButton("Четверг", callback_data=f"day_{sport}_четверг"))
    markup.add(InlineKeyboardButton("Суббота", callback_data=f"day_{sport}_суббота"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Вид спорта: {sport.capitalize()}\nВыбери день:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("day_"))
def booking_time(call):
    parts = call.data.split("_")
    sport = parts[1]
    day = parts[2]
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("17:00", callback_data=f"time_{sport}_{day}_17:00"))
    markup.add(InlineKeyboardButton("18:00", callback_data=f"time_{sport}_{day}_18:00"))
    markup.add(InlineKeyboardButton("19:00", callback_data=f"time_{sport}_{day}_19:00"))
    markup.add(InlineKeyboardButton("20:00", callback_data=f"time_{sport}_{day}_20:00"))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"{sport.capitalize()} — {day.capitalize()}\nВыбери время:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("time_"))
def booking_confirm(call):
    parts = call.data.split("_")
    sport = parts[1]
    day = parts[2]
    time_slot = parts[3]
    user_name = call.from_user.first_name or "Клиент"
    chat_id = call.message.chat.id

    records.setdefault(chat_id, []).append(f"{sport} {day} {time_slot}")

    qr_text = f"Вход: {user_name} | {sport} | {day} {time_slot}"
    bio = BytesIO()
    qr = qrcode.make(qr_text)
    qr.save(bio, 'PNG')
    bio.seek(0)

    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id,
                          text=f"Записал на {sport} {day} в {time_slot} ✅")
    bot.send_photo(chat_id, bio, caption=f"Твой QR-код:\n{qr_text}")

    bot.send_message(ADMIN_ID, f"Новая запись!\nОт: {user_name}\n{sport} {day} {time_slot}")

@bot.message_handler(func=lambda m: m.text == "🏋️ Мой прогресс")
def my_progress(message):
    chat_id = message.chat.id
    progress.setdefault(chat_id, {"weight": [], "photos": []})
    bot.send_message(chat_id, "Введи текущий вес (кг):")
    bot.register_next_step_handler(message, save_weight)

def save_weight(message):
    chat_id = message.chat.id
    try:
        weight = float(message.text.replace(",", "."))
        progress[chat_id]["weight"].append(weight)
        bot.reply_to(message, f"Вес {weight} кг сохранён!\nТвои веса: {progress[chat_id]['weight']}\nОтправь фото прогресса или напиши 'пропустить'")
        bot.register_next_step_handler(message, save_photo)
    except:
        bot.reply_to(message, "Не понял число. Попробуй снова (например 85.5)")
        bot.register_next_step_handler(message, save_weight)

def save_photo(message):
    chat_id = message.chat.id
    if message.text and "пропустить" in message.text.lower():
        bot.reply_to(message, "Ок!")
        return
    if message.photo:
        progress[chat_id]["photos"].append(message.photo[-1].file_id)
        bot.reply_to(message, "Фото сохранено! 🔥")
    else:
        bot.reply_to(message, "Это не фото. Отправь фото или 'пропустить'")
        bot.register_next_step_handler(message, save_photo)

@bot.message_handler(func=lambda m: True)
def fallback(message):
    subscribers.add(message.chat.id)
    bot.send_message(message.chat.id, "Выбери кнопку 👇", reply_markup=get_main_keyboard())

# Напоминания
def reminder_loop():
    while True:
        current_time = time.strftime("%H:%M")
        if current_time == "17:00":
            for chat_id in subscribers:
                try:
                    bot.send_message(chat_id, "Через 2 часа тренировка! Не прогуливай 💪")
                except:
                    pass
            time.sleep(70)
        time.sleep(60)

threading.Thread(target=reminder_loop, daemon=True).start()

print("Спорт-клуб бот запущен!")

bot.infinity_polling()

