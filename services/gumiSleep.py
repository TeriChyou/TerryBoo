import sqlite3
from datetime import *

def setUp():
    conn = sqlite3.connect('krskKmskBotDb.db')
    cursor = conn.cursor()
    try:
        cursor.execute('INSERT INTO breakLawTime VALUES ("Gumi", 0)')
        cursor.execute('INSERT INTO breakLawTime VALUES ("Fox", 0)')
        conn.commit()
    except Exception as e:
        print(e)

def add_times(name):
    conn = sqlite3.connect('krskKmskBotDb.db')
    cursor = conn.cursor()
    today = str(datetime.now().date())
    try:
        times = get_latest_times(name)[0] + 1
        cursor.execute('UPDATE breakLawTime SET time = ?, lastUpdate = ? WHERE id == ?', (times, today, name))
        conn.commit()
    except Exception as e:
        print(e)
    
def get_latest_times(name):
    conn = sqlite3.connect('krskKmskBotDb.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT time FROM breakLawTime where id == ?', (name,))
        return cursor.fetchone()
    except Exception as e:
        print(e)

def get_last_update(name):
    conn = sqlite3.connect('krskKmskBotDb.db')
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT lastUpdate FROM breakLawTime where id == ?', (name, ))
        return cursor.fetchone()
    except Exception as e:
        print(e)

def resetTime(name):
    conn = sqlite3.connect('krskKmskBotDb.db')
    cursor = conn.cursor()
    try:
        cursor.execute(f'UPDATE breakLawTime SET time = ? WHERE id == "{name}"', (0, ))
        conn.commit()
    except Exception as e:
        print(e)
