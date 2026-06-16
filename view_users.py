import sqlite3

conn = sqlite3.connect("gioco.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM utenti")
users = cursor.fetchall()

for user in users:
    print(user)

conn.close()