import logging
import asyncio
import shutil
import tempfile
from pathlib import Path
from telegram import Update
from telegram.ext import ContextTypes
from app.utils.cleanup import temporary_workspace
from app.processors.image_processor import process as process_image
from app.processors.video_processor import process as process_video
from app.processors.carousel_processor import process as process_carousel
from app.processors.instagram_processor import retrieve

log = logging.getLogger(__name__)

async def send_report(message, report):
    limit = 3900
    for start in range(0, len(report), limit):
        await message.reply_text(report[start:start + limit])

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Welcome to IntelKit — AI-Powered Content Intelligence. Send a public Instagram link, image, album, or video and I will extract the useful signal.')

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Supported: public Instagram /reel/, /p/, /tv/ links, images, albums, and videos. Private or blocked Instagram content must be uploaded directly.')

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    manager = context.application.bot_data['manager']
    s = manager.status()
    await update.message.reply_text('IntelKit status: running\nProviders: ' + ', '.join(f'{k}={"configured" if v else "not configured"}' for k, v in s.items()))

async def _download(update: Update, context: ContextTypes.DEFAULT_TYPE, workspace: Path):
    media = update.message.photo[-1] if update.message.photo else update.message.video
    tg_file = await context.bot.get_file(media.file_id)
    suffix = '.jpg' if update.message.photo else '.mp4'
    target = workspace / f'upload-{media.file_id}{suffix}'
    await tg_file.download_to_drive(target)
    return target

async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.media_group_id:
        await _album_photo(update, context)
        return
    await update.message.reply_text('Analyzing image…')
    try:
        with temporary_workspace() as workspace:
            path = await _download(update, context, workspace)
            report = await process_image(path, context.application.bot_data['extractor'])
        await send_report(update.message, report)
    except Exception as exc:
        log.warning('image processing failed: %s', exc)
        await update.message.reply_text('I could not analyze that image. Please try again or send a clearer upload.')

async def _album_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    albums = context.application.bot_data.setdefault('albums', {})
    group_id = update.message.media_group_id
    entry = albums.setdefault(group_id, {'paths': [], 'task': None, 'chat_id': update.effective_chat.id})
    folder = Path(entry.setdefault('folder', tempfile.mkdtemp(prefix='intelkit-album-')))
    path = await _download(update, context, folder)
    entry['paths'].append(path)
    if entry['task'] is None:
        entry['task'] = context.application.create_task(_finish_album(group_id, context))

async def _finish_album(group_id, context):
    await asyncio.sleep(1.5)
    albums = context.application.bot_data.get('albums', {})
    entry = albums.pop(group_id, None)
    if not entry:
        return
    try:
        report = await process_carousel(sorted(entry['paths']), context.application.bot_data['extractor'])
        for start in range(0, len(report), 3900):
            await context.bot.send_message(entry['chat_id'], report[start:start + 3900])
    except Exception as exc:
        log.warning('carousel processing failed: %s', exc)
        await context.bot.send_message(entry['chat_id'], 'I could not analyze that album. Please try sending the slides again.')
    finally:
        shutil.rmtree(entry['folder'], ignore_errors=True)

async def video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Processing video frames and audio…')
    try:
        with temporary_workspace() as workspace:
            path = await _download(update, context, workspace)
            report = await process_video(path, context.application.bot_data['extractor'], workspace)
        await send_report(update.message, report)
    except Exception as exc:
        log.warning('video processing failed: %s', exc)
        await update.message.reply_text('I could not process that video within the configured limits.')

async def text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    value = (update.message.text or '').strip()
    if value.startswith(('https://instagram.com/', 'https://www.instagram.com/')):
        await update.message.reply_text('Retrieving public Instagram metadata…')
        try:
            with temporary_workspace() as workspace:
                kind, path, caption = await retrieve(value, workspace)
                if path.suffix.lower() in ('.mp4', '.m4v'):
                    report = await process_video(path, context.application.bot_data['extractor'], workspace, caption)
                else:
                    report = await process_image(path, context.application.bot_data['extractor'], caption)
            await send_report(update.message, report)
        except Exception as exc:
            log.info('Instagram retrieval unavailable: %s', exc)
            await update.message.reply_text('That Instagram post could not be retrieved publicly. Please upload the image or video directly.')
    else:
        await update.message.reply_text('Send a public Instagram link, image, album, or video for analysis.')
