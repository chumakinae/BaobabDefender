# -*- coding: utf-8 -*-
import re
import sqlite3
import uuid
import datetime
import pytz
import telebot
from geopy.geocoders import Nominatim
from telebot import types
from tzwhere import tzwhere
import time
import schedule

bot = telebot.TeleBot('7090977563:AAGi-MjX7V8o378Sed1s7wfaUOK0UCP0td4')

conn = sqlite3.connect('data.db')
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    user_id INTEGER,
                    user_name TEXT,
                    tz_info TEXT,
                    time_rec TEXT,
                    gr_rec TEXT,
                    gender TEXT,
                    timezone INTEGER,
                    status,
                    age
                )""")


@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("👋 Запустить")
    markup.add(btn1)
    bot.send_message(message.from_user.id, "Добрый день. Данный бот поможет вам за N дней усилить защиту ваших аккаунтов, данных, а также обучит основам обеспечения цифровой гигиены. Вам достаточно ежедневно выполнять по одной рекомендации. С наилучшими пожеланиями, Киберпротект", reply_markup=markup)


@bot.message_handler(content_types=['text'])
def get_text_messages(message):
    if message.text == '👋 Запустить':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True) #создание новых кнопок
        btn2 = types.KeyboardButton('Давайте поскорее начнём!')
        markup.add(btn2)
        bot.send_message(message.from_user.id, "Вы сделали уверенный шаг на пути обеспечения безопасности ваших данных. Пожалуйста, ответьте на несколько вопросов, и мы начнем.", reply_markup=markup) #ответ бота
        bot.register_next_step_handler(message, first_question)


def first_question(message):
    bot.send_message(message.from_user.id, "Как к вам обращаться?", reply_markup = telebot.types.ReplyKeyboardRemove()) # удаление кнопки
    bot.register_next_step_handler(message, second_question)


def second_question(message):

    global user_id
    global user_name
    global tz_info
    user_id = message.from_user.id
    user_name = message.text
    pattern = r'^[A-Za-zА-Яа-яЁё]+$'
    if re.match(pattern, user_name):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn21 = types.KeyboardButton('Ежедневно')
        btn22 = types.KeyboardButton('Рабочие дни')
        btn23 = types.KeyboardButton('Выходные дни')
        markup.add(btn21, btn22, btn23)
        bot.send_message(message.from_user.id, "Сформируйте удобный для вас график получения рекомендаций и уведомлений.",reply_markup=markup)
        bot.register_next_step_handler(message, pre_get_timezone)
    else:
        bot.send_message(message.from_user.id, "😭 Не похоже на [имя/фамилию]. Попробуйте еще раз.")
        bot.register_next_step_handler(message, second_question)


def pre_get_timezone(message): # определяем часовой пояс, <---неизвестна работоспособность данного участка кода =\
    global gr_rec
    gr_rec = message.text  # формируем график =)
    if message.text == 'Ежедневно' or message.text == 'Рабочие дни' or message.text == 'Выходные дни':
        bot.send_message(message.from_user.id, "Укажите город, в котором вы находитесь",  reply_markup = telebot.types.ReplyKeyboardRemove())
        bot.register_next_step_handler(message, get_timezone)


def get_timezone(message, markup=None):
    global tz_info
    global tz_offset
    global timedelta
    global time_difference
    city = message.text
    geo = Nominatim(user_agent="SuperMon_Bot")
    try:
        location = geo.geocode(city)
    except Exception as e:
        bot.send_message(message, f"Произошла ошибка при попытке найти город: {str(e)}")
        return
    if location is None:
        bot.send_message(message,"Не удалось найти такой город. Попробуйте написать его название латиницей или указать более крупный город поблизости.")
    else:
        tzw = tzwhere.tzwhere()
        try:
            timezone_str = tzw.tzNameAt(location.latitude, location.longitude)  # получаем название часового пояса
            if timezone_str is None:
                bot.send_message(message.from_user.id, "Не удалось определить часовой пояс для данного города.")
                return
        except Exception as e:
            bot.send_message(message.from_user.id, f"Произошла ошибка при попытке определить часовой пояс: {str(e)}")
            return

        # Преобразование смещения в формат ±ЧЧ:ММ
        tz = pytz.timezone(timezone_str)
        tz_info = datetime.datetime.now(tz=tz).strftime("%z")  # Получаем смещение часового пояса
        tz_hours = tz_info[:3]  # Получаем часы
        tz_minutes = tz_info[3:]  # Получаем минуты

        # Приводим к формату ЧЧ:ММ
        tz_offset = f"{tz_hours}:{tz_minutes}"
        tz_offset_parts = tz_offset.split(":")
        hours = int(tz_offset_parts[0])
        minutes = int(tz_offset_parts[1])

        # Создаем объект timedelta
        time_difference = datetime.timedelta(hours=hours, minutes=minutes)
        bot.send_message(message.from_user.id, f"Часовой пояс установлен в {timezone_str} ({tz_info} от GMT).")
        bot.send_message(message.from_user.id,  "Во сколько вы хотели бы получать рекомендации? Запишите время в формате: ЧЧ:ММ", reply_markup=markup)
        bot.register_next_step_handler(message, time_recomendation)


def time_recomendation(message):
    global time_rec
    time_rec = message.text
    pattern = r'^[0-9]{2}:[0-9]{2}$' # <---добавить символы
    if re.match(pattern, time_rec):
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn3 = types.KeyboardButton('Муж')
        btn4 = types.KeyboardButton('Жен')
        btn5 = types.KeyboardButton('Пропустить')
        markup.add(btn3, btn4, btn5)
        bot.send_message(message.from_user.id, 'Укажите пол.', reply_markup=markup)
        bot.register_next_step_handler(message, fourth_question)
    else:
        bot.send_message(message.from_user.id, "😔 Не похоже на время. Попробуйте еще раз. Назови город")
        bot.register_next_step_handler(message, get_timezone)


def fourth_question(message):
    global gender
    gender = message.text
    if message.text == 'Муж' or message.text == 'Жен' or message.text == 'Пропустить':
        gender = message.text
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn6 = types.KeyboardButton('до 18')
        btn7 = types.KeyboardButton('от 18 до 25')
        btn8 = types.KeyboardButton('от 26 до 30')
        btn9 = types.KeyboardButton('от 31 до 35')
        btn10 = types.KeyboardButton('от 36 до 40')
        btn11 = types.KeyboardButton('от 41 до 45')
        btn12 = types.KeyboardButton('от 46 до 55')
        btn13 = types.KeyboardButton('старше 55')
        markup.add(btn6, btn7, btn8, btn9, btn10, btn11, btn12, btn13)
        bot.send_message(message.from_user.id, 'Укажите возраст.', reply_markup=markup)
        bot.register_next_step_handler(message, basadate)
    else:
        bot.send_message(message.from_user.id, 'Пожалуйста, выберите одну из предоставленных кнопок.')
        bot.register_next_step_handler(message, fourth_question)


def basadate(message):
    global age
    global status
    global A
    age = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
    btn16 = types.KeyboardButton('Меню')
    markup.add(btn16)
    bot.send_message(message.from_user.id, 'Успешная регистрация!', reply_markup=markup)
    bot.register_next_step_handler(message, menu)
def menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard = True)
    btn17 = types.KeyboardButton('🥳 Запустить новогодний адвент по цифровой гигиене')
    btn18 = types.KeyboardButton('😎 Мой профиль')
    btn19 = types.KeyboardButton('🧐 Рекомендации')
    btn20 = types.KeyboardButton('👍 Результаты выполнения')
    btn21 = types.KeyboardButton('😇 Пригласить друзей')
    btn22 = types.KeyboardButton('🤔 Пройти тест по цифровой гигиене')
    btn23 = types.KeyboardButton('👀 Об авторах')
    markup.add(btn17, btn18, btn19, btn20, btn21, btn22, btn23)
    bot.send_message(message.from_user.id, 'Меню', reply_markup=markup)
    bot.register_next_step_handler(message, choise)
    connection = sqlite3.connect('data.db')
    cursor = connection.cursor()
    cursor.execute(
        f"INSERT INTO users (id, user_id, user_name, tz_info, gr_rec, time_rec, gender, age) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, user_name, tz_info, gr_rec, time_rec, gender, age))
    connection.commit()
def choise(message):
    if message.text == '🥳 Запустить новогодний адвент по цифровой гигиене':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создание новых кнопок
        global gr_rec
        btn25 = types.KeyboardButton('Отметить как выполненное')
        btn26 = types.KeyboardButton('Отложить выполнение')
        btn27 = types.KeyboardButton('Меню')
        markup.add(btn25, btn26, btn27)
        if gr_rec == "Ежедневно":
            current_time = datetime.datetime.now() + time_difference
            user_time = datetime.datetime.strptime(time_rec, "%H:%M").time()
            day_of_week = datetime.datetime.now().weekday()  # Получаем номер дня недели (0 - Понедельник, 1 - Вторник, ..., 6 - Воскресенье)
            connection = sqlite3.connect('data.db')
            cursor = connection.cursor()
            for A in range(1, 31):
                cursor.execute("SELECT choice FROM data_ WHERE N = ?", (A,))
                result = cursor.fetchone()
                if result:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn29 = types.KeyboardButton('Меню')
                    markup.add(btn29, btn25, btn26)
                    bot.send_message(message.from_user.id, result[0], reply_markup=markup)
                    time.sleep(2)  #  86400пауза между сообщениями
        if gr_rec == 'Рабочие дни':
            for A in range(1, 31):
                connection = sqlite3.connect('data.db')
                cursor = connection.cursor()
                cursor.execute("SELECT choice FROM data_ WHERE N = ?", (A,))
                result = cursor.fetchone()
                if result:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn29 = types.KeyboardButton('Меню')
                    markup.add(btn29, btn25, btn26)
                    schedule.every().monday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
                    schedule.every().tuesday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
                    schedule.every().wednesday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
                    schedule.every().thursday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
                    schedule.every().friday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
        if gr_rec == 'Выходные дни':
            for A in range(1, 31):
                connection = sqlite3.connect('data.db')
                cursor = connection.cursor()
                cursor.execute("SELECT choice FROM data_ WHERE N = ?", (A,))
                result = cursor.fetchone()
                if result:
                    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                    btn29 = types.KeyboardButton('Меню')
                    markup.add(btn29, btn25, btn26)
                    schedule.every().saturday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
                    schedule.every().sunday.at(time_rec).do(bot.send_message(message.from_user.id, result[0], reply_markup=markup))
        bot.register_next_step_handler(message, menu)
    elif message.text == '😎 Мой профиль':
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        try:
            cursor.execute('SELECT user_name, gender, age, gr_rec FROM users WHERE user_id = ?', (message.from_user.id,))
            user_data = cursor.fetchone()
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            btn26 = types.KeyboardButton('Редактировать данные')
            btn27 = types.KeyboardButton('Меню')
            markup.add(btn26, btn27)
            if user_data:
                user_name, gender, age, gr_rec = user_data
                response_message = []
                if user_name:
                    response_message.append(f"🙂 Имя: {user_name}")
                if gr_rec:
                    response_message.append(f"👀 График получения рекомендаций и уведомлений: {gr_rec}")
                if gender:
                    response_message.append(f"🚻 Пол: {gender}")
                if age:
                    response_message.append(f"👨 Возраст: {age}")
                bot.send_message(message.from_user.id, "\n".join(response_message), reply_markup = markup)
                bot.register_next_step_handler(message, reg_again)
        except Exception as e:
            bot.send_message(message.from_user.id, f"Произошла ошибка: {str(e)}")
    elif message.text =='😇 Пригласить друзей':
        bot_username = bot.get_me().username
        invite_link = f"https://t.me/{bot_username}?start={message.from_user.id}"
        invite_text = "Привет! Присоединяйся к нашему боту и получай рекомендации и уведомления!"
        markup = types.InlineKeyboardMarkup()
        share_button = types.InlineKeyboardButton(text='Поделиться', switch_inline_query=invite_text)
        markup.add(share_button)
        bot.send_message(message.from_user.id, f"Пригласите друзей с помощью этой ссылки: {invite_link}\n{invite_text}", reply_markup=markup)
        bot.register_next_step_handler(message, menu)
    elif message.text == '🤔 Пройти тест по цифровой гигиене':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn28 = types.KeyboardButton('Пройти тест')
        markup.add(btn28)
        bot.send_message(message.from_user.id, 'Выполните все рекомендации и пройдите проверку знаний, получите звание Джедая ордена Цифровой гигиены и возможность скачать стикерпак от Киберпротекта', reply_markup=markup)
        bot.register_next_step_handler(message, test)
    elif message.text == '👀 Об авторах':
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn29 = types.KeyboardButton('Меню')
        markup.add(btn29)
        bot.send_message(message.from_user.id, 'Данный бот был разработан командой "МАОУ Гимназия города Юрги" - Рогов Пётр, Полухин Алексей, Дронов Лев, Купцов Илья, руководитель - учитель информатики Терентьева Елена Валерьевна. Ссылка на КиберЗаботу - https://cyber-care.ru/. Ссылка на КиберПротект - https://cyberprotect.ru/', reply_markup=markup)
        bot.register_next_step_handler(message, menu)


def test(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn29 = types.KeyboardButton('Меню')
    markup.add(btn29)
    if message.text == 'Пройти тест':
        bot.send_message(message.from_user.id, 'https://forms.yandex.ru/cloud/665528a43e9d08252ef19336/', reply_markup=markup)
        bot.register_next_step_handler(message, menu)


def reg_again(message):
    if message.text == 'Редактировать данные':
        connection = sqlite3.connect('data.db')
        cursor = connection.cursor()
        cursor.execute('DELETE FROM users WHERE user_id = ?', (message.from_user.id,))
        first_question(message)
        connection.commit()
    else:
        menu(message)
    if message.text == "Отметить как выполненное":
        conn = sqlite3.connect('data.db')
        cursor = conn.cursor()
        new_value = str(A)
        cursor.execute("SELECT status FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row is not None:
            current_value = row[0]
            sum_value = current_value + new_value
            cursor.execute("UPDATE users SET status=?  WHERE user_id = ?", (sum_value, user_id))
            conn.commit()

        else:

            bot.send_message(message.from_user.id, "Меню")
    elif message.text == "Выполнено":
        bot.send_message(message.from_user.id, "Выполнено")


bot.polling(none_stop=True, interval=0)