from app.services.ocr import extract_text

async def process(path, extractor):
    text = extract_text(path)
    prompt = 'Uploaded image. OCR text:\n' + (text or '[No readable text detected]')
    try:
        return await extractor.analyze(prompt, [open(path, 'rb').read()])
    except Exception:
        if text:
            return '**Extracted Text (AI analysis unavailable)**\n' + text + '\n\nConfigure at least one AI provider key for visual understanding.'
        raise
