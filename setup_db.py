import sqlite3

conn = sqlite3.connect('database.db')
cursor = conn.cursor()

# Tabela de usuários
cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL
)
''')

# Tabela de produtos
cursor.execute('''
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    preco REAL NOT NULL,
    descricao TEXT
)
''')

# Inserir usuário admin
cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', ('admin', '123'))

# Inserir produtos
cursor.execute('INSERT INTO products (nome, preco, descricao) VALUES (?, ?, ?)',
               ('Camiseta Preta', 59.90, 'Camiseta básica de algodão preta'))

cursor.execute('INSERT INTO products (nome, preco, descricao) VALUES (?, ?, ?)',
               ('Tênis Esportivo', 199.90, 'Tênis leve e confortável'))

conn.commit()
conn.close()

print("Banco criado com sucesso!")
