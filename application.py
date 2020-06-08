import os
import requests

from flask import Flask, session, render_template, request, redirect, url_for, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
KEY = "6WZXBFDyxoZRMow0jQZjA"

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


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/check_registration", methods=["GET","POST"])
def check_registration():
    # Get form information.
    first_name = request.form.get("first_name")
    last_name = request.form.get("last_name")
    email = request.form.get("email")
    password = generate_password_hash(request.form.get("password"))
    date_created = datetime.now()

    # Make sure user doesn't exist already.
    if db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).rowcount == 1:
        return render_template("register.html", message="Email has already been used.",first_name=first_name, last_name=last_name);

    #make sure passwords where the same
    if not request.form.get("password") == request.form.get("password_confirm"):
        return render_template("register.html", message="Passwords do not match.",first_name=first_name, last_name=last_name,email=email);

    # Add a user.
    db.execute("INSERT INTO users (first_name, last_name, email, password, date_created) VALUES (:first_name, :last_name, :email, :password, :date_created)",{"first_name": first_name, "last_name": last_name, "email": email, "password": password, "date_created": date_created})
    db.commit()
    return render_template("login.html", message="Account was successfully created. Please login.");

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/check_login", methods=["GET","POST"])
def check_login():
    # Get form information.
    email = request.form.get("email")
    password = request.form.get("password")

    # Make sure user exists
    if db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).rowcount == 0:
        return render_template("login.html", message="There is not account with that email address.");

    # get user & password
    user = db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchall()[0]
    user_password = user.password
    if check_password_hash(user_password, password):
        session.clear()
        session['user_id'] = user.user_id
        return redirect(url_for("search"))
    return render_template("login.html",message="Incorrect password. Try Again.")

@app.route("/search", methods=["GET","POST"])
def search():
  if "user_id" in session:
      table = False
      results = []
      if request.method == "POST":
          search = "%{}%".format(request.form.get("text"))
          type = request.form.get("search")
          if type == "title":
              results = db.execute("SELECT * FROM books WHERE title ILIKE :search", {"search": search}).fetchall()
          if type == "author":
              results = db.execute("SELECT * FROM books WHERE author ILIKE :search", {"search": search}).fetchall()
          if type == "isbn":
              results = db.execute("SELECT * FROM books WHERE isbn ILIKE :search", {"search": search}).fetchall()
          if type == None:
              results = db.execute("SELECT * FROM books WHERE title ILIKE :search OR author ILIKE :search OR isbn ILIKE :search", {"search": search}).fetchall()
          if len(results) > 0:
              table=True
          return render_template("search.html", results=results, table=table)
      return render_template("search.html", results=results, table=table)
  else:
      return redirect(url_for("login"))

@app.route("/logout")
def logout():
    session.clear();
    return redirect(url_for("index"))

@app.route("/book/<string:isbn>", methods=["GET","POST"])
def book(isbn):
    reviewed = True
    reviewsExist = False
    user_id = str(session['user_id'])
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": KEY, "isbns": isbn})
    if res.status_code != 200:
        raise Exception("ERROR: API request unsuccessful. Code: " + str(res.status_code))
    data = res.json()
    average = data["books"][0]["average_rating"]
    number_ratings = data["books"][0]["work_ratings_count"]
    if db.execute("SELECT * FROM reviews WHERE user_id = :user_id AND isbn = :isbn", {"user_id": user_id, "isbn": isbn}).rowcount == 0:
        reviewed = False
    if book is None:
        return render_template("search.html", message="Book not found: try again.")
    if request.method == "POST":
        review = request.form.get("text")
        rating = request.form.get("rating")
        db.execute("INSERT INTO reviews (isbn, rating, review, user_id) VALUES (:isbn, :rating, :review, :user_id)",
              {"isbn": book.isbn, "rating": rating, "review": review, "user_id": user_id})
        db.commit()
        reviewed = True
        reviews = db.execute("SELECT * FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchall()
    if len(reviews) > 0:
        reviewsExist=True
    return render_template("book.html", book = book, reviews = reviews, reviewed = reviewed, average = average, number_ratings = number_ratings, reviewsExist = reviewsExist)

@app.route("/api/<string:isbn>")
def book_api(isbn):
    """Return details about a single book."""
    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    count = db.execute("SELECT COUNT(rating) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    average = db.execute("SELECT AVG(rating) FROM reviews WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
      return jsonify ({"error": "Invalid isbn"}), 422

    return jsonify({
                "title": book.title,
                "author": book.author,
                "year": book.year,
                "isbn": book.isbn,
                "review_count": str(count[0]),
                "average_score": str(round(average[0],2))})
