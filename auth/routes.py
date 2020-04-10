from flask import Blueprint, session, request, redirect, render_template, flash, jsonify
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from helpers import apology, login_required, connectdb

auth = Blueprint('auth', __name__)

db = connectdb()


@auth.route("/login", methods=["GET", "POST"])
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
        session["username"] = rows["username"]
        session["email"] = rows["email"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@login_required
@auth.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@auth.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""


    if request.method == "GET":
        session.clear()
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
        db.execute("""INSERT INTO users(username, hash, email, registeration) VALUES(:username, :hash_pw, :email, :time)""",
                   {"username": username, "hash_pw": hash_pw, "email": email, "time": time})
        db.commit()
    except:
        return apology("something went wrong with the database")
        
    rows = db.execute("SELECT id, username, email FROM users WHERE username = :username",
                      {"username": username}).fetchone()
    session["user_id"] = rows["id"]
    session["username"] = rows["username"]
    session["email"] = rows["email"]
    flash("You're now registered!")
    return redirect("/")

@auth.route("/check", methods=["GET"])
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


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    auth.errorhandler(code)(errorhandler)
