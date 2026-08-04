# Install AiChat Pro

## Windows

Double-click:

```bat
install_windows.bat
```

All optional Python packages install by default.

For only required packages, run:

```bat
install_windows.bat minimal
```

Then launch with:

```bat
run_app.bat
```

The installer creates Windows shortcuts on the normal Desktop and OneDrive Desktop when those folders exist.

## macOS / Linux

From a terminal:

```bash
chmod +x install_unix.sh run_app.sh
./install_unix.sh
./run_app.sh
```

All optional Python packages install by default.

For only required packages:

```bash
./install_unix.sh minimal
```

The installer creates a desktop launcher when the operating system exposes a standard Desktop folder.

## Requirements

- Python 3.10 or newer.
- LM Studio local server is recommended for local LLM chat.
- `full_install.py` contains the required Python package list directly and also reads `requirements.txt` when present.
- Optional tools such as FFmpeg, ComfyUI, Automatic1111, Edge TTS, and Whisper can be installed separately.
- All optional Python packages are installed automatically by default.
- Use the `minimal` argument to skip optional Python packages.
- External desktop/server tools such as LM Studio, FFmpeg, ComfyUI, and Automatic1111 still require separate native installation.

## Knowledge seeding

The installer runs `tools/seed_knowledge.py`, which generates local knowledge files for all built-in race and character options and stores them in the SQLite `knowledge_documents` table when possible.

## Frontend direction

The app launches with FastAPI serving the React frontend at `http://localhost:8501`. Streamlit is not included in this package.




