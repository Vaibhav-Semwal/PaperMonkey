import os
import redis
import json
from django.utils import timezone
from asgiref.sync import sync_to_async, async_to_sync
from langchain_core.documents import Document
from .models import CrawledPage, CrawledLink
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(host= os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB_INDEX"), decode_responses=True)

CACHE_TTL = 60  # 1 hour

#region HELPERS FUNCTIONS

async def fetch_page(url: str): 

    print("entered fetch_page")      
    # Redis cache hit 
    cached = await get_from_redis(url)
    if cached:
        print(f"[REDIS HIT] {url}")
        return [Document(
            page_content=cached["html_content"],
            metadata={"source": url}
        )]
    print(f"[REDIS MISS] {url}")

    # DB hit and warm Redis  
    already_crawled = await is_already_crawled(url)

    if already_crawled:
        print(f"[DB HIT] {url}")
        page = await CrawledPage.objects.aget(url=url)
        data = {
            "html_content": page.html_content,
            "title": page.title,
            "status_code": page.status_code,
        }
        await set_in_redis(url, data)
        return [Document(
            page_content=page.html_content,
            metadata={"source": url}
        )]
    print(f"[DB MISS] {url}")
    return None

def _get_from_redis(url: str):
    cached = r.get(f"page:{url}")
    return json.loads(cached) if cached else None

def _set_in_redis(url: str, data: dict):
    r.setex(f"page:{url}", CACHE_TTL, json.dumps(data))

def _save_crawled_page_sync(data: dict) -> CrawledPage:
    page, created = CrawledPage.objects.update_or_create(
        url=data["url"],
        defaults={
            "title": data.get("title", ""),
            "html_content": data.get("html_content", ""),
            "status_code": data.get("status_code", 200),
            "etag": data.get("etag", ""),
            "content_type": data.get("content_type", ""),
            "updated_at": timezone.now(),
        }
    )

    links = data.get("links", [])

    if links:
        CrawledLink.objects.filter(source_page=page).delete()
        CrawledLink.objects.bulk_create([
            CrawledLink(source_page=page, target_url=link)
            for link in set(links)
        ], ignore_conflicts=True)

    print(f"[{'Created' if created else 'Updated'}] {data['url']}")
    return page

#endregion

# Async-safe wrappers 
save_crawled_page = sync_to_async(_save_crawled_page_sync)
is_already_crawled = sync_to_async(
    lambda url: CrawledPage.objects.filter(url=url).exists()
)
get_from_redis = sync_to_async(_get_from_redis)
set_in_redis   = sync_to_async(_set_in_redis)