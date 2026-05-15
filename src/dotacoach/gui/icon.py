from PIL import Image, ImageDraw


def make_tray_icon(status: str = "idle", size: int = 64) -> Image.Image:
    """生成程序内置的托盘图标，避免打包 PNG 资源。

    status: "idle"（灰）/ "online"（橙）/ "paused"（半透）/ "warn"（红）
    """
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    color_map = {
        "idle": (110, 110, 110, 255),
        "online": (249, 115, 22, 255),
        "paused": (110, 110, 110, 180),
        "warn": (239, 68, 68, 255),
    }
    fill = color_map.get(status, color_map["idle"])
    pad = max(2, size // 12)
    d.ellipse((pad, pad, size - pad, size - pad), fill=fill)
    # 中间 "D" 字
    try:
        from PIL import ImageFont
        font = ImageFont.load_default()
    except Exception:
        font = None
    text = "D"
    if font:
        bbox = d.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        d.text(
            ((size - tw) / 2, (size - th) / 2 - 2),
            text, fill=(255, 255, 255, 255), font=font,
        )
    return img
