from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

def get_db_connection():
    conn = psycopg2.connect('database.db')
    conn.row_factory = psycopg2.Row
    return conn

@app.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return jsonify([dict(p) for p in products])

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?', 
        (username, password)).fetchone()
    conn.close()

    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(debug=True)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

    # Tabelas
    cur.execute('''CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
    )''')

    cur.execute('''CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        preco REAL NOT NULL,
        descricao TEXT
        -- OBS: sem estoque aqui porque vamos garantir por migração abaixo
    )''')

    # ---- MIGRAÇÃO: adiciona coluna 'estoque' se não existir ----
    cols = [r['name'] for r in cur.execute('PRAGMA table_info(products)').fetchall()]
    if 'estoque' not in cols:
        cur.execute('ALTER TABLE products ADD COLUMN estoque INTEGER NOT NULL DEFAULT 0')

        # Se quiser dar um estoque inicial aos itens existentes:
        cur.execute('UPDATE products SET estoque = 10 WHERE estoque IS NULL')  # opcional

    # Seed admin (se não existir)
    admin = cur.execute('SELECT 1 FROM users WHERE username=?', ('admin',)).fetchone()
    if not admin:
        cur.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            ('admin', generate_password_hash('123'))
        )

    conn.commit()
    conn.close()

@app.route('/api/products', methods=['GET'])
def list_products():
    conn = get_db_connection()
    rows = conn.execute('SELECT id, nome, preco, descricao, estoque FROM products').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200

@app.route('/api/products/<int:produto_id>', methods=['GET'])
def get_product(produto_id):
    conn = get_db_connection()
    row = conn.execute('SELECT id, nome, preco, descricao, estoque FROM products WHERE id = ?', (produto_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    return jsonify(dict(row)), 200

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json(force=True) or {}
    nome = data.get('nome')
    preco = data.get('preco')
    descricao = data.get('descricao', '')
    estoque = int(data.get('estoque', 0))

    if not nome or preco is None:
        return jsonify({'erro': 'Nome e preço são obrigatórios'}), 400

    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO products (nome, preco, descricao, estoque) VALUES (?, ?, ?, ?)',
        (nome, preco, descricao, estoque)
    )
    conn.commit()
    new_id = cur.lastrowid
    novo = conn.execute('SELECT id, nome, preco, descricao, estoque FROM products WHERE id = ?', (new_id,)).fetchone()
    conn.close()
    return jsonify(dict(novo)), 201

@app.route('/api/products', methods=['POST'])
def create_product():
    data = request.get_json(force=True) or {}
    nome = data.get('nome')
    preco = data.get('preco')
    descricao = data.get('descricao', '')
    estoque = int(data.get('estoque', 0))

    if not nome or preco is None:
        return jsonify({'erro': 'Nome e preço são obrigatórios'}), 400

    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO products (nome, preco, descricao, estoque) VALUES (?, ?, ?, ?)',
        (nome, preco, descricao, estoque)
    )
    conn.commit()
    new_id = cur.lastrowid
    novo = conn.execute('SELECT id, nome, preco, descricao, estoque FROM products WHERE id = ?', (new_id,)).fetchone()
    conn.close()
    return jsonify(dict(novo)), 201

@app.route('/api/products/<int:produto_id>', methods=['PUT'])
def update_product(produto_id):
    data = request.get_json(force=True) or {}

    conn = get_db_connection()
    produto = conn.execute('SELECT id, nome, preco, descricao, estoque FROM products WHERE id = ?', (produto_id,)).fetchone()
    if not produto:
        conn.close()
        return jsonify({'erro': 'Produto não encontrado'}), 404

    nome = data.get('nome', produto['nome'])
    preco = data.get('preco', produto['preco'])
    descricao = data.get('descricao', produto['descricao'])
    estoque = int(data.get('estoque', produto['estoque']))

    conn.execute(
        'UPDATE products SET nome = ?, preco = ?, descricao = ?, estoque = ? WHERE id = ?',
        (nome, preco, descricao, estoque, produto_id)
    )
    conn.commit()
    atualizado = conn.execute('SELECT id, nome, preco, descricao, estoque FROM products WHERE id = ?', (produto_id,)).fetchone()
    conn.close()
    return jsonify(dict(atualizado)), 200

@app.route('/api/estoque/<int:produto_id>', methods=['GET'])
def get_estoque(produto_id):
    conn = get_db_connection()
    row = conn.execute('SELECT estoque FROM products WHERE id = ?', (produto_id,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    return jsonify({'id': produto_id, 'estoque': row['estoque']}), 200

@app.route('/api/estoque/<int:produto_id>', methods=['PUT'])
def set_estoque(produto_id):
    data = request.get_json(force=True) or {}
    if 'estoque' not in data:
        return jsonify({'erro': 'Campo "estoque" é obrigatório'}), 400

    novo_estoque = int(data['estoque'])
    conn = get_db_connection()
    cur = conn.execute('UPDATE products SET estoque = ? WHERE id = ?', (novo_estoque, produto_id))
    conn.commit()
    afetados = cur.rowcount
    conn.close()
    if afetados == 0:
        return jsonify({'erro': 'Produto não encontrado'}), 404
    return jsonify({'mensagem': 'Estoque atualizado', 'id': produto_id, 'estoque': novo_estoque}), 200

import os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2
import psycopg2.extras

app = Flask(__name__)
CORS(app)

DATABASE_URL = os.getenv("DATABASE_URL")  # defina no Render

def get_db_connection():
    # Aiven exige SSL; sua URL já terá ?sslmode=require
    return psycopg2.connect(DATABASE_URL)

def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    # Tabelas (DDL idempotente)
    cur.execute("""
      CREATE TABLE IF NOT EXISTS users(
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL
      );
    """)
    cur.execute("""
      CREATE TABLE IF NOT EXISTS products(
        id SERIAL PRIMARY KEY,
        nome TEXT NOT NULL,
        preco DOUBLE PRECISION NOT NULL,
        descricao TEXT,
        estoque INTEGER NOT NULL DEFAULT 0
      );
    """)
    # Seed admin (hasheado) se não existir
    cur.execute("SELECT 1 FROM users WHERE username=%s;", ('admin',))
    if cur.fetchone() is None:
        cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s);",
            ('admin', generate_password_hash('123'))
        )
    conn.commit()
    cur.close()
    conn.close()

# chame a migração/DDL no start
init_db()
