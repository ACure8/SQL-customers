from flask import Flask, render_template
import sqlite3

website = Flask(__name__, template_folder="templates")

@website.route("/")
def home_page():
    '''home route'''
    connect = sqlite3.connect("wowfoods.db")
    c = connect.cursor()
    categories = c.execute("""SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC;
                            """).fetchall()
    connect.close()
    return render_template('Wowfoods.html', categories=categories)

@website.route("/menu")
def menu_page():
    connect = sqlite3.connect("wowfoods.db")
    c = connect.cursor()
    categories = c.execute("""SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC;
                            """).fetchall()
    connect.close()
    return render_template("Menu.html", categories=categories)

@website.route("/cart")
def cart_page():
    connect = sqlite3.connect("wowfoods.db")
    c = connect.cursor()
    categories = c.execute("""SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC;
                            """).fetchall()
    connect.close()
    return render_template("Cart.html", categories=categories)

@website.route("/account")
def signin_page():
    connect = sqlite3.connect("wowfoods.db")
    c = connect.cursor()
    categories = c.execute("""SELECT *
                            FROM Categories 
                            ORDER BY category_id ASC;
                            """).fetchall()
    connect.close()
    return render_template("Signin.html", categories=categories)

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
