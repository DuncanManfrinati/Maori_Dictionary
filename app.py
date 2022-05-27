import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from flask import Flask, render_template, request, redirect, session
import sqlite3
from sqlite3 import Error
from flask_bcrypt import Bcrypt

app = Flask(__name__)
bcrypt = Bcrypt(app)
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
        cur.execute(query, (category,))
        con.commit()
        con.close()

        return redirect("/login")
    return render_template("home.html", logged_in=is_logged_in(), categories=categories())


@app.route('/login', methods=['GET', 'POST'])
def login():
    # logging into the website
    if is_logged_in():
        return redirect("/")

    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"].strip()

        query = """SELECT id, firstname, password, teacher FROM users WHERE email = ?"""
        con = create_connection(DATA_BASE)
        cur = con.cursor()
        cur.execute(query, (email,))
        user_data = cur.fetchall()
        con.close()

        try:
            user_id = user_data[0][0]
            firstname = user_data[0][1]
            db_password = user_data[0][2]
            teacher = user_data[0][3]
        except IndexError:
            return redirect("/login?error=Email+Invalid+or+Password+Incorrect")
            print("Email Invalid or Password Incorrect")

        session["email"] = email
        session["user_id"] = user_id
        session["first_name"] = firstname
        session["teacher"] = teacher
        print(session)

        if db_password != password:
            return redirect("/login?error=Email+Invalid+or+Password+Incorrect")
            return redirect("/")
        else:
            return redirect("/login?error=Incorrect+username+or+password")

    return render_template("login.html", logged_in=is_logged_in())


@app.route('/signup', methods=['POST', 'GET'])
# This link take the user to a form
def signup():
    if request.method == 'POST':
        print(request.form)
        firstname = request.form.get('firstname').title().strip()
        lastname = request.form.get('lastname').title().strip()
        email = request.form.get('email')
        password = request.form.get('password')
        confirmpassword = request.form.get('confirmpassword')
        teacher = request.form.get('role')

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

        hashed_password = bcrypt.generate_password_hash(password)

        con = create_connection(DATA_BASE)

        query = "INSERT INTO users (id, firstname, lastname, email, password, teacher) VALUES(NULL,?, ?, ?, ?, ?)"

        cur = con.cursor()
        try:
            cur.execute(query, (firstname, lastname, email, hashed_password, teacher))
        except sqlite3.IntegrityError:
            return redirect("/signup?error=Email+is+already+being+used")
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


def is_teacher():
    teacher = False
    if session.get("teacher") is None:
        teacher = False
    elif session.get("teacher"):
        teacher = True
    return teacher


def categories():
    con = create_connection(DATA_BASE)
    query = "SELECT id,categories FROM categories"
    cur = con.cursor()
    cur.execute(query, )

    category_ids = cur.fetchall()
    con.close()

    return category_ids


# This link takes the words from the dictionary table and presents them for the user, the word present match with the
# word's category
@app.route("/category/<category_id>", methods=['POST', 'GET'])
def category(category_id):
    # This if statement allows the teacher to insert new words into the category that they are currently in by
    # inserting the words information like, maori name, english name, english definition and the word's level.
    if request.method == 'POST':
        maori = request.form.get('maori')
        english = request.form.get('english')
        definition = request.form.get('definition')
        level = request.form.get('level')
        image = "noimage.png"
        time = datetime.now()

        con = create_connection(DATA_BASE)
        print(category_id)
        query = "INSERT INTO dictionary (id, maori, english, category_id, definition, level, image, time ) VALUES(null , ?, ?, ?, ?, ?, ?, ?)"

        cur = con.cursor()
        cur.execute(query, (maori, english, category_id, definition, level, image, time,))
        con.commit()
        con.close()

    con = create_connection(DATA_BASE)
    query = "SELECT id, maori, english, image FROM dictionary WHERE category_id=?;"
    cur = con.cursor()
    cur.execute(query, (category_id,))
    cat = cur.fetchall()
    con.close()

    return render_template("categories.html", is_teacher=is_teacher(), logged_in=is_logged_in(),
                           category_ids=int(category_id), cat=cat,
                           categories=categories())


# This link is the word link which when pressed present the word's information
@app.route("/word/<id>", methods=['POST', 'GET'])
def dictionary(id):
    if request.method == 'POST':
        # This if statement connects to the form in "word.html" that allow the teacher to edit the word by
        # changing/update the word's information through a form at the bottom of the page.
        edit_maori = request.form.get('editmaori')
        edit_english = request.form.get('editenglish')
        edit_level = request.form.get('editlevel')
        new_time = datetime.now()

        con = create_connection(DATA_BASE)
        print(id)
        query = "UPDATE dictionary SET maori = ?, english = ?, level = ?, time = ? WHERE id=? ;"

        cur = con.cursor()
        cur.execute(query, (edit_maori, edit_english, edit_level, new_time, id))
        con.commit()
        con.close()

    id = int(id)
    con = create_connection(DATA_BASE)
    query = "SELECT id, maori, english, image, level, time, user_id FROM dictionary WHERE id=?;"
    cur = con.cursor()
    cur.execute(query, (id,))
    word = cur.fetchall()
    con.close()

    return render_template("word.html", is_teacher=is_teacher(), logged_in=is_logged_in(), word=word, id=id,
                           categories=categories())


# This link is located above the word and allow the teacher to delete the word
@app.route("/word/delete_yes/<id>", methods=['POST', 'GET'])
def yes_word_delete(id):
    con = create_connection(DATA_BASE)
    query = "DELETE FROM dictionary WHERE id = ?"
    cur = con.cursor()
    cur.execute(query, (id,))
    con.commit()
    print()
    con.close()

    return render_template("home.html", is_teacher=is_teacher(), logged_in=is_logged_in(), categories=categories(),
                           id=id)


# This link is located above the word which when clicked does nothing to delete the word
@app.route("/word/delete_no", methods=['POST', 'GET'])
def no_word_delete():
    return render_template("home.html", is_teacher=is_teacher(), logged_in=is_logged_in(),
                           categories=categories())


if __name__ == '__main__':
    app.run()
