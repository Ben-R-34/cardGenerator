import json, pathlib, asyncio
from jinja2 import Template
from playwright.async_api import async_playwright
import base64

root = pathlib.Path(__file__).parent
cards = json.loads((root/"data.json").read_text(encoding="utf-8"))

def render_html(template_name, **ctx):
    tmpl = Template((root/template_name).read_text(encoding="utf-8"))
    return tmpl.render(**ctx)

async def html_to_pdf(html_str, out_path):
    out_path = str(out_path)
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        # Load HTML via data URL so assets resolve via base tag
        await page.set_content(html_str, wait_until="load")
        await page.pdf(path=out_path, print_background=True)
        await browser.close()

base = root.as_uri()  # e.g., file:///C:/Users/kopfb/Desktop/cardGenerator

front_html = render_html("template_fronts.html", cards=cards, base_href=base)
back_html  = render_html("template_back.html",  cards=cards, base_href=base)


asyncio.run(html_to_pdf(front_html, root/"cards_fronts.pdf"))
asyncio.run(html_to_pdf(back_html,  root/"cards_backs.pdf"))
print("Wrote cards_fronts.pdf and cards_backs.pdf")

