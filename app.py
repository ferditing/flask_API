from flask import Flask, request, jsonify, render_template, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configure MySQL database; update with your MySQL username, password, host, and database name.
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:ferdi215@localhost:3307/library'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Flask-Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# ----------------------
# Database Models
# ----------------------
class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(120), nullable=False)
    author = db.Column(db.String(120), nullable=False)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)

class Borrower(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)

class BorrowRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    borrower_id = db.Column(db.Integer, db.ForeignKey('borrower.id'), nullable=False)
    book = db.relationship('Book', backref=db.backref('borrow_records', lazy=True))
    borrower = db.relationship('Borrower', backref=db.backref('borrow_records', lazy=True))

# ----------------------
# API Endpoints
# ----------------------

# Books Endpoints
@app.route('/books', methods=['GET'])
def get_books():
    books = Book.query.all()
    result = [{
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies
    } for book in books]
    return jsonify(result)

@app.route('/books', methods=['POST'])
def add_book():
    # Support both JSON (API) and form submissions (HTML)
    if request.content_type == 'application/json':
        data = request.json
    else:
        data = request.form
    total = int(data.get('total_copies', 1))
    new_book = Book(
        title=data.get('title'),
        author=data.get('author'),
        total_copies=total,
        available_copies=total
    )
    db.session.add(new_book)
    db.session.commit()
    if request.content_type == 'application/json':
        return jsonify({"id": new_book.id, "title": new_book.title}), 201
    else:
        return redirect(url_for('index'))

@app.route('/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    book = Book.query.get(book_id)
    if book:
        return jsonify({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "total_copies": book.total_copies,
            "available_copies": book.available_copies
        })
    return jsonify({"error": "Book not found"}), 404

@app.route('/books/<int:book_id>', methods=['PUT'])
def update_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    data = request.json
    book.title = data.get('title', book.title)
    book.author = data.get('author', book.author)
    if 'total_copies' in data:
        diff = int(data['total_copies']) - book.total_copies
        book.total_copies = int(data['total_copies'])
        book.available_copies += diff
        if book.available_copies < 0:
            book.available_copies = 0
    db.session.commit()
    return jsonify({
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "total_copies": book.total_copies,
        "available_copies": book.available_copies
    })

@app.route('/books/<int:book_id>', methods=['DELETE'])
def delete_book(book_id):
    book = Book.query.get(book_id)
    if not book:
        return jsonify({"error": "Book not found"}), 404
    db.session.delete(book)
    db.session.commit()
    return jsonify({"message": "Book deleted"})

# Borrowers Endpoints
@app.route('/borrowers', methods=['GET'])
def get_borrowers():
    borrowers = Borrower.query.all()
    result = []
    for borrower in borrowers:
        borrowed_books = [{
            "id": record.book.id,
            "title": record.book.title,
            "author": record.book.author,
            "total_copies": record.book.total_copies,
            "available_copies": record.book.available_copies
        } for record in borrower.borrow_records]
        result.append({
            "id": borrower.id,
            "name": borrower.name,
            "borrowed_books": borrowed_books
        })
    return jsonify(result)

@app.route('/borrowers', methods=['POST'])
def add_borrower():
    # If Content-Type is form data, use request.form
    if request.content_type.startswith('application/x-www-form-urlencoded'):
        name = request.form.get('name')
    # Otherwise, handle JSON
    elif request.content_type == 'application/json':
        data = request.json
        name = data.get('name')
    else:
        return jsonify({"error": "Unsupported Media Type"}), 415

    # Now create the new borrower
    new_borrower = Borrower(name=name)
    db.session.add(new_borrower)
    db.session.commit()
    return jsonify({"id": new_borrower.id, "name": new_borrower.name}), 201


# Borrow and Return Endpoints
@app.route('/borrow', methods=['POST'])
def borrow_book():
    data = request.json
    # Bulk creation support if "records" key exists
    if 'records' in data:
        results = []
        for rec in data['records']:
            book_id = rec.get('book_id')
            borrower_id = rec.get('borrower_id')
            book = Book.query.get(book_id)
            borrower = Borrower.query.get(borrower_id)
            if not book:
                results.append({"book_id": book_id, "borrower_id": borrower_id, "error": "Book not found"})
                continue
            if not borrower:
                results.append({"book_id": book_id, "borrower_id": borrower_id, "error": "Borrower not found"})
                continue
            if book.available_copies < 1:
                results.append({"book_id": book_id, "borrower_id": borrower_id, "error": "No available copies"})
                continue
            if BorrowRecord.query.filter_by(book_id=book_id, borrower_id=borrower_id).first():
                results.append({"book_id": book_id, "borrower_id": borrower_id, "error": "This borrower already has this book"})
                continue
            book.available_copies -= 1
            new_record = BorrowRecord(book_id=book_id, borrower_id=borrower_id)
            db.session.add(new_record)
            db.session.commit()
            results.append({"book_id": book_id, "borrower_id": borrower_id, "message": "Book borrowed successfully"})
        return jsonify(results)
    else:
        book_id = data.get('book_id')
        borrower_id = data.get('borrower_id')
        book = Book.query.get(book_id)
        borrower = Borrower.query.get(borrower_id)
        if not book:
            return jsonify({"error": "Book not found"}), 404
        if not borrower:
            return jsonify({"error": "Borrower not found"}), 404
        if book.available_copies < 1:
            return jsonify({"error": "No available copies"}), 400
        if BorrowRecord.query.filter_by(book_id=book_id, borrower_id=borrower_id).first():
            return jsonify({"error": "This borrower already has this book"}), 400
        book.available_copies -= 1
        new_record = BorrowRecord(book_id=book_id, borrower_id=borrower_id)
        db.session.add(new_record)
        db.session.commit()
        return jsonify({
            "message": "Book borrowed successfully",
            "book": {"id": book.id, "title": book.title},
            "borrower": {"id": borrower.id, "name": borrower.name}
        })

@app.route('/return', methods=['POST'])
def return_book():
    data = request.json
    book_id = data.get('book_id')
    borrower_id = data.get('borrower_id')
    record = BorrowRecord.query.filter_by(book_id=book_id, borrower_id=borrower_id).first()
    if not record:
        return jsonify({"error": "Borrow record not found"}), 404
    db.session.delete(record)
    book = Book.query.get(book_id)
    if book:
        book.available_copies += 1
    db.session.commit()
    return jsonify({"message": "Book returned successfully", "book": {"id": book.id, "title": book.title}})

@app.route('/borrow_records', methods=['GET'])
def get_borrow_records():
    records = BorrowRecord.query.all()
    result = []
    for record in records:
        result.append({
            "book": {
                "id": record.book.id,
                "title": record.book.title,
                "author": record.book.author,
                "total_copies": record.book.total_copies,
                "available_copies": record.book.available_copies
            },
            "borrower": {
                "id": record.borrower.id,
                "name": record.borrower.name
            }
        })
    return jsonify(result)

@app.route('/edit_borrower/<int:borrower_id>', methods=['GET', 'POST'])
def edit_borrower_page(borrower_id):
    borrower = Borrower.query.get(borrower_id)
    if not borrower:
        return jsonify({"error": "Borrower not found"}), 404

    if request.method == 'POST':
        # If the form is submitted (using application/x-www-form-urlencoded)
        name = request.form.get('name')
        if name:
            borrower.name = name
            db.session.commit()
            return redirect(url_for('index'))
        else:
            return render_template('edit_borrower.html', borrower=borrower, error="Name is required")
    
    # For GET, render the edit form with current borrower data
    return render_template('edit_borrower.html', borrower=borrower)


# ----------------------
# Front-End Routes (Hybrid Approach)
# ----------------------
@app.route('/')
def index():
    books = Book.query.all()
    borrowers = Borrower.query.all()
    return render_template('index.html', books=books, borrowers=borrowers)

@app.route('/add_book')
def add_book_page():
    return render_template('add_book.html')

@app.route('/borrow_book')
def borrow_book_page():
    return render_template('borrow_book.html')

@app.route('/return_book')
def return_book_page():
    return render_template('return_book.html')

@app.route('/add_borrower')
def add_borrower_page():
    return render_template('add_borrower.html')


if __name__ == '__main__':
    app.run(debug=True)
