import sys
from pathlib import Path

# Allow `python scripts/run_polling.py` from the repository root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import get_settings
from app.providers.manager import AIProviderManager
from app.bot.client import build_application
from app.intelligence.extractor import IntelligenceExtractor
s=get_settings(); m=AIProviderManager(s); build_application(s,m,IntelligenceExtractor(m)).run_polling()
