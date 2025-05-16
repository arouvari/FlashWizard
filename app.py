import sqlite3
from flask import Flask, render_template, request, redirect, session
from werkzeug.security import generate_password_hash, check_password_hash
import db
import config

app = Flask(__name__)
app.secret_key = config.secret_key

@app.route("/")
def index():
    decks = db.query("SELECT id, name, description, tags, user_id FROM decks")
    return render_template("index.html", decks=decks)

@app.route("/register")
def register():
    return render_template("register.html")

@app.route("/new", methods=["POST"])
def new():
    username = request.form["username"]
    password1 = request.form["password1"]
    password2 = request.form["password2"]
    if password1 != password2:
        return "ERROR: Passwords don't match"
    password_hash = generate_password_hash(password1)

    try:
        sql = "INSERT INTO users (username, password_hash) VALUES (?, ?)"
        db.execute(sql, [username, password_hash])
    except sqlite3.IntegrityError:
        return "ERROR: Username is taken"
    return "Account created"

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    username = request.form["username"]
    password = request.form["password"]

    if not username or not password:
        return "ERROR: Username or password missing"

    user = db.query("SELECT id, username, password_hash FROM users WHERE username = ?", [username])
    if not user:
        return "ERROR: Wrong username or password"

    user_data = user[0]
    if check_password_hash(user_data["password_hash"], password):
        session["user_id"] = user_data["id"]
        session["username"] = user_data["username"]
        return redirect("/")
    else:
        return "ERROR: Wrong username or password"

@app.route("/logout")
def logout():
    del session["username"]
    return redirect("/")

@app.route("/create", methods=["GET", "POST"])
def create():
    return render_template("create.html")

@app.route("/deck/<int:deck_id>/add-cards", methods=["GET", "POST"])
def add_cards(deck_id):
    if request.method == "POST":
        num_cards = int(request.form["num_cards"])
        return render_template("add_cards.html", deck_id=deck_id, num_cards=num_cards)
    return render_template("num_cards.html", deck_id=deck_id)

@app.route("/deck/<int:deck_id>/create-cards", methods=["POST"])
def create_cards(deck_id):
    num_cards = int(request.form["num_cards"])
    for i in range(num_cards):
        question = request.form.get(f"question_{i}")
        answer = request.form.get(f"answer_{i}")
        if question and answer:
            db.execute("INSERT INTO flashcards (deck_id, question, answer) VALUES (?, ?, ?)", [deck_id, question, answer])
    return redirect("/")

@app.route("/send", methods=["POST"])
def send():
    if "user_id" not in session:
        return redirect("/login")

    name = request.form["name"]
    description = request.form["description"]
    tags = ",".join(request.form.getlist("tags"))
    user_id = session["user_id"]
    result = db.execute("INSERT INTO decks (name, description, tags, user_id) VALUES (?, ?, ?)", [name, description, tags, user_id])
    deck_id = result.lastrowid
    return redirect(f"/deck/{deck_id}/add-cards")

@app.route("/deck/<int:deck_id>/study")
def study_deck(deck_id):
    flashcards = db.query("SELECT id, question, answer FROM flashcards WHERE deck_id = ?", [deck_id])

    if "current_card" not in session:
        session["current_card"] = 0
        session["show_answer"] = False

    current_index = session["current_card"]
    total_cards = len(flashcards)

    if total_cards == 0:
        return "No flashcards in deck"

    current_index = max(0, min(current_index, total_cards-1))

    return render_template("study.html", deck_id=deck_id, card=flashcards[current_index], current_index=current_index+1, total_cards=total_cards, show_answer=session["show_answer"])

@app.route("/deck/<int:deck_id>/study/action", methods=["POST"])
def study_action(deck_id):
    action = request.form.get("action")

    if action == "next":
        session["current_card"] += 1
        session["show_answer"] = False
    elif action == "prev":
        session["current_card"] -= 1
        session["show_answer"] = False
    elif action == "flip":
        session["show_answer"] = not session["show_answer"]

    return redirect(f"/deck/{deck_id}/study")

@app.route("/deck/<int:deck_id>/edit", methods=["GET", "POST"])
def edit_deck(deck_id):
    if "user_id" not in session:
        return redirect("/login")

    deck = db.query("SELECT * FROM decks WHERE id = ?", [deck_id])
    if not deck or deck[0]["user_id"] != session["user_id"]:
        return "Unauthorized", 403

    if request.method == "GET":
        return render_template("edit_deck.html", deck=deck[0], deck_id=deck_id)

    name = request.form["name"]
    description = request.form["description"]
    tags = ",".join(request.form.getlist("tags"))
    db.execute("UPDATE decks SET name=?, description=?, tags=? WHERE id=?",
               [name, description, tags, deck_id])
    return redirect("/")

@app.route("/deck/<int:deck_id>/delete", methods=["POST"])
def delete_deck(deck_id):
    if "user_id" not in session:
        return redirect("/login")

    deck = db.query("SELECT user_id FROM decks WHERE id = ?", [deck_id])
    if not deck or deck[0]["user_id"] != session["user_id"]:
        return "Unauthorized", 403

    db.execute("DELETE FROM flashcards WHERE deck_id = ?", [deck_id])
    db.execute("DELETE FROM decks WHERE id = ?", [deck_id])
    return redirect("/")

@app.route("/deck/<int:deck_id>/manage")
def manage_cards(deck_id):
    flashcards = db.query("SELECT id, question, answer FROM flashcards WHERE deck_id = ?", [deck_id])
    return render_template("manage_cards.html", flashcards=flashcards, deck_id=deck_id)

@app.route("/flashcard/<int:card_id>/edit", methods=["POST"])
def edit_flashcard(card_id):
    question = request.form["question"]
    answer = request.form["answer"]
    db.execute("UPDATE flashcards SET question=?, answer=? WHERE id=?",
               [question, answer, card_id])
    deck_id = db.query("SELECT deck_id FROM flashcards WHERE id = ?", [card_id])[0]["deck_id"]
    return redirect(f"/deck/{deck_id}/manage")

@app.route("/flashcard/<int:card_id>/delete", methods=["POST"])
def delete_flashcard(card_id):
    deck_id = db.query("SELECT deck_id FROM flashcards WHERE id = ?", [card_id])[0]["deck_id"]
    db.execute("DELETE FROM flashcards WHERE id = ?", [card_id])
    return redirect(f"/deck/{deck_id}/manage")
