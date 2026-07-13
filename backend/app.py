import hashlib
import pathlib
import sqlite3

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# the whole database is this one file, sitting next to app.py
DB_PATH = pathlib.Path(__file__).parent / "demo.db"

# received files are stored here: uploads/<user_id>/<category>/<filename>
UPLOAD_ROOT = pathlib.Path(__file__).parent / "uploads"

# DEMO: known users, seeded into the database on first start. The real
# deployment would manage these through the hospital's own registration.
DEMO_USERS = [
    ("1123501", "王小明"),
    ("1123502", "陳美麗"),
    ("1123503", "林大文"),
]


def get_db():
    """
    Open a fresh connection to the database file.

    sqlite3.Row makes query results readable by column name
    (row["name"]) instead of only by position (row[1]).
    """
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


# Runs once at startup: create the tables on the very first run and make
# sure the demo users exist. "IF NOT EXISTS" / "OR IGNORE" make every
# later startup a harmless no-op.
with get_db() as db:
    db.execute("CREATE TABLE IF NOT EXISTS users (id TEXT PRIMARY KEY, name TEXT)")
    db.execute(
        """
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL,
            filename TEXT NOT NULL,
            hash TEXT NOT NULL,
            size INTEGER NOT NULL,
            uploaded_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    db.executemany("INSERT OR IGNORE INTO users (id, name) VALUES (?, ?)", DEMO_USERS)


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


@app.route("/upload", methods=["POST"])
def upload():
    """
    Receive one file plus its metadata from the desktop app.

    The folder structure carried the metadata on the client's disk; over
    HTTP it must travel explicitly, so the form brings user_id, category
    and the client-side SHA-256. The hash is recomputed here on the bytes
    that actually arrived -- a match proves the transfer was intact.
    """
    user_id = request.form["user_id"]
    category = request.form["category"]
    sent_hash = request.form["hash"]
    sent_file = request.files["file"]

    with get_db() as db:
        known = db.execute("SELECT 1 FROM users WHERE id = ?", (user_id,)).fetchone()
    if known is None:
        return jsonify(error=f"user '{user_id}' is not registered"), 404

    content = sent_file.read()
    received_hash = hashlib.sha256(content).hexdigest()
    if received_hash != sent_hash:
        return jsonify(error="hash mismatch, file was corrupted in transit"), 400

    # keep only the bare filename: a client could smuggle path parts in it
    # (or send no name at all -- werkzeug allows a nameless file part)
    filename = pathlib.PurePath(sent_file.filename or "unnamed").name

    folder = UPLOAD_ROOT / user_id / category
    folder.mkdir(parents=True, exist_ok=True)

    # same free-name trick as the client uses: report.pdf -> report_1.pdf
    destination = folder / filename
    counter = 1
    while destination.exists():
        destination = folder / f"{destination.stem.rstrip('_0123456789')}_{counter}{destination.suffix}"
        counter += 1

    destination.write_bytes(content)

    with get_db() as db:
        db.execute(
            "INSERT INTO files (user_id, category, filename, hash, size) VALUES (?, ?, ?, ?, ?)",
            (user_id, category, destination.name, received_hash, len(content)),
        )

    return jsonify(saved=destination.name, size=len(content)), 201


if __name__ == "__main__":
    app.run(port=5000, debug=True)
