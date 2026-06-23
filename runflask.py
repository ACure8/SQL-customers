from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

website = Flask(__name__, template_folder="templates", static_folder="static")
website.secret_key = "****"
DB_PATH = "wowfoods.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@website.route("/")
def home_page():
    '''home route'''
    connect = get_db()
    c = connect.cursor()
    products = c.execute("""SELECT p.product_id,
                                p.product_name,
                                p.price,
                                p.image_url,
                                c.category_name,
                                GROUP_CONCAT(t.tag_name, ', ') AS tags,
                                GROUP_CONCAT(t.description, ', ') AS tag_descriptions
                            FROM Products AS p
                                JOIN
                                Categories AS c ON p.category_id = c.category_id
                                LEFT JOIN
                                Product_Dietary_Tags AS pt ON p.product_id = pt.product_id
                                LEFT JOIN
                                Dietary_Tags AS t ON pt.tag_id = t.tag_id
                            GROUP BY p.product_id
                            ORDER BY p.product_id ASC
                            """).fetchall()
    popular = c.execute("""SELECT p.product_id,
                                p.product_name,
                                SUM(oi.quantity) AS total_units_sold,
                                SUM(oi.quantity * oi.price_at_purchase) AS total_revenue
                            FROM Products p
                                JOIN
                                Order_Items oi ON p.product_id = oi.product_id
                            GROUP BY p.product_id
                            ORDER BY total_units_sold DESC;
                            """).fetchall()
    connect.close()
    return render_template('Wowfoods.html', products=products, popular=popular)

@website.route("/menu")
def menu_page():
    connect = get_db()
    c = connect.cursor()
    categories = c.execute("""SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC;
                            """).fetchall()
    products = c.execute("""SELECT p.product_id,
                                p.product_name,
                                p.price,
                                p.image_url,
                                c.category_name,
                                GROUP_CONCAT(t.tag_name, ', ') AS tags,
                                GROUP_CONCAT(t.description, '; ') AS tag_descriptions
                            FROM Products AS p
                                JOIN
                                Categories AS c ON p.category_id = c.category_id
                                LEFT JOIN
                                Product_Dietary_Tags AS pt ON p.product_id = pt.product_id
                                LEFT JOIN
                                Dietary_Tags AS t ON pt.tag_id = t.tag_id
                            GROUP BY p.product_id
                            ORDER BY p.product_id ASC
                            """).fetchall()
    connect.close()
    return render_template("Menu.html", categories=categories, products=products)

@website.route("/cart")
def cart_page():
    connect = get_db()
    c = connect.cursor()
    categories = c.execute("""SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC;
                            """).fetchall()
    products = c.execute("""SELECT p.product_id,
                                p.product_name,
                                p.price,
                                p.image_url,
                                c.category_name,
                                GROUP_CONCAT(t.tag_name, ', ') AS tags,
                                GROUP_CONCAT(t.description, '; ') AS tag_descriptions
                            FROM Products AS p
                                JOIN
                                Categories AS c ON p.category_id = c.category_id
                                LEFT JOIN
                                Product_Dietary_Tags AS pt ON p.product_id = pt.product_id
                                LEFT JOIN
                                Dietary_Tags AS t ON pt.tag_id = t.tag_id
                            GROUP BY p.product_id
                            ORDER BY p.product_id ASC
                            """).fetchall()
    accounts = []
    if "user_id" in session:
        accounts = c.execute("""SELECT u.full_name,
                                    o.order_id,
                                    p.product_name,
                                    oi.quantity,
                                    oi.price_at_purchase,
                                    (oi.quantity * oi.price_at_purchase) AS line_total
                                FROM Users AS u
                                    JOIN
                                    Orders AS o ON u.user_id = o.user_id
                                    JOIN
                                    Order_Items AS oi ON o.order_id = oi.order_id
                                    JOIN
                                    Products AS p ON oi.product_id = p.product_id
                                WHERE u.user_id = ?
                                ORDER BY o.order_id ASC
                                    """, (session["user_id"],)).fetchall()
    connect.close()
    return render_template("Cart.html", categories=categories, products=products, accounts=accounts)

@website.route("/account")
def account_page():
    connect = get_db()
    c = connect.cursor()

    users = c.execute("""SELECT u.user_id,
                                    u.full_name,
                                    u.email,
                                    u.password_hash,
                                    u.phone,
                                    u.address,
                                    u.date_of_birth,
                                    u.wants_offers,
                                    u.created_at,
                                    pi.card_last_four,
                                    pi.card_type,
                                    pi.expiry_date
                                FROM Users AS u
                                    LEFT JOIN
                                    User_Payment_Info AS pi ON u.user_id = pi.user_id
                                ORDER BY u.user_id
                                """).fetchall()

    connect.close()
    return render_template("Accounts.html", users=users)


@website.route('/signin', methods=["GET", "POST"])
def signin_page():
    connect = get_db()
    c = connect.cursor()

    users = c.execute("""SELECT *
                        FROM Users AS u
                        ORDER BY u.user_id
                        """).fetchall()
    
    if request.method == "POST":
        if request.form.get("forgot_email"):
            forgot_email = request.form["forgot_email"].strip()
            connect.close()
            return f"Password reset instructions would be sent to {forgot_email} if this were enabled."

        if request.form.get("full_name") and request.form.get("confirm_password"):
            full_name = request.form["full_name"].strip()
            email = request.form["email"].strip().lower()
            password = request.form["password"]
            confirm_password = request.form["confirm_password"]
            date_of_birth = request.form.get("date_of_birth") # "get" returns True or False
            wants_offers = True if request.form.get("wants_offers") in ("on", "1", "true") else False

            if password != confirm_password:
                connect.close()
                return "Passwords do not match."

            existing_user = c.execute(
                "SELECT user_id FROM Users WHERE email = ?",
                (email,) # the "email," makes it a Tuple but if it was "email" then it sends as a str(may make an error)
            ).fetchone()

            if existing_user:
                connect.close()
                return "An account with that email already exists."

            password_hash = generate_password_hash(password)
            # compute next user_id (next integer after current max)
            max_id_row = c.execute("SELECT MAX(user_id) AS max_id FROM Users").fetchone()
            next_id = 1
            if max_id_row and max_id_row["max_id"] is not None:
                try:
                    next_id = int(max_id_row["max_id"]) + 1
                except Exception:
                    next_id = max_id_row["max_id"] + 1

            # Use the database CURRENT_TIMESTAMP to keep the default timestamp format
            c.execute(
                """INSERT INTO Users (user_id, full_name, email, password_hash, date_of_birth, wants_offers, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                (next_id, full_name, email, password_hash, date_of_birth, wants_offers)
            )
            connect.commit()
            connect.close()
            return redirect(url_for("show_user", username=full_name))

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = c.execute(
            "SELECT user_id, full_name, password_hash FROM Users WHERE email = ?",
            (email,)
        ).fetchone()

        if user and check_password_hash(user["password_hash"], password):
            # session["user_id"] = user["user_id"]
            # session["full_name"] = user["full_name"]
            # connect.close()
           return redirect(url_for("show_user", username=user["full_name"])) # redirect to a URL that contains the user's name to indicate signed-in state

        connect.close()
        return "Invalid email or password."


    connect.close()
    return render_template("Signin.html", users=users)

def _set_session_for_username(username):
    # try to resolve user_id from the database and set session
    conn = get_db()
    cur = conn.cursor()
    row = cur.execute("""SELECT user_id, full_name 
                        FROM Users 
                        WHERE full_name = ?
                        """, (username,)).fetchone()
    if row:
        session["user_id"] = row["user_id"]
        session["full_name"] = row["full_name"]
    else:
        return "that account doesn't exist so no sessions"
        # session["full_name"] = username
    conn.close()


@website.route('/<username>')
def show_user(username):
    _set_session_for_username(username)
    return redirect(url_for('home_page_user', username=username))


@website.route('/<username>')
def home_page_user(username):
    _set_session_for_username(username)
    return home_page()


@website.route('/menu/<username>')
def menu_page_user(username):
    _set_session_for_username(username)
    return menu_page()


@website.route('/cart/<username>')
def cart_page_user(username):
    _set_session_for_username(username)
    return cart_page()


@website.route('/account/<username>')
def account_page_user(username):
    _set_session_for_username(username)
    return account_page()


# # Error handling for page not found errors 
# @website.errorhandler(404)
# def page_not_found(error):
#     return render_template('error.html', error='Page not found'), 404

# # Error handling for 500 (Internal Server) error
# @website.errorhandler(500)
# def internal_server_error(error):
#     return render_template('error.html', error='Internal server error'), 500

# # Error handling for unexpected errors 
# @website.errorhandler(Exception)
# def unexpected_error(error):
#     return render_template('error.html', error='Something went wrong'), 500

if __name__ == "__main__":
   print("\n\033[1;95m- LOADING... -\033[0m\n")
   website.run(debug=True, port=5000)