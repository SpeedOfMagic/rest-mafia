import sqlite3


class Profile:
    login: str
    password: str
    name: str
    image: bytes
    gender: str
    mail: str
    total_time: int
    session_count: int
    win_count: int
    lose_count: int

    def __init__(self, login, password, name='', image=b'', gender='', mail='',
                 total_time=0, session_count=0, win_count=0, lose_count=0):
        self.login = login
        self.password = password
        self.name = name
        self.image = image
        self.gender = gender
        self.mail = mail
        self.total_time = total_time
        self.session_count = session_count
        self.win_count = win_count
        self.lose_count = lose_count


class ProfileDao:
    DB_PATH = 'profiles.db'

    connection: sqlite3.Connection

    def __init__(self):
        self.connection = sqlite3.connect(self.DB_PATH)
        self.connection.row_factory = sqlite3.Row

        self.connection.cursor().execute('''CREATE TABLE IF NOT EXISTS "Profiles" (
            "login" STRING PRIMARY KEY,
            "password" STRING NOT NULL,  -- Actually sha256 of a real password
            "name" STRING NOT NULL,
            "image" STRING NOT NULL,
            "gender" STRING NOT NULL,
            "mail" STRING NOT NULL,
            "total_time" INTEGER NOT NULL,
            "session_count" INTEGER NOT NULL,
            "win_count" INTEGER NOT NULL,
            "lose_count" INTEGER NOT NULL
        );''')
        self.connection.commit()

    def insert_profile(self, profile: Profile) -> None:
        self.connection.cursor().execute('INSERT INTO Profiles VALUES (?,?,?,?,?,?,?,?,?,?)', (
            profile.login, profile.password, profile.name, profile.image, profile.gender, profile.mail,
            profile.total_time, profile.session_count, profile.win_count, profile.lose_count
        ))
        self.connection.commit()

    def lookup_profile(self, login: str) -> Profile:
        cursor = self.connection.cursor()
        cursor.execute('SELECT * FROM Profiles WHERE "login"=?', (login,))
        row = cursor.fetchone()
        cursor.close()
        return Profile(**row)

    def modify_profile(self, login: str, password=None, name=None, image=None, gender=None, mail=None) -> None:
        profile = self.lookup_profile(login)
        profile.password = profile.password if password is None else password
        profile.name = profile.name if name is None else name
        profile.image = profile.image if image is None else image
        profile.gender = profile.gender if gender is None else gender
        profile.mail = profile.mail if mail is None else mail

        self.connection.cursor().execute(
            '''UPDATE Profiles
            SET password = ?, name = ?, image = ?, gender = ?, mail = ?
            WHERE login = ?''',
            (profile.password, profile.name, profile.image, profile.gender, profile.mail, profile.login))
        self.connection.commit()

    def finish_game(self, login: str, total_time: int, won: bool) -> None:
        profile = self.lookup_profile(login)
        profile.total_time += total_time
        profile.session_count += 1
        profile.win_count += won
        profile.lose_count += not won
        self.connection.cursor().execute(
            '''UPDATE Profiles
            SET total_time = ?, session_count = ?, win_count = ?, lose_count = ?
            WHERE login = ?''',
            (profile.total_time, profile.session_count, profile.win_count, profile.lose_count, profile.login))
