import telebot
import pyowm
from pyowm import OWM
from pyowm.utils.config import get_default_config
from database.sqlClass import SqlConnect
from creds import TOKEN, OWM_KEY

config_dict = get_default_config()
config_dict['language'] = 'ua'

bot = telebot.TeleBot(TOKEN)
owm = OWM(OWM_KEY, config_dict)
bot_v = '0.2'

mgr = owm.weather_manager()


@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, 'Привіт! Це звичайний бот. Такий як всі. Що він вміє (буде вміти):\n'
                                      '- Погода зараз у любому куточку світу\n'
                                      '- Прогноз погоди на найближчі дні\n'
                                      '- Надсилати погоду в певний час (наприклад, вранці)\n\n'
                                      'Версія бота: ' + bot_v + ' | Розробник @Konark96')

    sql = SqlConnect()

    if message.from_user.language_code == 'ru':
        language_code = 'ru'
    else:
        language_code = 'ua'

    if sql.add_new_user(message.chat.id, language_code):
        keyboard = telebot.types.InlineKeyboardMarkup()
        city_btn = telebot.types.InlineKeyboardButton(text='Задати місто', callback_data='set_city')
        language_btn = telebot.types.InlineKeyboardButton(text='Змінити мову', callback_data='change_language')
        keyboard.add(city_btn, language_btn)
        bot.send_message(message.chat.id, 'Ви успішно зареєструвалися. Виберіть дію.', reply_markup=keyboard)
    else:
        markup = get_keyboard_default()
        bot.send_message(message.chat.id, 'Що бажаєте зробити?\n\nЯкщо знайшли баг, пишіть @Konark96', reply_markup=markup)


@bot.message_handler(content_types=['text'])
def send_text(message):
    if message.text == 'Задати місто':
        set_city(message)
    else:
        markup = get_keyboard_default()
        bot.send_message(message.chat.id, 'Не зрозуміла команда. Виберіть що Ви хочете зробити.', reply_markup=markup)


@bot.callback_query_handler(lambda geo: geo.data == 'geo_position')
def request_geo(geo):
    keyboard = telebot.types.ReplyKeyboardMarkup(True)
    request_geo = telebot.types.KeyboardButton(text='Моя локація', request_location=True)
    keyboard.add(request_geo)
    bot.send_message(geo.message.chat.id, 'Відправ мені свою локацію', reply_markup=keyboard)


@bot.callback_query_handler(lambda geo: geo.data == 'name_city')
def location_by_name(city):
    bot.send_message(city.message.chat.id, 'Напишіть назву міста:')
    bot.register_next_step_handler(city.message, get_weather_by_name)


@bot.callback_query_handler(lambda after_reg: after_reg.data == 'set_city')
def set_city_after_reg(chat):
    set_city(chat.message)


@bot.callback_query_handler(lambda after_reg: after_reg.data == 'change_language')
def set_city_after_reg(chat):
    keyboard = telebot.types.InlineKeyboardMarkup()
    ua_btn = telebot.types.InlineKeyboardButton(text='Україньска 🇺🇦', callback_data='ua')
    ru_btn = telebot.types.InlineKeyboardButton(text='Русский 🇷🇺', callback_data='ru')
    keyboard.add(ua_btn, ru_btn)
    bot.send_message(chat.message.chat.id, 'Виберіть мову бота.', reply_markup=keyboard)


@bot.callback_query_handler(lambda language: language.data == 'ua' or language.data == 'ru')
def set_bot_language(chat):
    sql = SqlConnect()

    sql.change_language(chat.data, chat.message.chat.id)
    bot.send_message(chat.message.chat.id, 'Мова успішно змінена.')


def get_weather_by_name(message):
    try:
        observation = mgr.weather_at_place(message.text)
        w = observation.weather
        output_weather(message, w)

        sql = SqlConnect()

        if sql.change_city(message.chat.id, message.text):
            bot.send_message(message.chat.id, 'Місто по замовчуванню змінено на ' + message.text)

    except pyowm.commons.exceptions.NotFoundError:
        bot.send_message(message.chat.id, 'Такого міста не існує. Введіть корректну назву:')
        bot.register_next_step_handler(message, get_weather_by_name)

    except AssertionError:
        bot.send_message(message.chat.id, 'Назва повина бути строковую.')
        bot.register_next_step_handler(message, get_weather_by_name)


def output_weather(message, weather, city_name = ''):
    temp = str(int(float(weather.temperature('celsius')['temp'])))
    temp_feels = str(int(weather.temperature('celsius')['feels_like']))
    keyboard_hider = telebot.types.ReplyKeyboardRemove()

    if city_name:
        city = city_name
    else:
        city = message.text

    bot.send_message(message.chat.id, 'Погода у місті ' + city + ':\n' + weather.detailed_status.title() + '\n'
                                        'Температура: ' + temp + ' °C (відчувається як ' + temp_feels + ' °C)\n'
                                        'Вологість повітря: ' + str(weather.humidity) + '%\n'
                                        'Швидкість вітру: ' + str(weather.wind()['speed']) + ' м/с\n', reply_markup=keyboard_hider)


@bot.message_handler(content_types=['location'])
def get_location(message):
    observation = mgr.weather_at_coords(message.location.latitude, message.location.longitude)
    w = observation.weather

    output_weather(message, w, observation.location.name)


def set_city(message):
    keyboard = telebot.types.InlineKeyboardMarkup()
    geo_button = telebot.types.InlineKeyboardButton(text='Гео-локація', callback_data='geo_position')
    name_button = telebot.types.InlineKeyboardButton(text='Назва', callback_data='name_city')
    keyboard.add(geo_button)
    keyboard.add(name_button)
    bot.send_message(message.chat.id, 'Як Ви хочете задати своє місце по замовчуванню?', reply_markup=keyboard)


def get_keyboard_default():
    markup = telebot.types.ReplyKeyboardMarkup(True)
    markup.row('Погода у моєму місті')
    markup.row('Погода у іншому місті')
    markup.row('Задати місто', 'Змінити мову')

    return markup


if __name__ == '__main__':
    bot.polling(none_stop=True)
