from app.services.ocr import extract_text

async def process(path, extractor, context_text=''):
    text = extract_text(path)
    prompt = 'Uploaded image. OCR text:\n' + (text or '[No readable text detected]')
    if context_text:
        prompt += '\n\nPublic Instagram caption/description:\n' + context_text
    try:
        return await extractor.analyze(prompt, [open(path, 'rb').read()])
    except Exception:
        if text:
            return '**Extracted Text (AI analysis unavailable)**\n' + text + '\n\nConfigure at least one AI provider key for visual understanding.'
        raise
