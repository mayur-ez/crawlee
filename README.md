# Crawlee

A Python web crawler built on the [Crawlee](https://crawlee.dev/python/) framework. Recursively scrapes websites, extracts content, and saves HTML locally.

## Features

- **Interactive URL input** — enter URLs manually, load from a custom file, or use the built-in defaults
- **Recursive crawling** — automatically discovers and follows all links on each page
- **HTML persistence** — saves every crawled page to the `html/` directory
- **Parallel execution** — leverages Crawlee's auto-scaling concurrency
- **Automatic retries** — handles failures with configurable retry policy (default: 3)
- **Extensible** — includes stubs for MongoDB and Beanstalkd queue integration

## Quick start

```bash
# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the crawler
python crawler.py
```

Follow the interactive menu to choose seed URLs, then watch the crawler discover pages and save HTML to the `html/` directory.

## Project structure

```
├── crawler.py              # Main entry point
├── config.py               # URL selection menu
├── handlers.py             # Request handler (extract title, save HTML, enqueue links)
├── beanstalk_queue.py      # Beanstalkd integration (stub)
├── mongo.py                # MongoDB integration (stub)
├── requirements.txt        # Python dependencies
├── assets/
│   └── domain_list.txt     # Default seed URLs
├── html/                   # Crawled HTML output
└── storage/                # Crawlee persistent storage
```

## Dependencies

- [Crawlee](https://crawlee.dev/python/) — web crawling framework
- BeautifulSoup4 + lxml — HTML parsing
- Pydantic — data validation
- pymongo — MongoDB client (optional)
- pystalk — Beanstalkd client (optional)

See `requirements.txt` for the full pinned list.
