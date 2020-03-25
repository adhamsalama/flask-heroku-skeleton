import os
from flask import Flask, flash, json, jsonify, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from helpers import apology, login_required, send_email


app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@login_required
def index():
    """Display index page"""

    return render_template("index.html")

@app.route("/search", methods=["GET"])
@login_required
def search():
    """Search for something (Optional)"""
    
    results = ''
    return render_template("results.html", results=results)


@app.route("/profile")
@login_required
def profile():
    """Display user profile"""

    return render_template("profile.html", )


@app.route("/feedback", methods=["GET", "POST"])
def feedback():
    """Get user feedback"""

    if request.method == "GET":
        return render_template("feedback.html")
    else:
        feedback_type = request.form.get("type")
        email = request.form.get("email")
        feedback = request.form.get("feedback")
        if not (feedback_type or email or feedback):
            return apology("please fill the form")
        db.execute("INSERT INTO user_feedback (id, email, feedback, type) VALUES(:id, :email, :feedback, :type)", {"id": session["user_id"], "email": email, "feedback": feedback, "type": feedback_type})
        db.commit()
        flash("Feedback submitted! Thanks for your feedback!")
        return redirect("/")


@app.route("/check", methods=["GET"])
def check():
    """Check if username or email is taken"""

    email = request.args.get("email")
    username = request.args.get("username")
    email = request.args.get("email")
    verify_username = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchone()
    if email:
        verify_email = db.execute("SELECT email FROM users WHERE email = :email", {"email": email}).fetchone()
        if verify_email and verify_username:
            return jsonify("Username and email already taken.")
        if verify_username:
            return jsonify("Username already taken.")
        if verify_email:
            return jsonify("Email already taken.")
    if verify_username:
        return jsonify("Username already taken.")
    return jsonify(True)

@app.route("/settings/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "GET":
        return render_template("change_password.html")
    else:
        password = request.form.get("password")
        new_password = request.form.get("new_password")
        confirmation = request.form.get("confirmation")
        pw_hash = db.execute("SELECT hash FROM users WHERE id = :id", {"id": session["user_id"]}).fetchone()["hash"]
        if not password or not new_password or new_password != confirmation:
            return apology("please fill the form correctly")
        elif password == new_password:
            return apology("new and old password can't be the same")
        elif not check_password_hash(pw_hash, password):
            return apology("incorrect password")
        else:
            # Specifications for password
            # password length
            if len(new_password) < 6:
                return apology("password must be longer than 6 characters")
            capital = None
            lower = None
            for c in new_password:
                if c.isupper():
                    capital = True
                if c.islower():
                    lower = True
            if not capital and not lower:
                return apology("password must contain atleast 1 uppercase and lowercase letter")
            # password must contain numbers
            if new_password.isalpha():
                return apology("password must contain numbers")
            # password must contain letters
            if new_password.isdigit():
                return apology("password must contain letters")
            db.execute("UPDATE users SET hash = :new_password WHERE id = :id",
                           {"new_password":generate_password_hash(new_password), "id": session["user_id"]})
            db.commit()
            flash("Password updated!")
            return redirect("/")

@app.route("/settings/change_email", methods=["GET", "POST"])
@login_required
def change_email():
    if request.method == "GET":
        return render_template("change_email.html")
    else:
        email = request.form.get("email")
        new_email = request.form.get("new_email")
        if not email or not new_email:
            return apology("please fill the form")
        emails = db.execute("SELECT email FROM users WHERE email = :email", {"email": new_email}).fetchone()
        if email != session["email"]:
            return apology("wrong email")
        if emails:
            return apology("email already taken")
        else:
            db.execute("UPDATE users SET email = :new_email WHERE id = :id",
                           {"new_email": new_email, "id": session["user_id"]})
            db.commit()
            session["email"] = new_email
            flash("Email updated!")
            return redirect("/")

@app.route("/settings/add_email", methods=["GET", "POST"])
@login_required
def add_email():
    if request.method == "GET":
        return render_template("add_email.html")
    else:
        email = request.form.get("email")
        if not email:
            return apology("please enter an email")
        q = db.execute("SELECT email FROM users WHERE email = :email", {"email": email}).fetchone()
        if q:
            return apology("this email already exists")
        db.execute("UPDATE users SET email = :new_email WHERE id = :id",
                       {"new_email": email, "id": session["user_id"]})
        db.commit()
        session["email"] = email
        flash("Email added!")
        return redirect("/")

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = :username",
                          {"username": request.form.get("username")}).fetchone()

        # Ensure username exists and password is correct
        if not rows or not check_password_hash(rows["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows["id"]
        session["username"] =  rows["username"]
        session["email"] = rows["email"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")

@login_required
@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""
    if request.method == "GET":
        return render_template("register.html")
    else:
        username = request.form.get("username")
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        if not (username or password or confirmation or email) or password != confirmation:
            return apology("please fill the form correctly to register.")
    # Checking for username
    c = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchall()
    if c:
        return apology("username already taken")

    # Specifications for password

    # password length
    if len(password) < 6:
        return apology("password must be longer than 6 characters")
    # password must contain numbers
    if password.isalpha():
        return apology("password must contain numbers")
    # password must contain letters
    if password.isdigit():
        return apology("password must contain letters")

    for c in username:
        if not c.isalpha() and not c.isdigit() and c != "_":
            return apology("Please enter a valid username.")
    if len(username) < 1:
        return apology("please enter a username with more than 1 character.")
    hash_pw = generate_password_hash(password)
    from datetime import date
    time = date.today()
    try:
        q = db.execute("SELECT email FROM users WHERE email = :email", {"email": email}).fetchone()
        if q:
            return apology("this email already exists")
        db.execute("INSERT INTO users(username, hash, email, time) VALUES(:username, :hash_pw, :email, :time)", {"username": username, "hash_pw": hash_pw, "email": email, "time": time})
        db.commit()
    except:
        return apology("something went wrong with the database.")
    rows = db.execute("SELECT id, username, email FROM users WHERE username = :username", {"username": username}).fetchone()
    session["user_id"] = rows["id"]
    session["username"] = rows["username"]
    session["email"] = rows["email"]
    flash("You're now registered!")
    return redirect("/")

def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)

# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
