import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from .config import get_settings
from .utils.logging_config import configure_logging
from .providers.manager import AIProviderManager
from .intelligence.extractor import IntelligenceExtractor
from .api.health import router as health_router
from .api.webhook import router as webhook_router

settings = get_settings()
configure_logging(settings.log_level)
log = logging.getLogger(__name__)
manager = AIProviderManager(settings)
extractor = IntelligenceExtractor(manager)
telegram_app = None

if settings.app_env == 'production':
    from .bot.client import build_application
    try:
        telegram_app = build_application(settings, manager, extractor)
    except RuntimeError as exc:
        log.error('Telegram webhook disabled: %s', exc)

@asynccontextmanager
async def lifespan(application: FastAPI):
    if telegram_app is not None:
        await telegram_app.initialize()
        await telegram_app.start()
        if not settings.webhook_base_url:
            raise RuntimeError('WEBHOOK_BASE_URL is required in production')
        webhook_url = settings.webhook_base_url.rstrip('/') + '/telegram/webhook'
        await telegram_app.bot.set_webhook(
            url=webhook_url,
            secret_token=settings.telegram_webhook_secret or None,
            drop_pending_updates=False,
        )
        log.info('Telegram webhook registered at %s', webhook_url)
    try:
        yield
    finally:
        if telegram_app is not None:
            await telegram_app.stop()
            await telegram_app.shutdown()

app = FastAPI(title='IntelKit', version='1.0.0', lifespan=lifespan)
app.include_router(health_router(manager))
if telegram_app is not None:
    app.include_router(webhook_router(telegram_app, settings.telegram_webhook_secret))

@app.get('/')
async def root():
    if not settings.telegram_bot_token:
        telegram_status = 'missing TELEGRAM_BOT_TOKEN'
    elif settings.app_env == 'production':
        telegram_status = 'webhook active' if telegram_app is not None else 'webhook unavailable'
    else:
        telegram_status = 'configured for local polling'
    return {
        'name': 'IntelKit',
        'tagline': 'AI-Powered Content Intelligence',
        'environment': settings.app_env,
        'telegram': telegram_status,
    }
