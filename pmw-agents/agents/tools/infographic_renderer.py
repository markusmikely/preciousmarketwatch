# agents/tools/infographic_renderer.py

def render_comparison_svg(items: list, title: str) -> str:
    """
    Generates a clean comparison table as SVG.
    items: [{"name": str, "score": float, "pros": [str], "link": str}]
    Returns SVG string ready for WordPress upload.
    """
    # PMW brand colours
    GOLD   = "#C9A84C"
    DARK   = "#1A1A2E"
    LIGHT  = "#F5F5F0"
    TEXT   = "#2D2D2D"

    width  = 800
    row_h  = 80
    height = 120 + (len(items) * row_h)

    rows_svg = ""
    for i, item in enumerate(items):
        y    = 120 + (i * row_h)
        bg   = LIGHT if i % 2 == 0 else "#EBEBE6"
        star = "★" * round(item.get("score", 3)) + "☆" * (5 - round(item.get("score", 3)))
        rows_svg += f"""
        <rect x="0" y="{y}" width="{width}" height="{row_h}" fill="{bg}"/>
        <text x="20"  y="{y+50}" font-size="16" fill="{TEXT}" font-weight="bold">{item['name']}</text>
        <text x="300" y="{y+50}" font-size="14" fill="{GOLD}">{star}</text>
        <text x="500" y="{y+50}" font-size="13" fill="{TEXT}">{item.get('highlight','')}</text>
        """

    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
    <rect width="{width}" height="{height}" fill="{DARK}" rx="12"/>
    <text x="{width//2}" y="60" text-anchor="middle" font-size="22" fill="{GOLD}" font-weight="bold">{title}</text>
    <text x="{width//2}" y="90" text-anchor="middle" font-size="13" fill="{LIGHT}">PreciousMarketWatch.com</text>
    {rows_svg}
    </svg>"""