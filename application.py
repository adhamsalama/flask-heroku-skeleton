from flask import Flask, Blueprint
from flask_session import Session

app = Flask(__name__)


# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"


Session(app)


from auth.routes import auth
from settings.routes import settings
from main.routes import main

app.register_blueprint(auth)
app.register_blueprint(settings)
app.register_blueprint(main)
