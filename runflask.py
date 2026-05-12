#from flask import Flask, render_template
# Import the libraries to connect to the database and present the information in tables
import sqlite3
from tabulate import tabulate

#website = Flask(__name__, template_folder="templates")


# This is the filename of the database to be used
DB_NAME = 'wowfoods.db'

def print_query(view_name:str):
    ''' Prints the specified view from the database in a table '''
    # Set up the connection to the database
    db = sqlite3.connect(DB_NAME)
    cursor = db.cursor()
    # Get the results from the view
    sql = "SELECT * FROM '" + view_name + "'"
    cursor.execute(sql)
    results = cursor.fetchall()
    # Get the field names to use as headings
    field_names = "SELECT name from pragma_table_info('" + view_name + "') AS tblInfo"
    cursor.execute(field_names)
    headings = list(sum(cursor.fetchall(),()))
    # Print the results in a table with the headings
    print(tabulate(results,headings))
    db.close()

menu_choice =''
print("\nWelcome to the wowfoods database\n\n") 
while menu_choice != 'Z':
    menu_choice = input(
                        "Type the letter for the query that you would like to see.:\n\n" 
                        "A: All categories\n"
                        "B: All login session (sign-in asc)\n"
                        "C: All login session (sign-out asc)\n"
                        "D: All products with tags\n"
                        "E: All products with tags in one line\n"
                        "F: All user login sessions\n"
                        "G: All user order info\n"
                        "H: All user order status\n"
                        "Z: Exit\n\nType option here: ")
    print('\n')
    menu_choice = menu_choice.upper()
    if menu_choice == 'A':
        print_query('All categories')
    elif menu_choice == 'B':
        print_query('All login session (sign-in asc)')
    elif menu_choice == 'C':
        print_query('All login session (sign-out asc)')
    elif menu_choice == 'D':
        print_query('All products with tags')
    elif menu_choice == 'E':
        print_query('All products with tags in one line')
    elif menu_choice == 'F':
        print_query('All user login sessions')
    elif menu_choice == 'G':
        print_query('All user order info')
    elif menu_choice == 'H':
        print_query('All user order status')
    elif menu_choice != 'A'or'B'or'C'or'D'or'E'or'F'or'G'or'H'or'Z':
        print("This option is not available\n"
              "Please try a different option")


#@website.route("/")
#def home_page():
#    return render_template("Wowfoods.html")
#
#@website.route("/menu")
#def menu_page():
#    return render_template("Menu.html")
#
#@website.route("/cart")
#def cart_page():
#    return render_template("Cart.html")
#
#@website.route("/account")
#def signin_page():
#    return render_template("Signin.html")
#
#@website.route('/user/<username>')
#def show_user(username):
#    return f'Hello {username} ! please wait while we send you back'
#
#if __name__ == "__main__":
#    print("\n\033[1;95m- LOADING... -\033[0m\n")
#    website.run(debug=True, port=5000)