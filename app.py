from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

@app.route('/')
def home():
    return 'API do e-commerce está online!'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/api/products', methods=['GET'])
def get_products():
    data = request.get_json()
    nome = data.get('nome')
    preco = data.get('preco')
    descricao = data.get('descricao', '')

    if not nome or preco is None:
        return jsonify({'erro': 'Nome e preço são obrigatórios'}), 400

    conn = get_db_connection()
    conn.execute('INSERT INTO products (nome, preco, descricao) VALUES (?, ?, ?)', 
                 (nome, preco, descricao))
    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Produto criado com sucesso'}), 201

@app.route('/api/products/<int:produto_id>', methods=['PUT'])
def update_product(produto_id):
    data = request.get_json()
    nome = data.get('nome')
    preco = data.get('preco')
    descricao = data.get('descricao')

    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM products WHERE id = ?', (produto_id,)).fetchone()

    if produto is None:
        conn.close()
        return jsonify({'erro': 'Produto não encontrado'}), 404

    conn.execute('UPDATE products SET nome = ?, preco = ?, descricao = ? WHERE id = ?', 
                 (nome, preco, descricao, produto_id))
    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Produto atualizado com sucesso'})


@app.route('/api/products/<int:produto_id>', methods=['DELETE'])
def delete_product(produto_id):
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM products WHERE id = ?', (produto_id,)).fetchone()

    if produto is None:
        conn.close()
        return jsonify({'erro': 'Produto não encontrado'}), 404

    conn.execute('DELETE FROM products WHERE id = ?', (produto_id,))
    conn.commit()
    conn.close()

    return jsonify({'mensagem': 'Produto removido com sucesso'})



@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    user = conn.execute(
        'SELECT * FROM users WHERE username = ? AND password = ?', 
        (username, password)
    ).fetchone()
    conn.close()

    if user:
        return jsonify({'message': 'Login successful'})
    else:
        return jsonify({'message': 'Invalid credentials'}), 401

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
