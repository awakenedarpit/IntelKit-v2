import httpx

async def transcribe(path, groq_api_key=''):
    if not groq_api_key:
        return ''
    try:
        with open(path, 'rb') as audio:
            async with httpx.AsyncClient(timeout=90) as client:
                response = await client.post(
                    'https://api.groq.com/openai/v1/audio/transcriptions',
                    headers={'Authorization': f'Bearer {groq_api_key}'},
                    files={'file': (path.name, audio, 'audio/mpeg')},
                    data={'model': 'whisper-large-v3-turbo', 'response_format': 'text'},
                )
        if response.status_code == 200:
            return response.text.strip()
    except (OSError, httpx.HTTPError):
        pass
    return ''
