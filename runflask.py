from flask import Flask, render_template, send_from_directory

website = Flask(__name__, template_folder="templates")

@website.route("/")
def main_page():
    return render_template("Wowfood.html")

if __name__ == "__main__":
    print("\n\033[1;95m- LOADING... -\033[0m\n")
    website.run(debug=True, port=5000)