from pathlib import Path
import os
import sqlite3

import requests
from flask import Flask, abort, jsonify, render_template, request

from scripts.build_index import DATA_PATH, DB_PATH, build_index


app = Flask(__name__)
ROOT = Path(__file__).resolve().parent


def load_env_file(path=ROOT / ".env"):
    if not path.exists():
        return

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


load_env_file()
SERPAPI_SEARCH_ENDPOINT = os.environ.get(
    "SERPAPI_SEARCH_ENDPOINT", "https://serpapi.com/search.json"
)


def ensure_index():
    if not DATA_PATH.exists():
        return
    if not DB_PATH.exists() or DATA_PATH.stat().st_mtime > DB_PATH.stat().st_mtime:
        build_index(DATA_PATH, DB_PATH)


def get_db():
    ensure_index()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def search_local(query, limit=10):
    if not DATA_PATH.exists():
        return {"results": [], "error": "data/lyrics.csv was not found."}

    if not query.strip():
        return {"results": []}

    try:
        with get_db() as conn:
            rows = conn.execute(
                """
                SELECT
                    songs.id,
                    songs.rank,
                    songs.title,
                    songs.year,
                    songs.artist,
                    snippet(songs_fts, 3, '<mark>', '</mark>', ' ... ', 28) AS snippet,
                    bm25(songs_fts) AS score
                FROM songs_fts
                JOIN songs ON songs.id = songs_fts.rowid
                WHERE songs_fts MATCH ?
                ORDER BY score
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
    except sqlite3.OperationalError as exc:
        return {
            "results": [],
            "error": f"Search query could not be parsed: {exc}",
        }

    return {
        "results": [
            {
                "id": row["id"],
                "rank": row["rank"],
                "title": row["title"],
                "year": row["year"],
                "artist": row["artist"],
                "snippet": row["snippet"],
            }
            for row in rows
        ]
    }


def search_web(query, limit=10):
    api_key = os.environ.get("SERPAPI_API_KEY")
    if not api_key or api_key.startswith("paste-your-"):
        return {
            "results": [],
            "error": "SERPAPI_API_KEY is not configured on this server.",
        }
    if not query.strip():
        return {"results": []}

    response = requests.get(
        SERPAPI_SEARCH_ENDPOINT,
        params={
            "api_key": api_key,
            "engine": "google",
            "q": query,
            "num": min(limit, 10),
        },
        timeout=20,
    )
    if not response.ok:
        try:
            error_payload = response.json()
            error_message = error_payload.get("error") or error_payload.get("message")
        except ValueError:
            error_message = response.text
        error_message = error_message or "SerpApi search request failed."
        return {"results": [], "error": f"SerpApi search failed: {error_message}"}

    payload = response.json()
    if payload.get("error"):
        return {"results": [], "error": f"SerpApi search failed: {payload['error']}"}

    pages = payload.get("organic_results", [])
    return {
        "results": [
            {
                "title": page.get("title", "Untitled result"),
                "url": page.get("link", "#"),
                "snippet": page.get("snippet", ""),
                "displayUrl": page.get("displayed_link", page.get("link", "")),
            }
            for page in pages
        ]
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/search")
def api_search():
    mode = request.args.get("mode", "local")
    query = request.args.get("q", "")
    limit = min(int(request.args.get("limit", 10)), 25)

    try:
        if mode == "web":
            return jsonify(search_web(query, limit))
        return jsonify(search_local(query, limit))
    except requests.RequestException as exc:
        return jsonify({"results": [], "error": f"Web search failed: {exc}"}), 502


@app.route("/song/<int:song_id>")
def song(song_id):
    if not DB_PATH.exists():
        ensure_index()
    with get_db() as conn:
        row = conn.execute("SELECT * FROM songs WHERE id = ?", (song_id,)).fetchone()
    if row is None:
        abort(404)
    return render_template("song.html", song=row)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
