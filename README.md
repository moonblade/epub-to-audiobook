# EPUB to Audio Converter

Convert EPUB ebooks to audiobooks using AI voice synthesis powered by [Kokoro TTS](https://github.com/nazdridoy/kokoro-tts).

## Features

- **Drag & Drop Upload** - Simple web interface for uploading EPUB files
- **27 English Voices** - US and UK accents, male and female voices
- **Real-time Progress** - Live logs and progress tracking via SSE
- **Stop/Resume** - Pause and resume conversions at any time
- **Chapter Output** - Individual chapter files + merged full audiobook
- **Auto Model Download** - TTS models download automatically on first run

## Quick Start

```bash
# Clone and setup
git clone https://github.com/moonblade/epubtoaudio.git
cd epubtoaudio

# Setup and run (downloads models on first run)
make run
```

Open http://localhost:8000 in your browser.

## Requirements

- Python 3.10+
- ~500MB disk space (for TTS models)

## Installation

### Using Make (Recommended)

```bash
make setup    # Create venv, install deps, download models
make run      # Start the server
```

### Manual Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Download models
mkdir -p models
curl -L -o models/kokoro-v1.0.onnx https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/kokoro-v1.0.onnx
curl -L -o models/voices-v1.0.bin https://github.com/nazdridoy/kokoro-tts/releases/download/v1.0.0/voices-v1.0.bin

# Run
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Configuration

Environment variables for custom paths:

| Variable | Default | Description |
|----------|---------|-------------|
| `EPUBTOAUDIO_UPLOAD_PATH` | `./input` | Directory for uploaded EPUB files |
| `EPUBTOAUDIO_OUTPUT_PATH` | `./output` | Directory for generated audio files |

Example:
```bash
EPUBTOAUDIO_UPLOAD_PATH=/data/uploads EPUBTOAUDIO_OUTPUT_PATH=/data/audio make run
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Web UI |
| `POST` | `/upload` | Upload EPUB (form: `file`, `voice`, optional `upload_path`, `output_path`) |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/{id}` | Get job status |
| `POST` | `/jobs/{id}/stop` | Pause conversion |
| `POST` | `/jobs/{id}/resume` | Resume conversion |
| `DELETE` | `/jobs/{id}` | Delete job and files |
| `GET` | `/jobs/{id}/logs` | SSE log stream |
| `GET` | `/jobs/{id}/audio` | Download full audiobook |
| `GET` | `/jobs/{id}/audio/{chapter}` | Download specific chapter |
| `GET` | `/voices` | List available voices |

## Available Voices

### US English
| Male | Female |
|------|--------|
| am_adam (default) | af_alloy |
| am_echo | af_aoede |
| am_eric | af_bella |
| am_fenrir | af_heart |
| am_liam | af_jessica |
| am_michael | af_kore |
| am_onyx | af_nicole |
| am_puck | af_nova |
| | af_river |
| | af_sarah |
| | af_sky |

### UK English
| Male | Female |
|------|--------|
| bm_daniel | bf_alice |
| bm_fable | bf_emma |
| bm_george | bf_isabella |
| bm_lewis | bf_lily |

## Project Structure

```
epubtoaudio/
├── main.py           # FastAPI application
├── converter.py      # EPUB parsing + TTS conversion
├── job_manager.py    # Job state persistence
├── models.py         # Pydantic models
├── config.py         # Configuration
├── logger.py         # Logging with daily rotation
├── templates/        # Jinja2 HTML templates
├── static/           # CSS
├── models/           # TTS model files (gitignored)
├── input/            # Uploaded EPUBs (gitignored)
├── output/           # Generated audio (gitignored)
└── jobs/             # Job state JSON (gitignored)
```

## License

MIT
