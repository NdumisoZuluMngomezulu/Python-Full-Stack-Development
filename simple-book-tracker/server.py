from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3

app = Flask(__name__)
CORS(app)

def get_db():
    conn = sqlite3.connect('books.db')
    conn.row_factory = sqlite3.Row
    return conn

with get_db() as db:
    db.execute('CREATE TABLE IF NOT EXISTS books' \
    '(id INTEGER PRIMARY KEY, title TEXT, author TEXT)')

@app.route('/books', methods=['GET'])

def get_books():
    db = get_db()
    books = db.execute('SELECT * FROM books').fetchall()
    return jsonify([dict(book) for book in books])

@app.route('/books', methods=['POST'])

def add_book():
    data = request.json
    db = get_db()
    db.execute('INSERT INTO books (title, author) VALUES (?,?)',(data['title'], data['author']))
    db.commit()
    return jsonify({'status':'success'}), 201

if __name__ == '__main__':
    app.run(debug=True)