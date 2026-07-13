# V7 Python Distributed Web Crawler - Complete Project Explanation

## What Is This Project? (The Big Picture)

Imagine you have a **super-robot** whose job is to visit thousands of websites, download their pages (like saving web pages as files), and then send those pages to **specialist robots** who read them and extract useful information (like titles, descriptions, images, links, etc.).

This project is that super-robot system. It's called a **Distributed Web Crawler** and it:
1. Takes a list of website domains (like `example.com`, `google.com`)
2. Visits every page on those websites
3. Saves the raw HTML of each page
4. Sends each saved page to 16 different "parser workers" who extract specific data from the HTML
5. Stores everything in a database (MongoDB)
6. Can do all of this across multiple machines/containers at the same time (that's the "distributed" part)

---

## The 5 Big Technologies Used

| Technology | What It Does (Like a Child Would Say) |
|---|---|
| **Scrapy** | A Python framework that knows how to visit websites, follow links, and download pages. It's the "spider" that crawls the web. |
| **Beanstalkd** | A "to-do list" system. When you have thousands of jobs, you put them in Beanstalkd, and workers pick them up one by one. |
| **MongoDB** | A database that stores all the crawl jobs, downloaded HTML info, and parsed results. |
| **Playwright** | A tool that opens a real browser (like Chrome) to render JavaScript-heavy websites so we can get the full page content. |
| **Bunny CDN** | A cloud file storage service where the saved HTML files get uploaded for permanent storage. |

---

## How The Whole System Works (Step by Step)

### Step 1: You Submit a Crawl Job
You run a command like:
```bash
python scripts/submit_crawl_job.py --domain example.com --max-pages 500 --use-sitemap
```
This creates a "job" (a JSON message) and puts it into Beanstalkd (the to-do list queue).

### Step 2: Queue Listener Picks Up the Job
A worker called `crawl_job_listener.py` is always sitting and waiting. When a job appears in the queue, it grabs it and tells Scrapy to start crawling.

### Step 3: Scrapy Spider Crawls the Website
Scrapy launches a "spider" (like `domain_spider.py`) that:
- Visits the starting URL
- Finds all links on the page
- Follows those links to find more pages
- Keeps going until it has visited `max-pages` pages (or exhausts all links)
- Can optionally use sitemaps (XML files that list all pages on a website)

### Step 4: HTML Gets Saved
As each page is crawled, it goes through Scrapy's **pipelines** (a chain of processing steps):
1. **HTML Storage Pipeline** - Saves the raw HTML file to disk (organized by domain name)
2. **Bunny CDN Pipeline** - Uploads the HTML file to Bunny CDN cloud storage
3. **Parser Trigger Pipeline** - Creates a "parse job" in MongoDB and dispatches it to Beanstalkd

### Step 5: Parser Workers Extract Data
There are **16 different parser workers**, each specialized in extracting one type of data:
- `page_title_worker.py` - Extracts the page title (`<title>` tag)
- `meta_description_worker.py` - Extracts meta descriptions
- `headings_worker.py` - Extracts H1, H2, H3, etc. headings
- `links_worker.py` - Extracts all internal and external links
- `images_worker.py` - Extracts all images with alt text
- `canonical_worker.py` - Extracts canonical URLs
- `javascript_worker.py` - Detects JavaScript frameworks and scripts
- `google_analytics_worker.py` - Detects Google Analytics, GTM, etc.
- `structured_worker.py` - Extracts JSON-LD, Schema.org structured data
- `mobile_worker.py` - Checks mobile-friendliness signals
- `hreflang_worker.py` - Extracts language/region tags
- `directives_worker.py` - Extracts robots meta, X-Robots-Tag headers
- `uri_worker.py` - Analyzes URL structure and components
- `page_elements_worker.py` - Counts images, forms, scripts, stylesheets
- `third_party_services_worker.py` - Detects third-party integrations
- `amp_worker.py` - Checks for AMP (Accelerated Mobile Pages)

Each parser reads the HTML from disk, extracts its specific data, and saves the results to MongoDB.

### Step 6: Completion Monitor
A worker called `parser_completion_monitor.py` watches and counts how many parsers have finished for each page. When all 16 parsers are done, it marks that page as "complete."

### Step 7: Downstream Sync (Optional)
If enabled, a `downstream_sync_worker.py` takes the parsed data and syncs it to an external PHP database for the frontend/dashboard to display.

---

## Complete File/Folder Breakdown

### Root Level Files

| File | What It Does |
|---|---|
| `README.md` | Project documentation and quickstart guide |
| `requirements.txt` | Python packages needed (Scrapy, pymongo, greenstalk, playwright, etc.) |
| `setup.py` | Makes this project installable as a Python package |
| `scrapy.cfg` | Scrapy configuration - tells Scrapy where to find the spider project |
| `.env.example` | Template for environment variables (copy to `.env` and fill in) |
| `.env` | Actual environment variables (not in git, contains secrets) |
| `.gitignore` | Tells git which files to ignore |
| `.dockerignore` | Tells Docker which files to ignore when building |
| `Dockerfile` | Instructions for building the Docker container image |
| `docker-compose.yml` | Defines 2 crawler containers (crawler1, crawler2) that run simultaneously |
| `import_domains_*.csv` | CSV files with domain lists to import for crawling |

---

### `config/` - Configuration Files

This is the **brain** of the system. All settings live here.

| File | What It Does |
|---|---|
| `base_settings.py` | **Central config hub** - defines ALL settings: file paths, MongoDB connection, Beanstalkd queue settings, worker counts, Bunny CDN config, monitoring thresholds. Loads from `.env` file. |
| `logging_config.py` | Sets up logging for every component - creates log files with rotation (10MB max, 10 backups), timestamps, process IDs. Has a `LogOperation` context manager that auto-logs start/end times. |
| `parser_settings.py` | Defines all 16 parser task types, their priorities, timeouts, instance counts, and Beanstalkd tube names. |
| `proxy_list.json` | List of HTTP proxy servers for rotating IPs while crawling. |

**Key settings you should know:**
- `CRAWLER_INSTANCES=6` - How many crawler workers run simultaneously
- `QUEUE_TTR=300` - Time-to-run: a job must finish in 300 seconds or it goes back to queue
- `MONGO_DB=v7_crawler_db` - The MongoDB database name
- `QUEUE_CRAWL_TUBE=v7_crawler_crawl_jobs` - The Beanstalkd tube (queue channel) for crawl jobs

---

### `crawler/` - The Scrapy Crawling Engine

This is the **heart** of the system. It's a full Scrapy project.

#### `crawler/spider_project/spiders/` - The Spiders (5 files)

| Spider | What It Does |
|---|---|
| `base_spider.py` | Parent class for all spiders. Contains shared logic: request signing, proxy rotation, user-agent rotation, error handling, callback handling. |
| `domain_spider.py` | Crawls an ENTIRE domain. Follows links, respects `max-pages` limit, uses sitemaps. This is the most commonly used spider. |
| `url_spider.py` | Crawls a SINGLE specific URL (and optionally its subpages). Used when you only need one page, not the whole site. |
| `js_domain_spider.py` | Like `domain_spider` but uses Playwright (real browser) to render JavaScript. For SPAs (Single Page Applications) and sites that load content dynamically. |
| `__init__.py` | Empty file (makes it a Python package) |

#### `crawler/spider_project/pipelines/` - Data Processing Pipelines (4 files)

When Scrapy scrapes a page, the data flows through these pipelines in order:

| Pipeline | What It Does |
|---|---|
| `html_storage_pipeline.py` | Saves the raw HTML to disk under `data/html/{domain}/` with a unique filename based on the URL. Uses file locking for safety. |
| `bunny_cdn_pipeline.py` | Uploads the HTML file to Bunny CDN cloud storage. Has retry logic and exponential backoff. |
| `parser_trigger_pipeline.py` | Creates a parse job document in MongoDB's `parsed_html_data` collection, then dispatches individual parser tasks to Beanstalkd tubes (one per parser type). This is the bridge between crawling and parsing. |
| `stats_pipeline.py` | Updates crawl statistics in MongoDB - tracks pages crawled, errors, timing. |

#### `crawler/spider_project/middlewares/` - Request/Response Middlewares (7 files)

| Middleware | What It Does |
|---|---|
| `enhanced_ua_rotation.py` | Rotates User-Agent headers from a pool of 50+ realistic browser headers. Makes the crawler look like different real browsers. |
| `basic_ua_middleware.py` | Simpler User-Agent rotation (fallback option). |
| `proxy_middleware.py` | Routes requests through proxy servers from `proxy_list.json`. Rotates proxies and handles failures. |
| `content_filter_middleware.py` | Filters out unwanted content types (images, PDFs, videos, etc.) to only crawl HTML pages. |
| `retry_middleware.py` | Retries failed requests with smart strategies. Detects anti-bot challenges (Cloudflare, Akamai, etc.) and can abort or retry. |
| `redirect_middleware.py` | Handles HTTP redirects (301, 302) and tracks redirect chains. |
| `stats_middleware.py` | Collects timing and response statistics for monitoring. |

#### Other crawler files

| File | What It Does |
|---|---|
| `crawler/spider_project/settings.py` | Scrapy settings - tells Scrapy which pipelines, middlewares, and spider classes to use, concurrent request limits, timeouts, etc. |
| `crawler/spider_project/items.py` | Defines the data structure (Scrapy Items) for crawled pages - fields like URL, HTML content, status code, headers, etc. |
| `crawler/listener/crawl_job_listener.py` | Waits for crawl jobs on Beanstalkd, then launches the appropriate Scrapy spider. This is the bridge between the queue and Scrapy. |
| `crawler/listener/crawl_processor.py` | Handles the actual crawling logic - builds Scrapy's `CrawlCommand` with the right settings and starts the spider. |
| `crawler/listener/content_job_listener.py` | Listens for content verification jobs (checking if specific content exists on a page). |
| `crawler/listener/project_job_listener.py` | Listens for project-level jobs (multi-domain batch crawls). |
| `crawler/listener/parser_completion_monitor.py` | Watches parsed pages and counts how many parsers have completed. Marks pages as fully parsed when all 16 are done. |
| `crawler/broadcasting/crawl_broadcaster.py` | Broadcasts crawl events to downstream services (optional feature). |
| `crawler/scripts/domain_crawl_job_submitter.py` | Script to submit domain crawl jobs from CSV files. |
| `crawler/scripts/single_job_submitter.py` | Script to submit a single URL crawl job. |

---

### `parser/` - HTML Parser Workers

This is the **data extraction** layer. Each worker reads saved HTML and extracts specific information.

#### `parser/workers/` - 20 files

| Worker | What It Extracts |
|---|---|
| `base_parser_worker.py` | Parent class for ALL parser workers. Handles Beanstalkd job reservation, MongoDB updates, error handling, retry logic. Every parser inherits from this. |
| `page_title_worker.py` | Extracts `<title>` tag content |
| `meta_description_worker.py` | Extracts `<meta name="description">` content |
| `headings_worker.py` | Extracts all `<h1>` through `<h6>` headings |
| `canonical_worker.py` | Extracts `<link rel="canonical">` URL |
| `directives_worker.py` | Extracts `<meta name="robots">`, X-Robots-Tag headers |
| `google_analytics_worker.py` | Detects GA4, Universal Analytics, GTM, Google Tag Manager |
| `hreflang_worker.py` | Extracts `<link rel="alternate" hreflang="...">` tags |
| `images_worker.py` | Extracts all `<img>` tags with src, alt, width, height |
| `javascript_worker.py` | Detects JS frameworks (React, Vue, Angular, jQuery, etc.) |
| `links_worker.py` | Extracts all `<a href>` links, categorizes as internal/external |
| `mobile_worker.py` | Checks viewport meta tag, mobile-friendly signals |
| `page_elements_worker.py` | Counts forms, scripts, stylesheets, videos, iframes |
| `structured_worker.py` | Extracts JSON-LD, Microdata, RDFa structured data |
| `third_party_services_worker.py` | Detects Chatbots, analytics, ad networks, social widgets |
| `uri_worker.py` | Analyzes URL structure (protocol, subdomain, path depth, etc.) |
| `amp_worker.py` | Checks for AMP HTML version |
| `pagespeed_worker.py` | (Planned) Page speed analysis |
| `response_codes_worker.py` | (Planned) HTTP response code analysis |

#### `parser/dispatch/` - Parser Job Dispatch

| File | What It Does |
|---|---|
| `parser_dispatch.py` | Takes a parse job and dispatches it to all relevant parser Beanstalkd tubes. |

---

### `lib/` - Shared Libraries (Reusable Code)

This is the **toolbox** that all other components use.

#### `lib/queue/` - Beanstalkd Queue Management (3 files)

| File | What It Does |
|---|---|
| `beanstalkd_client.py` | Low-level wrapper around Beanstalkd (via `greenstalk` library). Handles connecting, reconnecting, putting/reserving/deleting jobs, and error handling. |
| `job_serializer.py` | Converts job dictionaries to JSON strings (and back) for transport through Beanstalkd. Adds metadata like version, timestamp, format. Validates job types. |
| `queue_manager.py` | High-level queue operations. Enqueue jobs with priority/delay, dequeue, mark complete, retry failed jobs, get stats. Manages job lifecycle. |

#### `lib/storage/` - Data Storage (3 files)

| File | What It Does |
|---|---|
| `mongodb_client.py` | MongoDB wrapper with connection pooling and retry logic. Supports find, insert, update, delete, count, create_index. Auto-reconnects on connection loss. |
| `mongodb_connection_manager.py` | Singleton pattern for managing multiple MongoDB connections (default DB + external PHP DB). |
| `file_storage.py` | Manages HTML files on disk. Generates file paths from URLs, writes with file locking, reads, deletes, lists files, cleans up old files. |

#### `lib/renderers/` - JavaScript Rendering (4 files)

| Renderer | What It Does |
|---|---|
| `base_renderer.py` | Abstract base class for all renderers. Defines the interface: `render(url)` returns `{html, status_code, headers, url, time, screenshot, error}`. Tracks statistics. |
| `splash_renderer.py` | Uses Splash (headless browser via HTTP API) to render JavaScript. Sends Lua scripts to navigate pages and wait for JS execution. |
| `selenium_renderer.py` | Uses Selenium WebDriver with Chrome/Firefox/Edge to render pages. Supports headless mode, proxies, custom user agents. |
| `puppeteer_renderer.py` | Uses Pyppeteer (Python Puppeteer) to control headless Chromium. Async/await based. |

#### `lib/utils/` - Utility Functions (10 files)

| File | What It Does |
|---|---|
| `url_processing.py` | URL normalization, fingerprinting (SHA-256 for dedup), domain extraction, media URL detection, URL validation, deduplication. |
| `proxy_manager.py` | Loads proxies from JSON, tracks success/failure rates per proxy, selects best proxy, supports per-domain proxy stats. |
| `health_check.py` | Checks system health: Beanstalkd connection, MongoDB connection, CPU/memory/disk usage, running process checks. Generates health reports. |
| `logging_utils.py` | Creates loggers with file rotation, console output, JSON formatting. Generates log file paths for every component. Has `LogOperation` context manager. |
| `sitemap_utils.py` | Parses XML sitemaps, extracts URLs, prioritizes URLs by freshness and priority scores, detects sitemap indexes. |
| `data_utils.py` | Safe type conversions for MongoDB (ObjectId, int, bool, datetime). Sanitizes data for MongoDB storage. |
| `extractor_base.py` | Base class for CSS/XPath data extraction using BeautifulSoup and Scrapy selectors. |
| `preflight_check.py` | Quick DNS + TCP check to see if a domain is reachable BEFORE committing crawl resources. |
| `site_level_checks.py` | Deep site analysis: robots.txt, sitemap.xml, SSL certificate inspection, custom 404 detection, www/non-www checks. |
| `state_abbreviations.py` | Geographic state/province abbreviation lookups (US, Canada, Australia). |

---

### `workers/` - System Orchestration (5 files)

| File | What It Does |
|---|---|
| `integration_service.py` | **The BOSS of the entire system.** Starts and monitors ALL worker processes. Checks health, restarts crashed workers, logs system status. This is the main process you start. |
| `worker_manager.py` | Manages individual worker processes - starts them, monitors them, restarts them on failure, tracks PIDs. |
| `monitor_worker.py` | Monitors the Beanstalkd queue and system health. Logs metrics. |
| `downstream_sync_worker.py` | Syncs parsed data from `v7_crawler_db` to the external PHP database (`v7_crawler_live`). |
| `downstream_sync_transformer.py` | Transforms data from the crawler's format to the format expected by the PHP system. |

---

### `scripts/` - CLI Tools and Utilities (14 files)

| Script | What It Does |
|---|---|
| `submit_crawl_job.py` (in crawler/) | Submits a crawl job to Beanstalkd. Supports domain mode and single-URL mode. |
| `domain_importer.py` | Imports domains from CSV/text files into MongoDB's `domains_crawl` collection. Normalizes domains, batch inserts. |
| `job_status.py` | Monitor jobs: list recent jobs, filter by status, search by ID, show full monitoring view. |
| `queue_status.py` | Monitor Beanstalkd queues: show all tube stats, peek at jobs, search by job ID. |
| `clear_jobs.py` | Clean up Beanstalkd jobs: list, clean all, delete specific job. |
| `clear_data.py` | NUCLEAR OPTION: Clears everything - MongoDB collections, Beanstalkd jobs, HTML files, logs. |
| `create_indexes.py` | Creates MongoDB indexes for optimal query performance on 3 collections. |
| `check_mongo.py` | Quick MongoDB connectivity check - ping, list collections, count documents. |
| `get_beanstalk_stats.py` | Dumps Beanstalkd server and per-tube statistics. |
| `submit_verification_job.py` | Submits content verification jobs (check if specific text/regex exists on a page). |
| `run_integration.sh` | Bash script to start the integration service. |
| `run_complete_crawl.sh` | End-to-end script: clean data, start workers, submit job, monitor, cleanup. |
| `restart_crawler.sh` | Docker-based restart with graceful/force/emergency modes. |
| `shutdown_crawler.py` | Graceful/force/emergency shutdown of all worker processes. |

---

## Data Flow Diagram (Text Version)

```
[You] --submit job--> [Beanstalkd Queue]
                            |
                    [Crawl Job Listener]
                            |
                    [Scrapy Spider Crawls Website]
                            |
                    [4 Pipelines Process Each Page]
                     /       |        \         \
              [Save HTML  [Upload  [Save to   [Update
               to Disk]   to CDN]  MongoDB]   Stats]
                            |
                    [Parser Trigger Pipeline]
                            |
                    [16 Parser Beanstalkd Tubes]
                     /   /   |   |   \   \
            [Title][Meta][Links][Images][JS]... (16 workers)
                     \   \   |   |   /   /
                    [Each saves results to MongoDB]
                            |
                    [Parser Completion Monitor]
                            |
                    [Marks page as "complete" when all 16 done]
                            |
                    [Downstream Sync Worker (optional)]
                            |
                    [External PHP Database]
```

---

## MongoDB Collections

| Collection | What It Stores |
|---|---|
| `crawl_jobs` | Crawl job definitions - domain, URL, max_pages, status, cycle_id, project_id, crawl parameters |
| `parsed_html_data` | Each crawled page's record - URL, HTML file path, processing status, parser results, completion count, sync status |
| `domains_crawl` | Domains to crawl - imported from CSV files, includes status, crawl parameters, project info |

---

## Beanstalkd Tubes (Queue Channels)

| Tube Name | What Goes In It |
|---|---|
| `v7_crawler_crawl_jobs` | Crawl jobs (domain or single URL) |
| `v7_crawl_project_jobs` | Project-level batch jobs |
| `v7_crawler_parser_completion_monitor` | Parser completion check jobs |
| `v7_html_parser_page_title_tube` | Page title parsing jobs |
| `v7_html_parser_meta_description_tube` | Meta description parsing jobs |
| `v7_html_parser_headings_tube` | Headings parsing jobs |
| `v7_html_parser_links_tube` | Links parsing jobs |
| `v7_html_parser_images_tube` | Images parsing jobs |
| ... (one tube per parser type) | ... |
| `v7_crawler_downstream_sync` | Downstream sync jobs |

---

## Docker Setup

The `docker-compose.yml` creates **2 crawler containers** (crawler1, crawler2) that:
- Share the same codebase via volume mount
- Have separate log directories (`shared_data/logs/c1` and `c2`)
- Share the same HTML storage (`shared_data/html`)
- Use `host` network mode (share the host machine's network)
- Get 4 CPU cores and 8GB RAM each
- Check health by connecting to Beanstalkd port 11300

The `Dockerfile` uses a multi-stage build:
1. **Builder stage**: Installs system dependencies and Python wheels
2. **Runtime stage**: Copies wheels, installs Playwright Chromium, runs as non-root user

---

## Key Concepts You Must Know

### What is a "Cycle"?
A cycle is a batch of domains to crawl together. When you import domains with a `cycle_id`, they all get crawled as part of that cycle.

### What is "TTR" (Time To Run)?
When a job is picked up from Beanstalkd, it has a timer (TTR). If the worker doesn't finish and "delete" the job before the timer expires, Beanstalkd puts the job back in the queue. This prevents stuck jobs.

### What is a "Tube"?
A tube is like a named queue channel in Beanstalkd. Different types of jobs go into different tubes so workers know what to pick up.

### What is "BFS Crawling"?
Breadth-First Search. The spider visits all links on the current page first, then moves to the next level. This ensures even coverage across the website.

### What is "Sitemap Crawling"?
Instead of following links randomly, the spider first fetches the website's `sitemap.xml` file which lists ALL pages. Then it systematically visits every page listed.

### What is "JS Rendering"?
Some websites load content with JavaScript (like React/Vue apps). Regular HTTP requests only get the empty HTML shell. JS rendering opens a real browser that executes JavaScript and waits for the full page to load.

### What is "Preflight Check"?
Before committing resources to crawl a domain, the system does a quick DNS + TCP check to see if the domain is reachable. Saves time on dead domains.

---

## How To Run The System

### Development (Manual)
```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Copy and edit .env
cp .env.example .env

# 3. Start the integration service (starts ALL workers)
./scripts/run_integration.sh

# 4. In another terminal, submit a crawl job
python scripts/submit_crawl_job.py --domain example.com --max-pages 100

# 5. Monitor progress
python scripts/job_status.py list
```

### Production (Docker)
```bash
# Start everything (MongoDB, Beanstalkd, Splash, 2 crawler containers)
docker-compose up --build

# Or restart with graceful shutdown
./scripts/restart_crawler.sh
```

---

## Common Senior Questions & Answers

**Q: How does the system handle duplicate URLs?**
A: `lib/utils/url_processing.py` has `url_fingerprint()` which generates SHA-256 hashes of normalized URLs. The `deduplicate_urls()` function removes duplicates before following links.

**Q: What happens if a worker crashes?**
A: The `integration_service.py` monitors all workers. If one crashes, `worker_manager.py` automatically restarts it. Jobs that were in-progress go back to the Beanstalkd queue due to TTR timeout.

**Q: How does proxy rotation work?**
A: `lib/utils/proxy_manager.py` loads proxies from `config/proxy_list.json`, tracks success/failure rates, and selects the best-performing proxy. The `proxy_middleware.py` applies proxies to Scrapy requests.

**Q: How do you add a new parser type?**
A: 1) Create a new worker in `parser/workers/`, 2) Add its config to `config/parser_settings.py`, 3) The `parser_trigger_pipeline.py` will automatically dispatch jobs to the new tube.

**Q: How does the system prevent getting blocked by websites?**
A: Multiple strategies: 50+ rotating user agents, proxy rotation, content filter middleware, challenge detection (Cloudflare/Akamai), configurable request delays, and `robots.txt` compliance.

**Q: What is the difference between `domain_spider` and `js_domain_spider`?**
A: `domain_spider` makes simple HTTP requests (fast, low resource). `js_domain_spider` uses Playwright to open a real browser (slow, high resource) for JavaScript-heavy sites.

**Q: How is the parsed data eventually used?**
A: The `downstream_sync_worker` transforms parsed data and sends it to the external PHP database (`v7_crawler_live`) which powers the frontend dashboard.

**Q: How does graceful shutdown work?**
A: Workers listen for SIGTERM signals. When received, they finish current jobs, release reserved jobs back to the queue, save state, and exit cleanly. The `shutdown_crawler.py` script manages this process.

---

## Technology Stack Summary

```
Language:        Python 3.10
Crawling:        Scrapy 2.12
Queue:           Beanstalkd (via greenstalk 2.0.2)
Database:        MongoDB (via pymongo 4.6.1)
JS Rendering:    Playwright 1.40 + Chromium
HTTP Client:     requests 2.31 + curl_cffi 0.7 (browser impersonation)
HTML Parsing:    BeautifulSoup4 + lxml 4.9.3
File Storage:    Bunny CDN (via requests)
Containerization: Docker + Docker Compose
Monitoring:      psutil 5.9.5 (CPU, memory, disk)
Process Mgmt:    subprocess + signal handlers
```

---

## File Count Summary

| Directory | Files | Purpose |
|---|---|---|
| `config/` | 5 | Configuration |
| `crawler/spider_project/spiders/` | 5 | Web spiders |
| `crawler/spider_project/pipelines/` | 4 | Data pipelines |
| `crawler/spider_project/middlewares/` | 7 | Request/response middleware |
| `crawler/listener/` | 5 | Queue listeners |
| `crawler/broadcasting/` | 1 | Event broadcasting |
| `crawler/scripts/` | 2 | Crawl submission scripts |
| `parser/workers/` | 20 | Parser workers |
| `parser/dispatch/` | 1 | Job dispatch |
| `lib/queue/` | 3 | Queue management |
| `lib/storage/` | 3 | Data storage |
| `lib/renderers/` | 4 | JS renderers |
| `lib/utils/` | 10 | Utilities |
| `workers/` | 5 | System orchestration |
| `scripts/` | 14 | CLI tools |
| **TOTAL** | **~89 files** | |
