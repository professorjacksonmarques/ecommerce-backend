from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

# ---------- Conexão (defina ANTES de init_db) ----------
def get_db_connection():
    conn = sqlite3.connect('database.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- Init DB (cria tabelas e seed admin/123 hasheado) ----------
def init_db():
    conn = get_db_connection()
    cur = conn.cursor()

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
    )''')

    # seed admin (se não existir)
    admin = cur.execute('SELECT 1 FROM users WHERE username=?', ('admin',)).fetchone()
    if not admin:
        cur.execute(
            'INSERT INTO users (username, password) VALUES (?, ?)',
            ('admin', generate_password_hash('123'))
        )

    conn.commit()
    conn.close()

# chame o init após definir as funções
init_db()

# ---------- Healthcheck ----------
@app.route('/', methods=['GET', 'HEAD'])
def home():
    return 'API do e-commerce está online!'

# ---------- PRODUCTS ----------
@app.route('/api/products', methods=['GET'])
def list_products():
    conn = get_db_connection()
    rows = conn.execute('SELECT * FROM products').fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows]), 200

@app.route('/api/products/<int:produto_id>', methods=['GET'])
def get_product(produto_id):
    conn = get_db_connection()
    row = conn.execute('SELECT * FROM products WHERE id = ?', (produto_id,)).fetchone()
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

    if not nome or preco is None:
        return jsonify({'erro': 'Nome e preço são obrigatórios'}), 400

    conn = get_db_connection()
    cur = conn.execute(
        'INSERT INTO products (nome, preco, descricao) VALUES (?, ?, ?)',
        (nome, preco, descricao)
    )
    conn.commit()
    new_id = cur.lastrowid
    novo = conn.execute('SELECT * FROM products WHERE id = ?', (new_id,)).fetchone()
    conn.close()
    return jsonify(dict(novo)), 201

@app.route('/api/products/<int:produto_id>', methods=['PUT'])
def update_product(produto_id):
    data = request.get_json(force=True) or {}

    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM products WHERE id = ?', (produto_id,)).fetchone()
    if not produto:
        conn.close()
        return jsonify({'erro': 'Produto não encontrado'}), 404

    nome = data.get('nome', produto['nome'])
    preco = data.get('preco', produto['preco'])
    descricao = data.get('descricao', produto['descricao'])

    conn.execute(
        'UPDATE products SET nome = ?, preco = ?, descricao = ? WHERE id = ?',
        (nome, preco, descricao, produto_id)
    )
    conn.commit()
    atualizado = conn.execute('SELECT * FROM products WHERE id = ?', (produto_id,)).fetchone()
    conn.close()
    return jsonify(dict(atualizado)), 200

@app.route('/api/products/<int:produto_id>', methods=['DELETE'])
def delete_product(produto_id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM products WHERE id = ?', (produto_id,)).fetchone()
    if not produto:
        conn.close()
        return jsonify({'erro': 'Produto não encontrado'}), 404

    conn.execute('DELETE FROM products WHERE id = ?', (produto_id,))
    conn.commit()
    conn.close()
    return jsonify({'mensagem': 'Produto removido com sucesso'}), 200

# ---------- AUTH ----------
@app.route('/api/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return jsonify({
            "hint": "Use POST com JSON para autenticar.",
            "exemplo": {"username": "admin", "password": "123"}
        }), 200

    data = request.get_json(force=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'username e password são obrigatórios'}), 400

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
    conn.close()

    if user and check_password_hash(user['password'], password):
        return jsonify({'message': 'Login successful'}), 200
    return jsonify({'message': 'Invalid credentials'}), 401

# ---------- Execução local ----------
if __name__ == '__main__':
    # Em produção use gunicorn (Render).
    app.run(host='0.0.0.0', port=5000, debug=True)
