from database import init_db
init_db()
import sqlite3
c = sqlite3.connect('chatbot.db')
print(c.execute("SELECT sql FROM sqlite_master WHERE name='party_rooms'").fetchone())
