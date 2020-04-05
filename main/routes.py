import os
from flask import flash, redirect, render_template, request, session, Blueprint
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from helpers import apology, login_required

main = Blueprint('main', __name__)


# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")


# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# Ensure responses aren't cached
@main.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@main.route("/")
@login_required
def index():
    """Display index page"""

    return render_template("index.html")


@main.route("/search", methods=["GET"])
@login_required
def search():
    """Search for something (Optional)"""
    
    results = ''
    return render_template("results.html", results=results)


@main.route("/profile")
@login_required
def profile():
    """Display user profile"""

    # Username and email are already stored in the session, registeration time isn't, you can query for registeration time only instead
    # Values in profile.html are from this query but you can use the values in the session instead
    info = db.execute('SELECT * FROM users WHERE id = :id', {'id': session['user_id']}).fetchone()
    return render_template("profile.html", info=info)


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    main.errorhandler(code)(errorhandler)
