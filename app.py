from flask import Flask, render_template, request, redirect
import db

app = Flask(__name__)

@app.route("/")
def index():
    decks = db.query("SELECT name, description, tags FROM decks")
    return render_template("index.html", decks=decks)

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
    name = request.form["name"]
    description = request.form["description"]
    tags = ",".join(request.form.getlist("tags"))
    result = db.execute("INSERT INTO decks (name, description, tags) VALUES (?, ?, ?)", [name, description, tags])
    deck_id = result.lastrowid
    return redirect(f"/deck/{deck_id}/add-cards")
