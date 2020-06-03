import os

from flask import Flask, render_template, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_session import Session
from flask_migrate import Migrate
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime

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
        return render_template("search.html",first_name=user.first_name)

    #check password
    #if not bcrypt.check_password_hash(user_password_hash, password):
        #return render_template("login.html",message="Incorrect password.",email=email);
    #user_id = db.execute ("SELECT user_id FROM users WHERE email = :email", {"email": email}).fetchone()
    #session["user_id"] = user_id
    #return redirect(url_for("search"))

@app.route("/search")
def search():
  if "user_id" in session:
      return render_template("search.html")
  else:
      return redirect(url_for("login"))
