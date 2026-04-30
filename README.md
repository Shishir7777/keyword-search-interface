# Keyword Search Interface

This project implements:

- Web search through SerpApi's Google Search API.
- Local keyword search over `lyrics.csv` using SQLite FTS5.
- Dynamic KWIC-style snippets for local results.
- Clickable local song titles that open the full song page with lyrics.

## 1. Set up locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 2. Add the dataset

Put the assignment dataset at:

```text
data/lyrics.csv
```

The CSV should contain these columns:

```text
rank,title,year,artist,lyrics
```

A tiny sample file is included so the app can run before you add the real dataset.

## 3. Configure web search

Create a SerpApi API key. Then create a `.env` file:

```env
SERPAPI_API_KEY=your-serpapi-api-key
SERPAPI_SEARCH_ENDPOINT=https://serpapi.com/search.json
```

If the key is missing, the web search tab will show a clear setup message.

## 4. Run

```bash
flask --app app run --host 0.0.0.0 --port 5000
```

Open:

```text
http://127.0.0.1:5000
```

## 5. Rebuild the local search index

The app automatically rebuilds the SQLite index when `data/lyrics.csv` is newer than `instance/lyrics.db`.

You can also rebuild it manually:

```bash
python scripts/build_index.py
```

## 6. Deployment notes

For a public demo, deploy this Flask app to a server where you can install Python packages, such as Render, Railway, Fly.io, a VPS, or your own Apache/Nginx reverse proxy setup.

For TxState `public_html`, you can only host static HTML easily, so that is suitable for a simple Part A static page only if your web API call is handled elsewhere. The full local search service needs a real app server.

## 7. Deploy on Render

Render's Flask quickstart says a Python web service can use:

- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn app:app`

Source:
[Render Flask docs](https://render.com/docs/deploy-flask)

### Steps

1. Put this project in a GitHub repository.
2. In Render, click `New` -> `Web Service`.
3. Connect the GitHub repo.
4. Use these settings:

```text
Language: Python 3
Build Command: pip install -r requirements.txt
Start Command: gunicorn app:app
```

5. Add environment variables in Render:

```text
SERPAPI_API_KEY=your-real-serpapi-key
SERPAPI_SEARCH_ENDPOINT=https://serpapi.com/search.json
```

6. Deploy.
7. After the service is live, open the public `onrender.com` URL and test both Local and Web modes.

Note: your `data/lyrics.csv` file must be committed to the repo if you want local search to work on Render.
