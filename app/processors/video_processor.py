from pathlib import Path
from app.services.media_service import extract_frames, extract_audio
from app.services.transcription import transcribe

async def process(path, extractor, workspace, context_text=''):
    frames=await extract_frames(path,workspace); audio=await extract_audio(path,Path(workspace)/'audio.mp3')
    transcript=await transcribe(Path(workspace)/'audio.mp3', extractor.manager.settings.groq_api_key) if audio else ''
    imgs=[p.read_bytes() for p in frames]
    note=f"Uploaded video. Extracted {len(frames)} representative frames; audio extraction {'succeeded' if audio else 'failed'}."
    if transcript:
        note += '\n\nSpeech transcript:\n' + transcript
    if context_text:
        note += '\n\nPublic Instagram caption/description:\n' + context_text
    return await extractor.analyze(note,imgs)
