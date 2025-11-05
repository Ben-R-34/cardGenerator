import json, pathlib, asyncio, base64
from jinja2 import Template
from playwright.async_api import async_playwright

root = pathlib.Path(__file__).parent

# Load data.json (utf-8 with BOM fallback)
raw = (root/"data.json").read_bytes()
try:
    text = raw.decode("utf-8")
except UnicodeDecodeError:
    text = raw.decode("utf-8-sig", errors="ignore")
cards = json.loads(text)

def render(template_file, **ctx):
    tpl = Template((root/template_file).read_text(encoding="utf-8"))
    return tpl.render(**ctx)

# Inline icon for non-leader backs
icon_bytes = (root/"assets/Project_Conquer.png").read_bytes()
ICON_DATA_URL = "data:image/png;base64," + base64.b64encode(icon_bytes).decode("ascii")

PAGE_SIZE = 70        # <-- 70 cards per PNG
COLS = 10             # 10 columns × 7 rows

BLANK = {
    "name": "", "text": "", "aspect": "", "rarity": "",
    "type": [], "cost": "", "power": None, "toughness": None,
    "orientation": "portrait", "has_back": False, "is_placeholder": True
}

def chunk(lst, n):
    for i in range(0, len(lst), n):
        yield lst[i:i+n]

async def build_pngs():
    pages = list(chunk(cards, PAGE_SIZE))
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()

        for i, subset in enumerate(pages, start=1):
            # >>> pad to 70 <<<
            pad = PAGE_SIZE - len(subset)
            if pad > 0:
                subset = subset + [BLANK.copy() for _ in range(pad)]
            
            # FRONTS
            front_html = render("template_fronts.html", cards=subset, cols=COLS)
            await page.set_content(front_html, wait_until="networkidle")
            await page.screenshot(path=str(root/f"cards_fronts_p{i:02d}.png"), full_page=True)

            # BACKS (same subset & order)
            back_html = render("template_back.html", cards=subset, cols=COLS, icon_data_url=ICON_DATA_URL)
            await page.set_content(back_html, wait_until="networkidle")
            await page.screenshot(path=str(root/f"cards_backs_p{i:02d}.png"), full_page=True)

            print(f"✅ Sheet {i}: {len(subset)} cards")
        await browser.close()

if __name__ == "__main__":
    asyncio.run(build_pngs())
