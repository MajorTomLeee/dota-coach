import logging
import httpx

log = logging.getLogger(__name__)

async def send_feishu_text(webhook_url: str, title: str, content: str) -> bool:
    body = {
        "msg_type": "post",
        "content": {
            "post": {
                "zh_cn": {
                    "title": title,
                    "content": [[{"tag": "text", "text": content}]],
                }
            }
        },
    }
    async with httpx.AsyncClient(timeout=10) as client:
        try:
            r = await client.post(webhook_url, json=body)
            r.raise_for_status()
            return True
        except Exception as e:
            log.warning("feishu push failed: %s", e)
            return False
