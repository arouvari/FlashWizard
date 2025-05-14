from flask import Flask
from flask import render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/")
def index():
    db = sqlite3.connect("database.db")
    decks = db.execute("SELECT name, description FROM decks").fetchall
    db.close()
    return render_template("index.html", decks=decks)

@app.route("/create")
def create():
    return render_template("create.html")

@app.route("/decks", methods=["POST"])
def decks():
    name = request.form["name"]
    description = request.form["description"]
    tags = request.form.getlist("tags")
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO decks (name, description) VALUES (?)", [name], [description])
    return render_template("decks.html", name=name, description=description, tags=tags)
