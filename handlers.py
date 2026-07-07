from pathlib import Path

from crawlee.crawlers import BeautifulSoupCrawlingContext


HTML_DIR = Path("html")
HTML_DIR.mkdir(exist_ok=True)


async def default_handler(context: BeautifulSoupCrawlingContext):

    soup = context.soup

    context.log.info(f"Visiting : {context.request.url}")

    title = soup.select_one("title").text

    context.log.info(f"Title : {title}")

    await save_html(context)

    await context.enqueue_links()


async def save_html(context: BeautifulSoupCrawlingContext):

    url = context.request.url

    filename = (
        url.replace("https://", "")
        .replace("http://", "")
        .replace("/", "_")
    )

    path = HTML_DIR / f"{filename}.html"

    path.write_text(
        str(context.soup),
        encoding="utf-8"
    )