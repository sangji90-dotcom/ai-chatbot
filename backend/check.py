import sqlite3
c = sqlite3.connect('chatbot.db')
print(c.execute('SELECT code, created_at FROM party_rooms ORDER BY id DESC LIMIT 2').fetchall())
