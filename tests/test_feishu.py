import httpx
import respx
from dotacoach.notify.feishu import send_feishu_text

@respx.mock
async def test_post_text():
    route = respx.post("https://example.com/hook").mock(
        return_value=httpx.Response(200, json={"code": 0})
    )
    ok = await send_feishu_text("https://example.com/hook", "title", "body")
    assert ok is True
    assert route.called
