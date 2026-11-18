import json
from fastapi.testclient import TestClient
from app.main import app
from app.config import Settings
from app.intelligence.deduplicator import deduplicate
from app.processors.instagram_processor import classify, _meta_content
from app.intelligence.report_generator import format_report
from app.providers.base import ProviderResult, ProviderError
from app.providers.manager import AIProviderManager
def test_health(): assert TestClient(app).get('/health').status_code==200
def test_urls(): assert classify('https://instagram.com/reel/ABC123')=='reel'; assert classify('https://instagram.com/nope') is None
def test_instagram_meta_attribute_order():
    html='<meta content="https://cdn.example/image.jpg" property="og:image">'
    assert _meta_content(html, 'og:image') == 'https://cdn.example/image.jpg'
def test_deduplicate(): assert deduplicate(['A fact','a fact','B'])==['A fact','B']
def test_report():
    out=format_report(json.dumps({'sections':[{'title':'Main Takeaway','bullets':['Useful point']}]}),'test'); assert 'Useful point' in out and 'Main Takeaway' in out
def test_settings(): assert Settings(app_env='test').max_file_size_bytes>0

def test_provider_order():
    import asyncio
    settings = Settings(primary_provider='groq', fallback_providers='gemini', groq_api_key='g', gemini_api_key='g2')
    manager = AIProviderManager(settings)
    async def fail(*args, **kwargs): raise ProviderError('temporary', retryable=True)
    async def succeed(*args, **kwargs): return ProviderResult('ok', 'gemini', 'test')
    manager.providers['groq'].analyze = fail
    manager.providers['gemini'].analyze = succeed
    result = asyncio.run(manager.analyze('test'))
    assert result.provider == 'gemini'
