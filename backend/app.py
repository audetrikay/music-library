import math
import os
import time
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor

import requests
from flask import Flask, jsonify

app = Flask(__name__)

LASTFM_API_KEY = os.environ.get("LASTFM_API_KEY")
LASTFM_USER = os.environ.get("LASTFM_USER", "audetrikay")
LASTFM_URL = "https://ws.audioscrobbler.com/2.0/"

LASTFM_DEFAULT_IMAGE_HASH = "2a96cbd8b46e442fc41c2b86b821562f"

# Cache de 30 secondes pour recalculer rapidement si un album oublié est réécouté
CACHE_DURATION = 30
cache = {"data": None, "timestamp": 0}

http_session = requests.Session()


def fetch_recent_page(page: int):
    """Récupère une page de 200 écoutes récentes horodatées sur Last.fm."""
    try:
        response = http_session.get(
            LASTFM_URL,
            params={
                "method": "user.getrecenttracks",
                "user": LASTFM_USER,
                "api_key": LASTFM_API_KEY,
                "format": "json",
                "limit": 200,
                "page": page,
            },
            timeout=10,
        )
        response.raise_for_status()
        payload = response.json()
        if "error" in payload:
            return []
        tracks = payload.get("recenttracks", {}).get("track", [])
        return [tracks] if isinstance(tracks, dict) else tracks
    except requests.RequestException:
        return []


def extract_best_image(images):
    if not isinstance(images, list):
        return ""
    return next(
        (
            img.get("#text", "")
            for img in reversed(images)
            if img.get("#text")
            and LASTFM_DEFAULT_IMAGE_HASH not in img.get("#text", "")
        ),
        "",
    )


def extract_track_timestamp(track):
    """
    Extrait le timestamp UNIX (uts) et le texte de date depuis un scrobble Last.fm.
    Ne jamais inventer de date si Last.fm n'en fournit pas.
    """
    attr = track.get("@attr", {})
    if isinstance(attr, dict) and attr.get("nowplaying") == "true":
        return int(time.time()), "En écoute actuellement"

    date_info = track.get("date")
    if isinstance(date_info, dict):
        uts_raw = date_info.get("uts")
        date_text = date_info.get("#text", "").strip()
        if uts_raw:
            try:
                return int(uts_raw), date_text
            except ValueError:
                return None, None

    return None, None


def fetch_albums():
    # Pagination Last.fm : jusqu'à 5 pages de 200 titres (1000 écoutes horodatées) en parallèle
    with ThreadPoolExecutor(max_workers=5) as executor:
        recent_futures = [executor.submit(fetch_recent_page, p) for p in range(1, 6)]
        tracks = []
        for f in recent_futures:
            tracks.extend(f.result())

    if not tracks:
        raise ValueError("Aucune donnée reçue depuis Last.fm")

    albums = OrderedDict()

    for track in tracks:
        artist = track.get("artist", {}).get("#text", "").strip()
        album_name = track.get("album", {}).get("#text", "").strip()
        title = track.get("name", "").strip()

        if not artist or not title:
            continue

        if not album_name:
            album_name = title

        uts, date_text = extract_track_timestamp(track)
        key = (artist.lower(), album_name.lower())

        if key not in albums:
            albums[key] = {
                "artist": artist,
                "album": album_name,
                "image": extract_best_image(track.get("image", [])),
                "tracks": [],
                "plays": 0,
                "last_listened_uts": uts,
                "last_listened_date": date_text,
            }

        album = albums[key]
        album["plays"] += 1

        # Conserver la date d'écoute la plus récente rencontrée pour cet album
        if uts is not None:
            if album["last_listened_uts"] is None or uts > album["last_listened_uts"]:
                album["last_listened_uts"] = uts
                album["last_listened_date"] = date_text

        if not album["image"]:
            album["image"] = extract_best_image(track.get("image", []))

        if title not in album["tracks"]:
            album["tracks"].append(title)

    all_albums = list(albums.values())

    # Séparer les albums qui possèdent une date d'écoute Last.fm vérifiée
    dated_albums = [a for a in all_albums if a.get("last_listened_uts") is not None]
    undated_albums = [a for a in all_albums if a.get("last_listened_uts") is None]

    # Trier du plus récemment écouté au plus anciennement écouté
    dated_albums.sort(key=lambda a: a["last_listened_uts"], reverse=True)

    # Calculer les 10 % d'albums non écoutés depuis le plus longtemps
    if len(dated_albums) >= 2:
        forgotten_count = max(1, round(len(dated_albums) * 0.10))
        main_albums = dated_albums[:-forgotten_count] + undated_albums
        # Les 10 % les plus anciens (triés du plus ancien au moins ancien)
        forgotten_albums = list(reversed(dated_albums[-forgotten_count:]))
    else:
        main_albums = all_albums
        forgotten_albums = []

    return {
        "albums": main_albums,
        "forgotten_albums": forgotten_albums,
        "total_albums": len(all_albums),
    }


@app.get("/api/albums")
def get_albums():
    now = time.time()

    if cache["data"] is not None and (now - cache["timestamp"] < CACHE_DURATION):
        payload = dict(cache["data"])
        payload["cached"] = True
        return jsonify(payload)

    try:
        if not LASTFM_API_KEY:
            raise ValueError("LASTFM_API_KEY is missing")

        result = fetch_albums()
        cache["data"] = result
        cache["timestamp"] = now

        payload = dict(result)
        payload["cached"] = False
        return jsonify(payload)

    except (requests.RequestException, ValueError) as error:
        app.logger.warning("Last.fm request failed: %s", error)

        if cache["data"] is not None:
            payload = dict(cache["data"])
            payload.update({
                "cached": True,
                "stale": True,
                "message": "Last.fm is temporarily unavailable.",
            })
            return jsonify(payload)

        return jsonify({
            "albums": [],
            "forgotten_albums": [],
            "message": "Unable to load music from Last.fm.",
        }), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
