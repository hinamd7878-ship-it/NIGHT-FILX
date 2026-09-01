#!/usr/bin/env python3
"""
NIGHTFLIX Movie Asset Importer

Put one movie folder inside MOVIE_ASSETS/:
  MOVIE_ASSETS/
    Movie Name/
      poster.jpg
      screenshots/
        01.jpg
        02.jpg

The script finds the first poster image automatically and all screenshot images,
copies them into POSTER/, and appends/updates movies.json.

Run:
  python tools/add_movie.py
"""

from pathlib import Path
import json, shutil, re
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = ROOT / "MOVIE_ASSETS"
POSTER_ROOT = ROOT / "POSTER"
JSON_FILE = ROOT / "movies.json"

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

def slugify(name):
    s = re.sub(r"[^a-zA-Z0-9]+", "-", name).strip("-").lower()
    return s or "movie"

def ask(prompt, default=""):
    value = input(f"{prompt}" + (f" [{default}]" if default else "") + ": ").strip()
    return value or default

def main():
    ASSET_ROOT.mkdir(exist_ok=True)
    folders = sorted([p for p in ASSET_ROOT.iterdir() if p.is_dir()])

    if not folders:
        print("\nNo movie folder found.")
        print("Create: MOVIE_ASSETS/Movie Name/poster.jpg")
        print("Optional screenshots: MOVIE_ASSETS/Movie Name/screenshots/*.jpg")
        return

    print("\nAvailable movie folders:")
    for i, folder in enumerate(folders, 1):
        print(f"  {i}. {folder.name}")

    choice = ask("Choose folder number", "1")
    try:
        folder = folders[int(choice) - 1]
    except (ValueError, IndexError):
        print("Invalid selection.")
        return

    title = ask("Movie / Series title", folder.name)
    year = int(ask("Year", "2026"))
    genre = ask("Genre", "Action")
    content_type = ask("Content type (movie/webseries/tvshow)", "movie")
    category = ask("Category (Movie/Web Series/TV Show/Hollywood/18+)", "")
    watch = ask("Watch URL", "")
    download = ask("Download URL", "")

    images = [
        p for p in folder.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ]

    screenshot_dir = folder / "screenshots"
    screenshots = [
        p for p in screenshot_dir.rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    ] if screenshot_dir.exists() else []

    poster_candidates = [
        p for p in images
        if p.parent == folder and p.name.lower().startswith(("poster","cover"))
    ]
    if not poster_candidates:
        poster_candidates = [p for p in images if p.parent == folder]
    if not poster_candidates:
        print("No poster image found in the selected folder.")
        return

    poster_src = poster_candidates[0]

    try:
        movies = json.loads(JSON_FILE.read_text(encoding="utf-8"))
    except Exception:
        movies = []

    ids = [
        int(m["id"]) for m in movies
        if isinstance(m, dict) and str(m.get("id","")).isdigit()
    ]
    next_id = max(ids, default=0) + 1

    slug = slugify(title)
    target = POSTER_ROOT / slug
    target.mkdir(parents=True, exist_ok=True)

    poster_dst = target / f"poster{poster_src.suffix.lower()}"
    shutil.copy2(poster_src, poster_dst)

    photos = []
    for i, src in enumerate(screenshots, 1):
        dst = target / "screenshots" / f"{i:02d}{src.suffix.lower()}"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        photos.append(dst.relative_to(ROOT).as_posix())

    item = {
        "site": "nightflix",
        "id": next_id,
        "title": title,
        "year": year,
        "genre": genre,
        "rating": 0,
        "poster": poster_dst.relative_to(ROOT).as_posix(),
        "status": "Completed",
        "contentType": content_type,
        "description": "",
        "watch": watch,
        "download": download,
        "episodes": [],
        "photos": photos,
        "popular": False,
        "isNew": True,
        "addedAt": datetime.now(timezone.utc).isoformat()
    }

    if category:
        item["category"] = category

    movies.append(item)
    JSON_FILE.write_text(
        json.dumps(movies, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("\nDONE")
    print(f"Added: {title}")
    print(f"ID: {next_id}")
    print(f"Poster: {item['poster']}")
    print(f"Screenshots: {len(photos)}")
    print("\nNow test the website, then git add/commit/push the changed files.")

if __name__ == "__main__":
    main()
