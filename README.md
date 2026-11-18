# IntelKit — AI-Powered Content Intelligence

A Telegram-only Python bot that extracts useful knowledge from public Instagram links and uploaded images, albums, and videos. It follows a signal-not-noise report style and never claims to analyze inaccessible content.

## What is implemented

- FastAPI health endpoint and production webhook endpoint with Telegram secret validation.
- Production startup initializes the Telegram application, starts its update processor, and automatically registers `WEBHOOK_BASE_URL/telegram/webhook` with Telegram.
- Development-safe provider manager with Groq → Gemini → OpenRouter fallback.
- Image OCR, carousel ordering/aggregation, video frame/audio extraction through FFmpeg.
- Concise structured report formatting with optional claims-to-verify section.
- Instagram public-page best-effort retrieval using visible `og:image` metadata; no authentication bypass.
- `/start`, `/help`, and `/status` Telegram commands.
- Automated tests that do not require real credentials.

## Limitations

The initial database-free Render architecture has no durable job queue, user history, or crash recovery for in-flight media. Instagram access depends on public HTML and can fail because Instagram changes or restricts delivery; upload the media directly when that happens. Speech transcription is intentionally a hook until a compatible STT credential is configured. Install the system `ffmpeg` binary for video processing.

## Local macOS setup

```bash
git clone https://github.com/awakenedarpit/IntelKit.git
cd IntelKit
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
brew install ffmpeg tesseract
cp .env.example .env
# edit .env and set TELEGRAM_BOT_TOKEN plus at least one AI key
pytest -q
APP_ENV=development python -m uvicorn app.main:app --reload
```

After credentials are configured, run polling locally with `python scripts/run_polling.py`; production never runs polling. The current build keeps import/startup testable without requiring a token.

## Render

Build command: `pip install -r requirements.txt`

Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Set `APP_ENV=production`, `WEBHOOK_BASE_URL` to the full Render service URL such as `https://your-service.onrender.com`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_BOT_TOKEN`, and the provider keys. On every production startup, IntelKit registers `https://your-service.onrender.com/telegram/webhook` automatically; no separate webhook command is required.

## Testing checklist

1. Run `pytest -q`.
2. Start the FastAPI app and open `/health`.
3. Configure one provider and exercise `/start`, `/help`, `/status`.
4. Send a single image with visible text.
5. Send an album and confirm one combined report.
6. Send a short video after installing FFmpeg.
7. Send a public Instagram link; if retrieval fails, confirm the bot asks for a direct upload.
8. Temporarily make the first provider unavailable and confirm fallback logs and response.
9. Test oversized/unsupported files and verify they are rejected without secrets in logs.
10. Approve production deployment only after these local checks pass.
