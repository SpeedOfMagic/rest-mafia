import sqlite3


class ProfileDao:
    DATABASE_NAME = 'profiles.db'

    connection: sqlite3.Connection

    def __init__(self):
        pass
