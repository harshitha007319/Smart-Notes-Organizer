from flask import Flask, render_template, request, redirect, jsonify
import sqlite3
import re

app = Flask(__name__)

DATABASE = "notes.db"


def get_db():
    return sqlite3.connect(DATABASE)


def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'Study',
            important INTEGER DEFAULT 0,
            priority TEXT DEFAULT 'Medium'
        )
    """)

    columns = [
        row[1]
        for row in conn.execute("PRAGMA table_info(notes)").fetchall()
    ]

    if "category" not in columns:
        conn.execute(
            "ALTER TABLE notes ADD COLUMN category TEXT DEFAULT 'Study'"
        )

    if "important" not in columns:
        conn.execute(
            "ALTER TABLE notes ADD COLUMN important INTEGER DEFAULT 0"
        )

    if "priority" not in columns:
        conn.execute(
            "ALTER TABLE notes ADD COLUMN priority TEXT DEFAULT 'Medium'"
        )

    conn.commit()
    conn.close()


# HOME
@app.route("/")
def home():
    conn = get_db()

    notes = conn.execute("""
        SELECT id, title, content, category, important, priority
        FROM notes
        ORDER BY id DESC
    """).fetchall()

    conn.close()

    return render_template("index.html", notes=notes)


# ADD NOTE
@app.route("/add", methods=["POST"])
def add():
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "Study")
    priority = request.form.get("priority", "Medium")

    if title and content:
        conn = get_db()

        conn.execute("""
            INSERT INTO notes
            (title, content, category, important, priority)
            VALUES (?, ?, ?, 0, ?)
        """, (title, content, category, priority))

        conn.commit()
        conn.close()

    return redirect("/")


# DELETE NOTE
@app.route("/delete/<int:id>")
def delete(id):
    conn = get_db()

    conn.execute(
        "DELETE FROM notes WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect("/")


# EDIT PAGE
@app.route("/edit/<int:id>", methods=["GET"])
def edit(id):
    conn = get_db()

    note = conn.execute("""
        SELECT id, title, content, category, important, priority
        FROM notes
        WHERE id = ?
    """, (id,)).fetchone()

    conn.close()

    if note is None:
        return "Note not found", 404

    return render_template("edit.html", note=note)


# UPDATE NOTE
@app.route("/update/<int:id>", methods=["POST"])
def update(id):
    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    category = request.form.get("category", "Study")
    priority = request.form.get("priority", "Medium")

    if title and content:
        conn = get_db()

        conn.execute("""
            UPDATE notes
            SET title = ?, content = ?, category = ?, priority = ?
            WHERE id = ?
        """, (title, content, category, priority, id))

        conn.commit()
        conn.close()

    return redirect("/")


# IMPORTANT NOTE
@app.route("/important/<int:id>")
def important(id):
    conn = get_db()

    conn.execute("""
        UPDATE notes
        SET important = CASE
            WHEN important = 0 THEN 1
            ELSE 0
        END
        WHERE id = ?
    """, (id,))

    conn.commit()
    conn.close()

    return redirect("/")


# AI SUMMARIZE
@app.route("/ai-summarize", methods=["POST"])
def ai_summarize():

    data = request.get_json()

    if not data:
        return jsonify({
            "success": False,
            "message": "Please select a note."
        })

    content = data.get("content", "").strip()

    if not content:
        return jsonify({
            "success": False,
            "message": "Please select a note first."
        })

    try:
        sentences = re.split(r'(?<=[.!?])\s+', content)

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if len(sentences) <= 3:
            summary = " ".join(sentences)

        else:
            important_words = [
                "important",
                "main",
                "key",
                "definition",
                "because",
                "used",
                "helps",
                "provides",
                "advantages",
                "benefits",
                "process",
                "system"
            ]

            scored = []

            for sentence in sentences:
                score = 0

                for word in important_words:
                    if word in sentence.lower():
                        score += 1

                if len(sentence.split()) >= 8:
                    score += 1

                scored.append((score, sentence))

            scored.sort(reverse=True)

            selected = [
                sentence
                for score, sentence in scored[:3]
            ]

            summary = " ".join(selected)

        return jsonify({
            "success": True,
            "summary": summary
        })

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Summarization failed: " + str(e)
        })


if __name__ == "__main__":
    create_database()
    app.run(debug=True)