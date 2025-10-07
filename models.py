import sqlite3
import os

DB_FILE = 'database.db'

def initialize_db():
    new_db = not os.path.exists(DB_FILE)
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    if new_db:
        c.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
        ''')

        c.execute('''
        CREATE TABLE products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        );
        ''')

        c.execute("INSERT INTO users (username, password) VALUES ('admin', 'admin')")
        c.execute("INSERT INTO products (name, price, stock) VALUES ('Camiseta', 49.90, 10)")
        c.execute("INSERT INTO products (name, price, stock) VALUES ('Tênis', 199.90, 5)")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    initialize_db()
    print("Database initialized.")
