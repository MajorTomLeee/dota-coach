import asyncio
import logging

import httpx

log = logging.getLogger(__name__)
BASE = "https://api.opendota.com/api"


class OpenDotaClient:
    def __init__(self, timeout: float = 15.0, max_retries: int = 3):
        self._client = httpx.AsyncClient(timeout=timeout)
        self.max_retries = max_retries

    async def _get(self, path: str) -> dict | list:
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                r = await self._client.get(f"{BASE}{path}")
                r.raise_for_status()
                return r.json()
            except (httpx.HTTPError, httpx.TimeoutException) as e:
                last_exc = e
                await asyncio.sleep(2 ** attempt)
        raise RuntimeError(f"OpenDota GET {path} failed after retries: {last_exc}")

    async def recent_matches(self, account_id: int) -> list[dict]:
        return await self._get(f"/players/{account_id}/recentMatches")

    async def match(self, match_id: int) -> dict:
        return await self._get(f"/matches/{match_id}")

    async def parse_request(self, match_id: int) -> dict:
        # 触发 OpenDota 解析回放（可选）
        r = await self._client.post(f"{BASE}/request/{match_id}")
        r.raise_for_status()
        return r.json()

    async def close(self) -> None:
        await self._client.aclose()
