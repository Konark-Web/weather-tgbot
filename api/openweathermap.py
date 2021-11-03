import requests
from datetime import datetime, timedelta
from creds import API_KEY


class OpenWeatherMapName:
    def __init__(self, city='None', lang='ua'):
        self.api_key = API_KEY
        self.city = city
        self.lang = lang
        self.weather_url = 'http://api.openweathermap.org/data/2.5/weather?q=' + self.city + '&APPID=' + self.api_key + '&lang=' + self.lang + '&units=metric'
        self.request = requests.get(self.weather_url)
        self.request_json = self.request.json()

    def get_all_info_now(self):
        return self.request_json

    def get_weather_now(self):
        return self.request_json['weather'][0]['description']

    def get_temp_now(self, round=False):
        if round:
            return str(int(float(self.request_json['main']['temp'])))

        return self.request_json['main']['temp']

    def get_feels_like_now(self, round=False):
        if round:
            return str(int(float(self.request_json['main']['feels_like'])))

        return self.request_json['main']['feels_like']

    def get_humidity_now(self):
        return self.request_json['main']['humidity']

    def get_wind_speed_now(self):
        return self.request_json['wind']['speed']

    def get_sunrise_now(self):
        return datetime.fromtimestamp(self.request_json['sys']['sunrise']).strftime('%H:%M:%S')

    def get_sunset_now(self):
        return datetime.fromtimestamp(self.request_json['sys']['sunset']).strftime('%H:%M:%S')

    def get_time_now(self):
        return datetime.fromtimestamp(self.request_json['dt']).strftime('%d-%m-%Y %H:%M:%S')

    def get_coord_city(self):
        return self.request_json['coord']['lon'], self.request_json['coord']['lat']

    def get_city_name(self):
        return self.request_json['name']


class OpenWeatherMapGeo(OpenWeatherMapName):
    def __init__(self, lat, lon, lang='ua', city='None'):
        super().__init__(city, lang)
        self.lat = lat
        self.lon = lon
        self.weather_url = 'http://api.openweathermap.org/data/2.5/weather?lat=' + str(self.lat) + '&lon=' + str(self.lon) + '&APPID=' + self.api_key + '&lang=' + self.lang + '&units=metric'
        self.request = requests.get(self.weather_url)
        self.request_json = self.request.json()