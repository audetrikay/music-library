# Music Library — What Your Music Looks Like

An interactive music library that transforms recent listening history into a visual collection of albums.

**Live website:** https://student05.wt.thomasjuldo.com/music/

## 1. Project concept

Music Library was created for the web development assignment **"What Your Music Looks Like"**.

Instead of displaying music as a traditional list, the application presents albums in a vintage-inspired wooden bookshelf.

Each album becomes an interactive object that users can explore to discover its cover, artist, tracks and listening information.

The project combines music data visualization, interactive design and personal nostalgia.

### The Forgotten Drawer

One of the main features is **The Forgotten Drawer**.

The application identifies the 10% of albums that have not been listened to for the longest time within the retrieved listening history.

These albums are separated from the main bookshelf and placed in a drawer that users can open to rediscover forgotten music.

The selection updates when the listening data changes.

## 2. Technologies

| Technology | Purpose |
|---|---|
| HTML | Page structure |
| CSS | Visual design and animations |
| JavaScript | User interactions and dynamic content |
| Python / Flask | Backend API |
| Last.fm API | Recent listening history |
| Nginx | Frontend web server and API proxy |
| Docker Compose | Container orchestration |
| Caddy | HTTPS reverse proxy on the deployment server |

## 3. How it works

The application follows a client-server architecture:

1. The browser requests music data from the Flask backend through `/api/albums`.
2. The backend requests recent tracks from the Last.fm API using `user.getRecentTracks`.
3. The backend groups tracks by album and prepares the data for visualization.
4. Albums are divided between the main bookshelf and the Forgotten Drawer.
5. The frontend displays the results as an interactive music collection.

The browser does not call the Last.fm API directly.

### Caching

The backend caches the music data for 60 seconds to reduce unnecessary requests to Last.fm.

If Last.fm becomes unavailable, the backend can return previously cached data when available. Otherwise, the application displays an error message.

### API security

The Last.fm API key is stored in a `.env` file and is only used by the backend.

The `.env` file is excluded from Git using `.gitignore`.

## 4. Installation

### Requirements

- Docker
- Docker Compose
- A Last.fm account
- A Last.fm API key

### Step 1 — Clone the repository

```bash
git clone https://github.com/audetrikay/music-library.git
cd music-library
```

### Step 2 — Configure environment variables

Create a `.env` file in the project root using `.env.example` as a template.

```env
LASTFM_API_KEY=your_api_key_here
LASTFM_USER=your_lastfm_username
```

You can obtain an API key at:

https://www.last.fm/api/account/create

### Step 3 — Start the application

```bash
docker compose up -d --build
```

### Step 4 — Open the website

Visit:

http://localhost:8080

To stop the application:

```bash
docker compose down
```

## 5. Project structure

```text
music-library/
├── backend/
│   ├── app.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── index.html
│   ├── style.css
│   ├── script.js
│   ├── nginx.conf
│   └── Dockerfile
├── image/
├── compose.yaml
├── .env.example
├── .gitignore
└── README.md
```

## 6. Deployment

The application is deployed on an Ubuntu server using Docker Compose, Nginx and Caddy.

Public URL:

https://student05.wt.thomasjuldo.com/music/

The application is hosted under `/music/` alongside another web project.

## 7. Design choices

The main goal was to create an experience that feels like exploring a physical music collection.

The visual identity includes:

- A vintage wooden bookshelf.
- Album covers presented as collectible objects.
- Warm retro colours and expressive typography.
- Interactive navigation and album exploration.
- A dedicated drawer for rediscovering less recently played albums.

The result is intended to be more personal and engaging than a conventional music dashboard.

## 8. Limitations

- The visualization depends on the listening history available through Last.fm.
- Albums without available artwork may require fallback visuals.
- The Forgotten Drawer represents the least recently listened albums within the retrieved data, not necessarily the user's entire lifetime listening history.
- Music data updates according to the backend cache duration.

## Author

Aude Desperies

ESILV — Web Development Project, 2026.