"""Consultas asincronas a YouTube Data API v3."""
from dataclasses import dataclass
import aiohttp

class YouTubeAPIError(RuntimeError): pass

@dataclass(frozen=True)
class Video:
    video_id: str; title: str; published_at: str | None; thumbnail_url: str | None
    @property
    def url(self): return f"https://www.youtube.com/watch?v={self.video_id}"

class YouTubeClient:
    def __init__(self, key: str, handle: str):
        self.key, self.handle, self.channel_id, self.uploads_id = key, handle, None, None
    async def _get(self, endpoint: str, **params):
        params["key"] = self.key
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=20)) as session:
                async with session.get(f"https://www.googleapis.com/youtube/v3/{endpoint}", params=params) as response:
                    data = await response.json(content_type=None)
                    if response.status != 200: raise YouTubeAPIError(data.get("error", {}).get("message", f"Error HTTP {response.status}"))
                    return data
        except aiohttp.ClientError as error: raise YouTubeAPIError("No se pudo conectar con YouTube.") from error
    async def _channel(self):
        if self.channel_id: return
        data = await self._get("channels", part="id,contentDetails", forHandle=self.handle)
        if not data.get("items"): raise YouTubeAPIError(f"No se encontro @{self.handle}.")
        item = data["items"][0]; self.channel_id = item["id"]; self.uploads_id = item["contentDetails"]["relatedPlaylists"]["uploads"]
    async def latest_video(self):
        await self._channel(); data = await self._get("playlistItems", part="snippet,contentDetails", playlistId=self.uploads_id, maxResults="1")
        if not data.get("items"): raise YouTubeAPIError("El canal no tiene videos publicos.")
        item = data["items"][0]; snippet = item["snippet"]; thumbs = snippet.get("thumbnails", {}); image = thumbs.get("maxres") or thumbs.get("high") or thumbs.get("medium") or thumbs.get("default")
        return Video(item["contentDetails"]["videoId"], snippet["title"], snippet.get("publishedAt"), image.get("url") if image else None)
    async def stats(self):
        await self._channel(); data = await self._get("channels", part="snippet,statistics", id=self.channel_id); item = data.get("items", [None])[0]
        if not item: raise YouTubeAPIError("No se pudieron obtener estadisticas.")
        stat = item["statistics"]
        return item["snippet"]["title"], (None if stat.get("hiddenSubscriberCount") else int(stat["subscriberCount"])), int(stat["videoCount"]), int(stat["viewCount"])
