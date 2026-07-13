# Distributed Web Crawler (Scrapy + Beanstalkd + MongoDB)

A scalable, modular, distributed web crawler system. Handles large-scale domain and single-URL crawls, with robust parsing, queueing, monitoring, and JavaScript rendering.

---

## Features
- Distributed, horizontally scalable architecture
- Queue-based job distribution (Beanstalkd)
- Domain and single-URL crawls
- Sitemap and BFS crawling
- Proxy rotation and management
- JavaScript rendering (Playwright, Splash, Selenium, Puppeteer)
- Duplicate URL detection
- Monitoring, health checks, auto-restart
- Extensible parser worker system
- Docker Compose support for full stack

---

## Architecture & Flow

1. **Job Submission**: Submit crawl jobs via script/API → Beanstalkd queue
2. **Queue Listener**: Picks up jobs, launches Scrapy spiders
3. **Crawler**: Crawls pages, stores HTML, enqueues parse jobs
4. **Parser Workers**: Specialized workers extract data from HTML (see `parser/workers/`)
5. **Monitor Worker**: Monitors queue, system health, logs metrics
6. **Integration Service**: Orchestrates all workers, restarts on failure, health checks

**Key Components:**
- `workers/integration_service.py`: Orchestrates all workers, health checks, restarts
- `workers/worker_manager.py`: Starts/stops/monitors worker processes
- `workers/monitor_worker.py`: Monitors queue and system health
- `parser/workers/`: Specialized HTML/data extractors (JS, AMP, links, images, etc)
- `lib/queue/`: QueueManager, Beanstalkd client, job serialization
- `lib/storage/`: MongoDB client, file storage, state manager
- `lib/renderers/`: Playwright, Splash, Selenium, Puppeteer support
- `lib/utils/`: Logging, health checks, URL/proxy/sitemap utilities
- `crawler/`: Scrapy project, spiders, pipelines, middlewares
- `scripts/`: Job submission, status, setup, integration runner
- `config/`: All settings, logging, proxies
- `data/`: HTML and logs

---

## Quickstart

### Prerequisites
- Python 3.8+
- MongoDB
- Beanstalkd
- Scrapy 2.12+
- (Optional) Splash, Playwright, Selenium, Puppeteer for JS rendering

### Installation
```bash
git clone https://github.com/yourusername/crawler_scrapy_distributed.git
cd crawler_scrapy_distributed
pip install -r requirements.txt
cp env.example .env  # Edit as needed
```

### Running the Full Stack (Recommended)
```bash
docker-compose up --build
```
This launches MongoDB, Beanstalkd, Splash, and all worker services. Logs are in `data/logs/`.

### Manual/Dev Run
```bash
./scripts/run_integration.sh
```
This starts all workers locally (Queue Listener, Crawler, Parser, Monitor).

---

## Usage

### Submitting Crawl Jobs
```bash
python scripts/submit_crawl_job.py --domain example.com --max-pages 500 --use-sitemap
python scripts/submit_crawl_job.py --url https://example.com/page --single-url
```
See `python scripts/submit_crawl_job.py --help` for all options.

### Monitoring & Status
```bash
python scripts/job_status.py list
python scripts/job_status.py status --status running
python scripts/job_status.py get <CRAWL_ID>
```
Logs: `data/logs/`
Job status script details: `scripts/README.md`

### Configuration
- `.env`: Main config (copied from `env.example`)
- `config/`: Python config files (settings, logging, proxies)

---

## Code Quality & Architecture

### Design Principles
The system is built with clean architecture principles, emphasizing separation of concerns and testability:

- **Explicit Parameter Passing**: Core functions use explicit parameters instead of namespace objects for clear interfaces
- **Encapsulation**: Business logic is decoupled from CLI parsing and framework dependencies
- **Testability**: Components can be easily mocked and tested in isolation
- **Configuration Management**: Centralized config with automatic fallbacks to sensible defaults

### Configuration System
- **Centralized Settings**: All configuration in `config/base_settings.py` with environment variable overrides
- **Smart Fallbacks**: Components automatically fall back to config defaults when parameters are not specified
- **Example**: `domains_collection` defaults to `MONGO_DOMAINS_COLLECTION` when not explicitly provided
- **Type Safety**: Clear parameter types throughout the codebase

## Extending the System
- **Add new parser workers**: Drop a new worker in `parser/workers/` (see existing ones for template)
- **Add new spiders**: Add to `crawler/spider_project/spiders/`
- **Add pipelines/middlewares**: `crawler/spider_project/pipelines/`, `crawler/spider_project/middlewares/`
- **Custom queue logic**: `lib/queue/`
- **Custom storage**: `lib/storage/`

---

## Project Structure (Key Parts)

```
config/           # All config (settings, logging, proxies)
crawler/          # Scrapy project, spiders, pipelines, middlewares
parser/workers/   # Specialized parser workers (JS, AMP, links, etc)
lib/queue/        # QueueManager, Beanstalkd client, job serialization
lib/storage/      # MongoDB client, file storage, state manager
lib/renderers/    # Playwright, Splash, Selenium, Puppeteer
lib/utils/        # Logging, health checks, URL/proxy/sitemap utils
workers/          # Integration service, worker manager, monitor
scripts/          # Job submission, status, setup, integration runner
data/             # HTML and logs
docker-compose.yml# Full stack orchestration
```

---

## Deployment & Operations

### Graceful Shutdown

The system is designed with graceful shutdown capabilities to prevent job loss during deployments and restarts.

#### Shutdown Script

Use `scripts/shutdown_crawler.py` for controlled shutdowns:

```bash
# Graceful shutdown (default, 120s grace period)
python scripts/shutdown_crawler.py

# Force shutdown (10s grace period)
python scripts/shutdown_crawler.py --mode force

# Emergency kill (immediate, may lose jobs)
python scripts/shutdown_crawler.py --mode emergency

# Docker container shutdown
python scripts/shutdown_crawler.py --docker --mode graceful
```

**Shutdown Modes:**
- **Graceful**: Workers finish current jobs, then exit (120s grace period)
- **Force**: Workers release jobs back to queue and exit quickly (10s grace period)
- **Emergency**: Immediate termination (use only in critical situations)

#### Restart Script

Use `scripts/restart_crawler.sh` for deployments:

```bash
# Graceful restart (recommended for production)
./scripts/restart_crawler.sh

# Force restart (quick, 10s grace)
./scripts/restart_crawler.sh --force

# Custom timeout
./scripts/restart_crawler.sh --timeout 60

# Emergency restart (immediate kill)
./scripts/restart_crawler.sh --emergency
```

The restart script:
1. Stops containers with appropriate grace period
2. Removes old containers and images
3. Rebuilds crawler image from scratch
4. Starts new containers

#### Worker Shutdown Behavior

Workers are designed to handle SIGTERM signals gracefully:
- **Crawl Job Listeners**: Release reserved jobs back to queue on shutdown
- **Parser Workers**: Complete current extraction tasks before exit
- **Integration Service**: Coordinates graceful shutdown of all child workers

#### Docker Configuration

```yaml
services:
  crawler:
    stop_grace_period: 120s  # 2 minutes for graceful shutdown
    stop_signal: SIGTERM     # Trigger graceful shutdown handlers
```

This ensures workers have sufficient time to:
- Finish processing current jobs
- Release reserved jobs back to Beanstalkd
- Save state and close connections cleanly

---

## Troubleshooting
- **Logs**: `data/logs/`
- **Health**: Monitor worker, integration service
- **Docker**: `docker-compose logs`
- **Mongo/Beanstalkd**: Check containers or local services
- **Stuck Jobs**: Check Beanstalkd stats with `scripts/job_status.py`
- **Worker Crashes**: Integration service auto-restarts workers
- **Graceful Shutdown Failed**: Use `--mode force` or check logs for blocking operations

---

## Contributing
- PRs welcome. Follow PEP8 and see `.clinerules` for style.

---

## License
MIT. See LICENSE file.