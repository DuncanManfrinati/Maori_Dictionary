import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error

app = Flask(__name__)
DATA_BASE = "C:/Users/18308/OneDrive - Wellington College/13DTS/Maori_Dictionary/identifier.sqlite"
app.secret_key = "duncan"


def create_connection(db_file):
    try:
        connection = sqlite3.connect(db_file)
        connection.execute('pragma foreign_keys=ON')
        return connection
    except Error as e:
        print(e)
    return None


@app.route('/', methods=['GET', 'POST'])
def home():
    # adding categories
    if request.method == "POST":
        category = request.form.get("category").strip().lower()
        con = create_connection(DATA_BASE)

        query = "INSERT INTO categories(categories) VALUES(?)"

        cur = con.cursor()
        cur.execute(query, (category, ))
        con.commit()
        con.close()

        return redirect("/login")
    return render_template("home.html", logged_in=is_logged_in(),categories=categories())



@app.route('/login', methods=['GET', 'POST'])
def login():
    #logging into the website
    if is_logged_in():
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        query = """SELECT id, firstname, password FROM users WHERE email = ?"""
        con = create_connection(DATA_BASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            user_id = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
        except IndexError:
            return redirect("/login?error=Email+Invalid+or+Password+Incorrect")
            print("Email Invalid or Password Incorrect")

        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = firstname
        print(session)

        if db_password != password:
            return redirect("/login?error=Email+Invalid+or+Password+Incorrect")
            return redirect("/")
        else:
            return redirect("/login?error=Incorrect+username+or+password")

    return render_template("login.html", logged_in=is_logged_in())


@app.route('/signup', methods=['POST', 'GET'])
#creating an account for the website
def signup():
    if request.method == 'POST':
        print(request.form)
        firstname = request.form.get('firstname').title().strip()
        lastname = request.form.get('lastname').title().strip()
        email = request.form.get('email')
        password = request.form.get('password')
        confirmpassword = request.form.get('confirmpassword')

        if password != confirmpassword:
            return redirect("/signup?error=Passwords+don't+match")
        if len(password) < 8:
            return redirect("/signup?error=Password+must+have+more+than+8+characters")
        if len(firstname) < 2:
            return redirect("/signup?error=Name+is+too+short")
        if len(lastname) < 1:
            return redirect("/signup?error=Lastname+must+be+longer")
        if len(email) < 6:
            return redirect("/signup?error=Email+is+not+valid")

        con = create_connection(DATA_BASE)

        query = "INSERT INTO users (firstname, lastname, email, password, ) VALUES(?, ?, ?, ?)"

        cur = con.cursor()
        cur.execute(query, (firstname, lastname, email, password,))
        con.commit()
        con.close()

        return redirect("/login")

    return render_template("signup.html", logged_in=is_logged_in())


@app.route('/logout')
def logout():
    print(list(session.keys()))
    [session.pop(key) for key in list(session.keys())]
    print(list(session.keys()))
    return redirect(request.referrer + "?message=See+you+next+time!")


def is_logged_in():
    if session.get("email") is None:
        print("Not Logged In")
        return False
    else:
        print("Logged In")
        return True


def categories():
    con = create_connection(DATA_BASE)
    query = "SELECT id,categories FROM categories"
    cur = con.cursor()
    cur.execute(query,)

    category_ids = cur.fetchall()
    print(category_ids)
    con.close()

    return category_ids

@app.route("/category/<category_id>")
def category(category_id):
    con = create_connection(DATA_BASE)
    query = "SELECT * FROM dictionary"
    cur = con.cursor()
    cur.execute(query, )

    cat = cur.fetchall()
    con.close()

    return render_template("categories.html", logged_in=is_logged_in(), category_ids=int(category_id), cat=cat)



if __name__ == '__main__':
    app.run()
