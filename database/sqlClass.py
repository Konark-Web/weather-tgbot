import sqlite3


class SqlConnect:
    def __init__(self):
        self.conn = sqlite3.connect('main.db')
        self.cursor = self.conn.cursor()

    def add_new_user(self, user_id, language_default):
        self.cursor.execute("SELECT * from users where user_id = ?", (user_id,))
        user_status = self.cursor.fetchone()

        if not user_status:
            self.cursor.execute("INSERT INTO users(user_id, lang) VALUES (?, ?)", (user_id, language_default))
            self.conn.commit()

            return True
        else:
            return False

    def change_language(self, language, user_id):
        self.cursor.execute("UPDATE users SET lang = ? WHERE user_id = ?", (language, user_id))
        self.conn.commit()

    def change_city(self, user_id, weather):
        city = weather.get_city_name()
        longitude, latitude = weather.get_coord_city()

        self.cursor.execute("SELECT city from users where user_id = ?", (user_id,))
        current_city = self.cursor.fetchone()

        self.cursor.execute("SELECT latitude from users where user_id = ?", (user_id,))
        current_latitude = self.cursor.fetchone()

        self.cursor.execute("SELECT longitude from users where user_id = ?", (user_id,))
        current_longitude = self.cursor.fetchone()

        if current_city[0] == city and current_longitude[0] == longitude and current_latitude[0] == latitude:
            return False
        else:
            self.cursor.execute("UPDATE users SET city = ?, latitude = ?, longitude = ? WHERE user_id = ?", (city, latitude, longitude, user_id))
            self.conn.commit()

            return True

    def change_geo(self, user_id, latitude, longitude):
        self.cursor.execute("SELECT latitude from users where user_id = ?", (user_id,))
        current_latitude = self.cursor.fetchone()

        self.cursor.execute("SELECT longitude from users where user_id = ?", (user_id,))
        current_longitude = self.cursor.fetchone()

        print(current_longitude[0] == longitude)

        if current_longitude[0] != '0' and current_latitude[0] != '0':
            if current_longitude[0] == longitude and current_latitude[0] == latitude:
                return False
            else:
                self.cursor.execute("UPDATE users SET latitude = ?, longitude = ?, city = 'None' WHERE user_id = ?", (latitude, longitude, user_id))
                self.conn.commit()

                return True

    def get_city_name(self, user_id):
        self.cursor.execute("SELECT city from users where user_id = ?", (user_id,))
        current_city = self.cursor.fetchone()

        if current_city[0] != 'None':
            return current_city[0]

        return False

    def get_geo(self, user_id):
        self.cursor.execute("SELECT latitude from users where user_id = ?", (user_id,))
        current_latitude = self.cursor.fetchone()

        self.cursor.execute("SELECT longitude from users where user_id = ?", (user_id,))
        current_longitude = self.cursor.fetchone()

        if current_longitude[0] and current_latitude[0]:
            return current_longitude[0], current_latitude[0]

        return False