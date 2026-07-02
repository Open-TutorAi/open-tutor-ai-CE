"""YouTube search router — scrapes YouTube to return real video IDs."""
import re
import requests
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

router = APIRouter(tags=["youtube"])

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7",
}


@router.get("/youtube/search")
async def search_youtube_videos(q: str = Query(..., min_length=1, max_length=200)):
    """Search YouTube and return the first 5 real video IDs for a given query."""
    try:
        url = f"https://www.youtube.com/results?search_query={requests.utils.quote(q)}&sp=EgIQAQ%3D%3D"
        # sp=EgIQAQ%3D%3D filters for videos only (not playlists/channels)
        resp = requests.get(url, headers=HEADERS, timeout=8)
        resp.raise_for_status()

        # Extract video IDs from the page source
        ids = re.findall(r'"videoId":"([a-zA-Z0-9_-]{11})"', resp.text)
        # Deduplicate while preserving order
        seen = set()
        unique_ids = []
        for vid in ids:
            if vid not in seen:
                seen.add(vid)
                unique_ids.append(vid)
            if len(unique_ids) >= 5:
                break

        if not unique_ids:
            return JSONResponse({"error": "No videos found", "videos": []}, status_code=404)

        return JSONResponse({"videos": unique_ids, "query": q})

    except requests.exceptions.Timeout:
        return JSONResponse({"error": "YouTube request timed out", "videos": []}, status_code=504)
    except Exception as e:
        return JSONResponse({"error": str(e), "videos": []}, status_code=500)
