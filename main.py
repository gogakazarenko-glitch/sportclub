import os
import time
import telebot

# Берём токен и ID из переменных окружения
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# Приветствие
@bot.message_handler(commands=['start'])
def start(message):
    bot.reply_to(message, "Добро пожаловать в спортбот 🏀⚽🏐\n\nЗдесь вы можете посмотреть расписание и оставить заявку!")

# Расписание тренировок
@bot.message_handler(commands=['schedule'])
def schedule(message):
    bot.send_message(
        message.chat.id,
        "📅 Расписание тренировок:\n"
        "Пн — Баскетбол 🏀\n"
        "Ср — Футбол ⚽\n"
        "Пт — Волейбол 🏐"
    )

# Заявка на участие
@bot.message_handler(commands=['order'])
def order(message):
    bot.send_message(
        message.chat.id,
        "✅ Ваша заявка принята!\n(демо‑режим, данные никуда не отправляются)"
    )

# Защита от подвисаний и автоперезапуск
while True:
    try:
        bot.polling(none_stop=True, skip_pending=True, timeout=30)
    except Exception as e:
        print(f"Ошибка: {e}")
        time.sleep(10) # пауза перед перезапуском
