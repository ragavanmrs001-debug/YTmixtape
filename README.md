# 🎧 YT Mixtape Studio

> Production-grade YouTube mixtape generator with FastAPI backend & Streamlit frontend.

Generate professional DJ-style mixtapes with **smooth cross-fading**, **auto-generated YouTube descriptions with timestamps**, and **static-image videos** — all from a beautiful web interface.

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| **🎵 Mixtape Generation** | Cross-fade multiple audio tracks with configurable overlap, fade-out/fade-in, and low-pass filtering |
| **📝 Description Generation** | Auto-create YouTube descriptions with tracklist timestamps, genre, hashtags |
| **🎬 Video Generation** | Combine a background image + mixtape audio into an MP4 via FFmpeg |
| **🚀 Full Pipeline** | One-click: mixtape → description → video |
| **🖥️ Web UI** | Premium dark-themed Streamlit dashboard |
| **⚡ REST API** | FastAPI backend with Swagger docs at `/docs` |

---

## 📂 Project Structure

```
youtube_mixtape/
├── app/
│   ├── __init__.py          # package init
│   ├── main.py              # FastAPI app
│   ├── audio.py             # mixtape generator functions (refactored)
│   ├── video.py             # ffmpeg wrapper
│   ├── description.py       # description generator
│   ├── utils.py             # helpers (file paths, job status)
│   └── config.py            # constants
├── frontend/
│   └── streamlit_app.py     # Streamlit UI that calls FastAPI
├── mixtape/                  # input tracks (drop your .mp3/.wav here)
├── images/                   # background images
├── output/                   # generated files saved here
├── requirements.txt
├── run.sh                    # server start commands
└── README.md
```

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

> **Note:** You also need [FFmpeg](https://ffmpeg.org/) installed on your system.
> - macOS: `brew install ffmpeg`
> - Ubuntu: `sudo apt install ffmpeg`

### 2. Start the Servers

Open **two terminals** in the project root:

**Terminal 1 — FastAPI Backend:**
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Terminal 2 — Streamlit Frontend:**
```bash
streamlit run frontend/streamlit_app.py --server.port 8501
```

### 3. Open the App

- **Frontend UI:** [http://localhost:8501](http://localhost:8501)
- **API Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/upload-tracks` | Upload audio files |
| `POST` | `/api/upload-image` | Upload background image |
| `POST` | `/api/generate-mixtape` | Generate cross-faded mixtape |
| `POST` | `/api/generate-description` | Generate YouTube description |
| `POST` | `/api/generate-video` | Generate MP4 video |
| `POST` | `/api/generate-all` | Full pipeline |
| `GET` | `/api/jobs/{job_id}` | Check job status |
| `GET` | `/api/download/{filename}` | Download generated file |
| `GET` | `/api/list-tracks` | List uploaded tracks |
| `GET` | `/api/list-images` | List uploaded images |
| `DELETE`| `/api/clear-tracks` | Remove all tracks |
| `GET` | `/api/health` | Health check |

---

## 🎛️ Configuration

All defaults are in [`app/config.py`](app/config.py):

| Setting | Default | Description |
|---------|---------|-------------|
| `TRANSITION_MS` | 6000 | Cross-fade overlap (ms) |
| `CHANNELS` | 2 | Stereo output |
| `FRAME_RATE` | 44100 | Sample rate (Hz) |
| `VIDEO_RESOLUTION` | 1280×720 | Output video size |
| `FPS` | 1 | Video frame rate |
| `PRESET` | ultrafast | FFmpeg encoding speed |

---

## 🛠️ Tech Stack

- **Backend:** FastAPI + Uvicorn
- **Frontend:** Streamlit
- **Audio:** pydub + FFmpeg
- **Video:** FFmpeg (subprocess)
- **Image:** Pillow

---

## 📄 License

MIT