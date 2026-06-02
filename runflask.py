from flask import Flask, render_template
import sqlite3

website = Flask(__name__, template_folder="templates", static_folder="static")
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
    connect.close()
    return render_template("Cart.html", categories=categories, products=products)

@website.route("/account")
def signin_page():
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
    accounts = c.execute("""SELECT u.user_id,
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
    return render_template("Signin.html", users=users, accounts=accounts)

@website.route('/user/<username>')
def show_user(username):
   return f'Hello {username} ! please wait while we send you back'


# Error handling for page not found errors 
@website.errorhandler(404)
def page_not_found(error):
    return render_template('error.html', error='Page not found'), 404

# Error handling for 500 (Internal Server) error
@website.errorhandler(500)
def internal_server_error(error):
    return render_template('error.html', error='Internal server error'), 500

# Error handling for unexpected errors 
# @website.errorhandler(Exception)
# def unexpected_error(error):
# return render_template('error.html', error='Something went wrong'), 500

if __name__ == "__main__":
   print("\n\033[1;95m- LOADING... -\033[0m\n")
   website.run(debug=True, port=5000)
