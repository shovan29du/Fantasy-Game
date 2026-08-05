# Companion Studio

A private, local-first product-ad studio inspired by Pippit's most useful workflow. It extracts product pages, writes three ad concepts, finds free stock candidates, assembles scenes, creates offline narration, mixes music, and exports a vertical H.264 MP4.

## Quick start on Windows

Requirements: Node.js 22+ and Python 3.11+.

1. Extract the project folder.
2. Right-click `start-local.ps1` and choose **Run with PowerShell**. If Windows blocks it, open PowerShell in this folder and run `powershell -ExecutionPolicy Bypass -File .\start-local.ps1`.
3. Open the local address printed in the terminal.

The first launch installs the free local dependencies. Product data and uploaded media stay on your computer.

## Included without external AI

- Product URL extraction using structured data and page metadata
- Photo and footage upload
- Three built-in advertising concepts when Ollama is unavailable
- Editable scenes, calls to action, themes, timing, captions, and previews
- Wikimedia Commons stock-image search with source and credit information
- Browser voice preview
- Offline Windows voice rendering when a system voice is available
- Background-music mixing
- Bundled FFmpeg download through `npm install`
- 1080 × 1920 H.264/AAC MP4 export
- Device-local draft saving

## Optional local AI engines

The app detects these automatically:

- **Ollama:** install Ollama and run `ollama pull qwen2.5:3b` for locally generated scripts.
- **Stable Diffusion:** run AUTOMATIC1111 or Forge with `--api` for local product-image generation.
- **rembg:** run `.venv\Scripts\python -m pip install rembg onnxruntime` for background removal support.
- **faster-whisper:** run `.venv\Scripts\python -m pip install faster-whisper` for local transcription support.
- **Piper:** place `piper` on PATH with a configured voice for fully offline narration on systems without a Windows voice pack.

The core editor and MP4 renderer still work when the optional engines are absent.

## Pro editor upgrades

- Drag-and-drop multi-track timeline for video, text, narration, and music
- Per-scene duration, transition, animation preset, and narrator
- Scene split, duplicate, delete, and reordering controls
- 30 FPS frame playhead with scrubbing
- Undo and redo history plus automatic local draft saving
- Ken Burns, parallax, rotation, kinetic-text, and reveal presets
- Saved brand kit with colours, tone, and disclaimers
- Batch format planning for 9:16, 4:5, 1:1, 16:9, and six-second bumpers
- Hook scoring and basic compliance preflight
- Portable JSON project export and restore
- Duration-aware MP4 rendering

Shop and social-publishing connectors are shown as authorization-ready integrations. They remain inactive until the user supplies and approves the relevant Shopify, YouTube, TikTok, Meta, Pinterest, or LinkedIn account access.

## Optional GPU Lab

The editor now includes guarded adapters for:

- Text-to-image generation
- Chat-to-image scene generation from companion dialogue
- Local image-to-video animation
- Talking product presenters
- AI UGC avatars
- Multilingual lip-sync
- Generated product placement
- Motion transfer
- Consent-based voice cloning
- Generative B-roll
- Automatic advert localisation

The local engine detects NVIDIA GPU memory and the following services:

- ComfyUI at `http://127.0.0.1:8188`
- LivePortrait at `http://127.0.0.1:8890`
- Coqui/XTTS at `http://127.0.0.1:8020`
- Ollama at `http://127.0.0.1:11434`
- Stable Diffusion WebUI/Forge at `http://127.0.0.1:7860`

These URLs can be changed with `COMFYUI_URL`, `LIVEPORTRAIT_URL`, `XTTS_URL`, `OLLAMA_URL`, and `STABLE_DIFFUSION_URL`. ComfyUI tasks use user-exported API workflows in `local_api/workflows`; see that folder's README for filenames and placeholders. This avoids locking the app to checkpoint names or custom nodes that may not exist on another computer.

Avatar, lip-sync, motion-transfer, presenter, and voice-cloning jobs require an explicit permission confirmation in the UI. The application does not bypass identity or consent checks.

## Video and document intelligence

- Generate timed SRT and WebVTT subtitles from video or audio with local Whisper.
- Scan video frames for slides, pictures, visible text, diagrams, charts, tables, mathematics, and formulas using Tesseract OCR plus an optional local Ollama vision model.
- Create structured notes and export them as DOCX, PPTX, PDF, or XLSX.
- Extract and read text aloud from PDF, DOCX, PPTX, XLSX, text, Markdown, CSV, JSON, HTML, subtitle, and image files.
- Customize a local reader avatar's name, style, colours, speech speed, and pitch.

Extraction quality depends on the source resolution, frame interval, speech clarity, and model accuracy. The app preserves OCR/vision uncertainty; review formulas and numeric tables before relying on them.

## Full installation package

Run the installer for your operating system:

- Windows: double-click `install_windows.bat`
- macOS: run `install_macos.command`
- Linux: run `sh install_linux.sh`
- Any OS: `python full_install.py`

The normal installer is now the **complete installation**. It creates the core Python environment, installs the interface and bundled FFmpeg, document exporters, PyTorch plus image/speech/caption libraries, Tesseract OCR, Ollama with writing and vision models, and ComfyUI in a separate environment. It then runs a production build and creates launcher shortcuts. On Windows it targets both the standard Desktop and OneDrive Desktop when both exist.

Optional switches:

```text
python full_install.py
python full_install.py --minimal
python full_install.py --skip-models
python full_install.py --import-research
python full_install.py --import-research --launch
```

The full installation can download several gigabytes. `--minimal` skips the large AI engines. `--skip-models` installs Ollama but skips its language-model download. ComfyUI checkpoint files are not silently chosen because checkpoints are large creative assets with model-specific licences; add a checkpoint you are licensed to use to `engines/ComfyUI/models/checkpoints`. `--import-research` safely extracts compatible supplied archives from Downloads into isolated source folders without executing their setup scripts or merging conflicting historical dependencies into the core environment.

## Important stock-media note

Wikimedia results come from many individual licences. Open the source page and check attribution and commercial-use terms before publishing an advertisement.
