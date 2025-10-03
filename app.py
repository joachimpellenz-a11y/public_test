from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Iterable

from flask import Flask, Response, abort, redirect, render_template, request, url_for

app = Flask(__name__)
DATABASE = Path(app.root_path) / "blog.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    DATABASE.parent.mkdir(parents=True, exist_ok=True)
    with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE
            )
            """
        )

        cursor.execute("SELECT COUNT(*) FROM posts")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO posts (title, body) VALUES (?, ?)",
                (
                    "Willkommen in deinem Blog",
                    "Dieser Beispielartikel zeigt, wie du Beiträge und Kommentare mit Flask und HTMX verwaltest.",
                ),
            )



# Ensure the database schema exists when the module is imported. This mirrors
# the previous before_first_request hook but remains compatible with newer
# Flask versions where the hook has been removed.
init_db()



@app.route("/", methods=["GET", "POST"])
def index() -> str:
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if not title or not body:
            abort(400, "Titel und Inhalt werden benötigt.")
        with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
            cursor.execute("INSERT INTO posts (title, body) VALUES (?, ?)", (title, body))
        return redirect(url_for("index"))

    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT id, title, body, created_at, (SELECT COUNT(*) FROM comments WHERE post_id = posts.id) AS comment_count FROM posts ORDER BY created_at DESC"
        )
        posts = cursor.fetchall()
    return render_template("index.html", posts=posts)


@app.route("/posts/<int:post_id>")
def post_detail(post_id: int) -> str:
    with closing(get_connection()) as conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT id, title, body, created_at FROM posts WHERE id = ?", (post_id,))
        post = cursor.fetchone()
        if post is None:
            abort(404)
        comments = get_comments_for_post(cursor, post_id)
    return render_template("post_detail.html", post=post, comments=comments)


def get_comments_for_post(cursor: sqlite3.Cursor, post_id: int) -> Iterable[sqlite3.Row]:
    cursor.execute(
        "SELECT id, author, content, created_at FROM comments WHERE post_id = ? ORDER BY created_at DESC",
        (post_id,),
    )
    return cursor.fetchall()


@app.route("/posts/<int:post_id>/comments", methods=["POST"])
def create_comment(post_id: int) -> str:
    author = request.form.get("author", "Anonymous").strip() or "Anonymous"
    content = request.form.get("content", "").strip()
    if not content:
        abort(400, "Kommentarinhalte dürfen nicht leer sein.")

    with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
        cursor.execute("SELECT 1 FROM posts WHERE id = ?", (post_id,))
        if cursor.fetchone() is None:
            abort(404)
        cursor.execute(
            "INSERT INTO comments (post_id, author, content) VALUES (?, ?, ?)",
            (post_id, author, content),
        )
        comments = get_comments_for_post(cursor, post_id)

    return render_template("partials/comment_list.html", comments=comments, post_id=post_id)


@app.route("/comments/<int:comment_id>", methods=["DELETE"])
def delete_comment(comment_id: int) -> Response:
    with closing(get_connection()) as conn, conn, closing(conn.cursor()) as cursor:
        cursor.execute(
            "SELECT post_id FROM comments WHERE id = ?",
            (comment_id,),
        )
        row = cursor.fetchone()
        if row is None:
            abort(404)
        (post_id,) = row
        cursor.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
        comments = get_comments_for_post(cursor, post_id)

    return render_template("partials/comment_list.html", comments=comments, post_id=post_id)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
