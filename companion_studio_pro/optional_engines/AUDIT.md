# Supplied archive audit

The archives were inspected without executing their setup scripts.

## Integrated capability sources

- CogVideoX, Text2Video-Zero and Tune-A-Video inform the local generation, controlled-video and tuning adapters.
- Video2Description informs local video description/caption workflows; the core uses modern Whisper-compatible timing rather than its legacy environment.
- Aphantasia adds CLIP-guided ideation as an optional research pack.
- Text-To-Video-AI contributes Edge TTS, Whisper and composition workflow ideas; its paid API integrations are not required.
- Magic Touch demonstrates image pans, fades and narration assembly. Equivalent effects already exist in the core FFmpeg/timeline implementation; GPL code is not copied into it.
- Waver is catalogued but the supplied archive contains documentation/assets rather than runnable weights and code.

## Excluded from automatic installation

Repositories with missing licences are not redistributed. Curated “awesome” lists are documentation, not models. Research packs with incompatible historical Python/CUDA pins are imported as source only and remain isolated from the core environment.

Model checkpoints are never included in the installer. Their licences and storage requirements vary, and downloading multi-gigabyte weights requires an explicit user choice.

