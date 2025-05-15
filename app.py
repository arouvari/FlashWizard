from flask import Flask
from flask import render_template, request
import sqlite3

app = Flask(__name__)

@app.route("/", methods=["POST"])
def index():
    name = request.form["name"]
    description = request.form["description"]
    tags = request.form.getlist("tags[]")
    db = sqlite3.connect("database.db")
    db.execute("INSERT INTO decks (name, description) VALUES (?, ?)", (name, description))
    db.commit()
    db.close()
    return render_template("index.html", name=name, description=description, tags=tags)

@app.route("/create")
def create():
    return render_template("create.html")
