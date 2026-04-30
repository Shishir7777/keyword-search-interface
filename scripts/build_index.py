from pathlib import Path
import csv
import sqlite3
import sys


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "lyrics.csv"
DB_PATH = ROOT / "instance" / "lyrics.db"


def normalize_header(name):
    return name.strip().lower().replace(" ", "_")


def find_column(field_map, options):
    for option in options:
        if option in field_map:
            return field_map[option]
    return None


def build_index(csv_path=DATA_PATH, db_path=DB_PATH):
    if not csv_path.exists():
        raise FileNotFoundError(f"Could not find dataset: {csv_path}")

    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        conn.execute("DROP TABLE IF EXISTS songs")
        conn.execute("DROP TABLE IF EXISTS songs_fts")
        conn.execute(
            """
            CREATE TABLE songs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                rank TEXT,
                title TEXT NOT NULL,
                year TEXT,
                artist TEXT,
                lyrics TEXT
            )
            """
        )
        conn.execute(
            """
            CREATE VIRTUAL TABLE songs_fts USING fts5(
                title,
                artist,
                year,
                lyrics,
                content='songs',
                content_rowid='id',
                tokenize='porter unicode61'
            )
            """
        )

        encodings = ["utf-8-sig", "cp1252", "latin-1"]
        last_error = None
        for encoding in encodings:
            try:
                rows = read_song_rows(csv_path, encoding)
                break
            except UnicodeDecodeError as exc:
                last_error = exc
        else:
            raise last_error

        conn.executemany(
            "INSERT INTO songs (rank, title, year, artist, lyrics) VALUES (?, ?, ?, ?, ?)",
            rows,
        )
        conn.execute(
            """
            INSERT INTO songs_fts(rowid, title, artist, year, lyrics)
            SELECT id, title, artist, year, lyrics FROM songs
            """
        )
        conn.commit()

    return len(rows)


def read_song_rows(csv_path, encoding):
    with csv_path.open("r", encoding=encoding, newline="") as handle:
            reader = csv.DictReader(handle)
            if not reader.fieldnames:
                raise ValueError("lyrics.csv has no header row")

            field_map = {normalize_header(field): field for field in reader.fieldnames}
            columns = {
                "rank": find_column(field_map, ["rank"]),
                "title": find_column(field_map, ["title", "song", "song_title"]),
                "year": find_column(field_map, ["year"]),
                "artist": find_column(field_map, ["artist"]),
                "lyrics": find_column(field_map, ["lyrics", "lyric"]),
            }
            missing = [field for field, column in columns.items() if column is None]
            if missing:
                raise ValueError(f"lyrics.csv is missing columns: {', '.join(missing)}")

            rows = []
            for row in reader:
                title = (row.get(columns["title"]) or "").strip()
                if not title:
                    continue
                rows.append(
                    (
                        (row.get(columns["rank"]) or "").strip(),
                        title,
                        (row.get(columns["year"]) or "").strip(),
                        (row.get(columns["artist"]) or "").strip(),
                        (row.get(columns["lyrics"]) or "").strip(),
                    )
                )
    return rows


if __name__ == "__main__":
    try:
        count = build_index()
    except Exception as exc:
        print(f"Index build failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
    print(f"Indexed {count} songs into {DB_PATH}")
