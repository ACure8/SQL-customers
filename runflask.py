from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

website = Flask(__name__, template_folder="templates", static_folder="static")
website.secret_key = "****"
DB_PATH = "wowfoodsnew.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@website.route("/signin")
def signin_page():
    return

@website.route("/")
def home_page():
    connect = get_db()
    c = connect.cursor()
    popular = c.execute("""
                        """).fetchall()
    connect.close()
    return render_template('Wowfoods.html', popular=popular)

@website.route("/menu")
def menu_page():
    return

@website.route("/cart")
def cart_page():
    return

@website.route("/cart")
def cart_page():
    return

if __name__ == "__main__":
   print("\n\033[1;95m- LOADING... -\033[0m\n")
   website.run(debug=True, port=5000)
