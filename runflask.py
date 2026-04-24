from flask import Flask, render_template, send_from_directory

website = Flask(__name__, template_folder="templates")












@website.route("/")
def home_page():
    return render_template("Wowfoods.html")

@website.route("/menu")
def menu_page():
    return render_template("Menu.html")

@website.route("/cart")
def cart_page():
    return render_template("Cart.html")

@website.route("/account")
def signin_page():
    return render_template("Signin.html")

@website.route('/user/<username>')
def show_user(username):
    return f'Hello {username} ! please wait while we send you back'

if __name__ == "__main__":
    print("\n\033[1;95m- LOADING... -\033[0m\n")
    website.run(debug=True, port=5000)