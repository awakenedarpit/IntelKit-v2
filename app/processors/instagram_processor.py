import re, httpx
from pathlib import Path
IG_RE=re.compile(r"https?://(?:www\.)?instagram\.com/(reel|p|tv)/[^/?#]+",re.I)
def _meta_content(html, property_name):
    for tag in re.findall(r'<meta\b[^>]*>', html, re.I):
        prop=re.search(r'(?:property|name)=["\']([^"\']+)', tag, re.I)
        content=re.search(r'content=["\']([^"\']*)', tag, re.I)
        if prop and content and prop.group(1).lower() == property_name.lower():
            return content.group(1).replace('&amp;', '&')
    return None

def classify(url):
    m=IG_RE.fullmatch(url.strip().rstrip('/'))
    return m.group(1).lower() if m else None
async def retrieve(url, workspace):
    kind=classify(url)
    if not kind: raise ValueError('Unsupported Instagram URL. Send a public /reel/, /p/, or /tv/ link.')
    async with httpx.AsyncClient(follow_redirects=True,timeout=20,headers={'User-Agent':'IntelKit/1.0'}) as c: r=await c.get(url)
    if r.status_code!=200: raise RuntimeError('Instagram content could not be retrieved publicly. Please upload the media directly.')
    # Public metadata is best-effort and never bypasses access controls.
    caption=_meta_content(r.text, 'og:description') or ''
    media_url=_meta_content(r.text, 'og:video') if kind in ('reel', 'tv') else None
    media_url=media_url or _meta_content(r.text, 'og:image')
    if not media_url: raise RuntimeError('Instagram media was not publicly retrievable. Please upload it directly.')
    data=await c.get(media_url)
    if data.status_code != 200 or not data.content:
        raise RuntimeError('Instagram media download was blocked. Please upload it directly.')
    content_type=data.headers.get('content-type','').lower()
    suffix='.mp4' if 'video' in content_type or kind in ('reel','tv') and media_url.lower().split('?')[0].endswith(('.mp4','.m4v')) else '.jpg'
    p=Path(workspace)/('instagram'+suffix); p.write_bytes(data.content); return kind,p,caption
