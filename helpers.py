import os
import smtplib
from flask import redirect, render_template, request, session
from functools import wraps
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


def connectdb():
    """Connects to a db"""
    # Check for environment variable
    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is not set")
    # Set up database
    engine = create_engine(os.getenv('DATABASE_URL'))
    db = scoped_session(sessionmaker(bind=engine))
    return db


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def send_email(receiver, name, subject, message):
    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(os.getenv("email"), os.getenv("password"))
    server.sendmail(os.getenv("email"), receiver, f"To: {receiver}\nSubject: {subject}\nHello {name},\n {message}")
