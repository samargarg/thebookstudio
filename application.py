import os
import requests
from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

KEY = "pjHZqNdhxeCBfylFh29HA"

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=["POST", "GET"])
def index():    
    if 'username' in session:
        username = session['username']
        user = db.execute("SELECT * FROM users WHERE username=:username", {"username": username}).first()
        return render_template("index.html", name=user.name)
    
    else:
        return render_template("index.html", username=None)

@app.route("/login", methods=["POST", "GET"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = db.execute("SELECT * FROM users WHERE username=:username AND password=:password", {"username": username, "password": password}).first()
        if db.execute("SELECT * FROM users WHERE username=:username AND password=:password", {"username": username, "password": password}).rowcount == 0:
            return render_template("login.html", message="Invalid Credentials") 

        else:
            session['username'] = username
            return redirect(url_for('index'))

    else:
        return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route("/register", methods=["POST", "GET"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        username = request.form.get("username")
        if db.execute("SELECT FROM users WHERE username=:username", {"username": username}).rowcount != 0:
            return render_template("register.html", message="EMAIL ADDRESS ALREADY REGISTERED WITH ANOTHER ACCOUNT!")
        password = request.form.get("password")
        if (name or username or password) is "":
            return render_template("register.html", message="ALL FIELDS ARE MANDATORY!")
        db.execute("INSERT INTO users (name, username, password) VALUES (:name, :username, :password)", 
                    {"name": name, "username": username, "password": password})
        db.commit()
        session['username'] = username
        return redirect(url_for('index'))
    else:
        return render_template("register.html")

@app.route("/search", methods=["POST", "GET"])
def search():
    search_item = "%" + request.form.get("search_item") + "%"
    books = db.execute("SELECT books.id, title, name FROM books JOIN authors ON books.author_id = authors.id WHERE UPPER(title) LIKE UPPER(:search_item) OR UPPER(name) LIKE UPPER(:search_item) OR isbn LIKE UPPER(:search_item) OR year LIKE :search_item", {"search_item": search_item})
    return render_template("search.html", books=books, search_item=search_item)

@app.route("/book/<int:book_id>", methods=["POST", "GET"])
def book(book_id):
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        comment = request.form.get("comment")
        if comment is "":
            db.execute("INSERT INTO reviews (book_id, username, rating) VALUES (:book_id, :username, :rating)", 
                    {"book_id": book_id, "username": session['username'], "rating": rating})
        else:
            db.execute("INSERT INTO reviews (book_id, username, rating, comment) VALUES (:book_id, :username, :rating, :comment)", 
                        {"book_id": book_id, "username": session['username'], "rating": rating, "comment": comment})
        db.commit()

    
    book = db.execute("SELECT books.id, isbn, title, name, year FROM books JOIN authors ON books.author_id = authors.id WHERE books.id = :book_id", {"book_id": book_id}).first()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": book['isbn']})
    data = res.json()
    
    # res = requests.get(" https://www.goodreads.com/review/recent_reviews.xml", params={"key": KEY, "isbn": "553376055", "user_id": 114941005})
    if 'username' in session:
        
        reviews = db.execute("SELECT name, rating, comment FROM reviews JOIN users ON reviews.username = users.username WHERE book_id=:book_id", {"book_id": book_id})

        if db.execute("SELECT * FROM reviews WHERE username=:username AND book_id=:book_id", {"username": session['username'], "book_id": book_id}).rowcount != 0:
            review = db.execute("SELECT * FROM reviews WHERE username=:username AND book_id=:book_id", {"username": session['username'], "book_id": book_id}).first()
            return render_template("book.html", book=book, review=review, reviews=reviews, data=data)

        else:
            return render_template("book.html", book=book, review=None, reviews=reviews, data=data)
    
    
    else:
        return render_template("book.html", book=book, review=None, reviews=None, data=data)

@app.route("/api/<string:isbn>")
def api(isbn):
    book = db.execute("SELECT books.id, title, name, year FROM books JOIN authors ON books.author_id = authors.id WHERE isbn = :isbn", {"isbn": isbn}).first()
    review_data = db.execute("SELECT AVG(rating), COUNT(rating) FROM reviews WHERE book_id=:book_id", {"book_id": book.id}).first()
    return jsonify({
        "title": book.title,
        "author": book.name,
        "year": book.year,
        "isbn": isbn,
        "review_count": review_data[1],
        "average_score": review_data[0]
    })
