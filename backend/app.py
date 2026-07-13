import pathlib
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# the whole database is this one file, sitting next to app.py
DB_PATH = pathlib.Path(__file__).parent / "demo.db"


def get_db():
    """
    Open a fresh connection to the database file.

    sqlite3.Row makes query results readable by column name
    (row["name"]) instead of only by position (row[1]).
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Runs once at startup: create the table on the very first run.
# "IF NOT EXISTS" makes every later startup a harmless no-op.
with get_db() as db:
    db.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT)")


@app.route("/test/<string:name>/<int:age>", methods=["GET"])
def test(name, age):
    name = "hi, my name is" + name
    age = age + 5

    return render_template("index.html", the_name=name, the_age=age)


@app.route("/users", methods=["GET"])
def list_users():
    with get_db() as db:
        rows = db.execute("SELECT id, name FROM users ORDER BY id").fetchall()

    return jsonify([dict(row) for row in rows])


@app.route("/users", methods=["POST"])
def add_user():
    # the ? placeholders let sqlite insert the values safely -- never build
    # SQL by gluing strings together (that is how injection attacks happen)
    with get_db() as db:
        db.execute(
            "INSERT OR REPLACE INTO users (id, name) VALUES (?, ?)",
            (request.form["id"], request.form["name"]),
        )

    return jsonify(saved=request.form["id"]), 201


if __name__ == "__main__":
    app.run(port=5000, debug=True)
