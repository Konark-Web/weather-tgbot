import asyncio

from creds import TOKEN, OWM_KEY

from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from pyowm import OWM
from pyowm.utils.config import get_default_config
from database.sqlClass import SqlConnect
from api.openweathermap import OpenWeatherMapName, OpenWeatherMapGeo

config_dict = get_default_config()
config_dict['language'] = 'ua'

loop = asyncio.get_event_loop()
bot = Bot(token=TOKEN, parse_mode='HTML')
dp = Dispatcher(bot, loop, storage=MemoryStorage())

owm = OWM(OWM_KEY, config_dict)
bot_v = '0.2'

mgr = owm.weather_manager()


class SetLocationGeo(StatesGroup):
    location = State()


class SetLocationName(StatesGroup):
    location = State()


class WeatherLocation(StatesGroup):
    location = State()


def get_keyboard_default():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.row('Погода у моєму місті')
    markup.row('Погода у іншому місті')
    markup.row('Задати місто', 'Змінити мову')

    return markup


def get_geo_keyboard():
    keyboard = InlineKeyboardMarkup()
    geo_button = InlineKeyboardButton(text='Гео-локація', callback_data='geo_position')
    name_button = InlineKeyboardButton(text='Назва', callback_data='name_city')
    keyboard.add(geo_button)
    keyboard.add(name_button)

    return keyboard


async def output_weather(message, weather, city_name=''):
    temp = weather.get_temp_now(True)
    temp_feels = weather.get_feels_like_now(True)

    if city_name:
        city = city_name
    else:
        city = message.text

    await message.reply('Погода у місті ' + city + ':\n' + weather.get_weather_now() + '\n'
                                        'Температура: ' + temp + ' °C (відчувається як ' + temp_feels + ' °C)\n'
                                        'Вологість повітря: ' + str(weather.get_humidity_now()) + '%\n'
                                        'Швидкість вітру: ' + str(weather.get_wind_speed_now()) + ' м/с\n'
                                        'Час світанку: ' + weather.get_sunrise_now() + ' | Час заходу: ' + weather.get_sunset_now(), reply_markup=get_keyboard_default())


@dp.message_handler(commands=['start'], state='*')
async def start_message(message: types.Message, state: FSMContext):
    await state.finish()
    await message.reply('Привіт! Це звичайний бот. Такий як всі. Що він вміє (буде вміти):\n'
                                      '- Погода зараз у любому куточку світу\n'
                                      '- Прогноз погоди на найближчі дні\n'
                                      '- Надсилати погоду в певний час (наприклад, вранці)\n\n'
                                      'Версія бота: ' + bot_v + ' | Розробник @Konark96')

    language_code = 'ua'

    if message.from_user.language_code == 'ru':
        language_code = 'ru'

    sql = SqlConnect()
    if sql.add_new_user(message.from_user.id, language_code):
        keyboard = InlineKeyboardMarkup()
        city_btn = InlineKeyboardButton(text='Задати своє місто', callback_data='set_city')
        language_btn = InlineKeyboardButton(text='Змінити мову', callback_data='change_language')
        keyboard.add(city_btn, language_btn)
        await bot.send_message(message.from_user.id, 'Ви успішно зареєструвалися. Виберіть дію.', reply_markup=keyboard)
    else:
        markup = get_keyboard_default()
        await bot.send_message(message.from_user.id, 'Що бажаєте зробити?\n\nЯкщо знайшли баг, пишіть @Konark96', reply_markup=markup)


@dp.callback_query_handler(text='set_city')
async def city_after_reg(data):
    await bot.send_message(data.message.from_user.id, 'Як Ви хочете задати своє місце за замовчуванням?',
                           reply_markup=get_geo_keyboard())


@dp.callback_query_handler(text='geo_position', state=None)
async def set_position_by_geo(data):
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    request_geo = KeyboardButton(text='Моя локація', request_location=True)
    keyboard.add(request_geo)
    await bot.send_message(data.message.chat.id, 'Відправ мені локацію', reply_markup=keyboard)
    await SetLocationGeo.location.set()


@dp.message_handler(content_types=['location'], state=SetLocationGeo.location)
async def change_default_geo(data, state: FSMContext):
    sql = SqlConnect()
    weather = OpenWeatherMapGeo(data.location.latitude, data.location.longitude)

    if sql.change_city(data.chat.id, weather):
        await bot.send_message(data.chat.id, 'Ваші гео-данні за замовчуванням змінені успішно.', reply_markup=get_keyboard_default())

    await output_weather(data, weather, weather.get_city_name())
    await state.finish()


@dp.callback_query_handler(text='name_city', state=None)
async def set_position_by_name(data):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    await bot.send_message(data.message.chat.id, 'Напишіть назву міста:', reply_markup=markup)
    await SetLocationName.location.set()


@dp.message_handler(state=SetLocationName.location)
async def change_default_name(data, state: FSMContext):
    try:
        weather = OpenWeatherMapName(data.text)

        if weather.get_all_info_now()['cod'] == '404':
            await data.reply('Такого міста не існує. Введіть корректну назву:')
            await SetLocationName.location.set()
        else:
            sql = SqlConnect()

            if sql.change_city(data.chat.id, weather):
                await bot.send_message(data.chat.id, 'Місто по замовчуванню змінено на ' + data.text)

            await output_weather(data, weather)

            await state.finish()
    except AssertionError:
        await data.reply('Назва повина бути строковую.')
        await SetLocationName.location.set()


@dp.message_handler(content_types=['text', 'location'], state=WeatherLocation.location)
async def weather_another_city(data, state: FSMContext):
    if data.location is None:
        weather = OpenWeatherMapName(data.text)

        if weather.get_all_info_now()['cod'] == '404':
            await data.reply('Такого міста не існує. Введіть корректну назву:')
            await WeatherLocation.location.set()

        await output_weather(data, weather, weather.get_city_name())
    else:
        weather = OpenWeatherMapGeo(data.location.latitude, data.location.longitude)

        await output_weather(data, weather, weather.get_city_name())

    await state.finish()


@dp.message_handler()
async def main_menu(message):
    if message.text == 'Погода у моєму місті':
        sql = SqlConnect()

        if sql.get_city_name(message.chat.id):
            weather = OpenWeatherMapName(sql.get_city_name(message.chat.id))

            await output_weather(message, weather, weather.get_city_name())
        elif sql.get_geo(message.chat.id):
            weather = OpenWeatherMapGeo(sql.get_geo(message.chat.id)[0], sql.get_geo(message.chat.id)[1])

            await output_weather(message, weather, weather.get_city_name())
        else:
            await message.reply('Нажаль, у вас не задано місце за замовчуванням. Пропонуємо додати його.', reply_markup=get_geo_keyboard())
    elif message.text == 'Погода у іншому місті':
        await message.reply('Введіть місто або відправте локацію.')
        await WeatherLocation.location.set()
    elif message.text == 'Задати місто':
        await bot.send_message(message.from_user.id, 'Як Ви хочете задати своє місце за замовчуванням?',
                               reply_markup=get_geo_keyboard())


if __name__ == '__main__':
    executor.start_polling(dp)
