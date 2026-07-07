import asyncio
from crawlee.crawlers import BeautifulSoupCrawler
from config import get_seed_urls
from handlers import default_handler


async def main():

    seed_urls = get_seed_urls()

    if not seed_urls:
        print("No URLs Found.")
        return

    crawler = BeautifulSoupCrawler()

    crawler.router.default_handler(default_handler)

    await crawler.run(seed_urls)


if __name__ == "__main__":
    asyncio.run(main())