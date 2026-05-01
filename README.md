# TikTok Transcriber

Paste a TikTok link or upload an MP4 → get the full transcript via Whisper.

## Deploy on Railway

1. Go to railway.app → New Project → Deploy from local directory
2. Upload this folder
3. Done — Railway auto-detects Python + installs ffmpeg via nixpacks.toml

## Run locally

```bash
pip install flask openai yt-dlp
brew install ffmpeg  # Mac
python app.py
```

Then open → http://localhost:5055

## Notes

- Works with TikTok, Instagram Reels, YouTube Shorts
- Transcription via OpenAI Whisper (~$0.006/min)
