import sys
import asyncio
from pathlib import Path

# Allow `python scripts/run_polling.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.providers.manager import AIProviderManager
from app.bot.client import build_application
from app.intelligence.extractor import IntelligenceExtractor

# python-telegram-bot's synchronous runner expects a current loop;
# Python 3.14 no longer creates one implicitly in the main thread.
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

s=get_settings(); m=AIProviderManager(s); build_application(s,m,IntelligenceExtractor(m)).run_polling()
