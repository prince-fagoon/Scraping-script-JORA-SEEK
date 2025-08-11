# Job Portal Scraper - Combined Edition

A modular job scraping system that collects sponsorship available jobs from multiple Australian job portals and combines them into a single CSV file.

## Features

- **Modular Design**: Base crawler class with portal-specific implementations
- **Multiple Sources**: Scrapes both Jora.com and Seek.com.au
- **Single Output**: All data combined into one `job_lists.csv` file
- **Source Tracking**: Each job entry includes the source portal
- **Robust Error Handling**: Continues scraping even if one portal fails

## File Structure

```
Job-details-Jora-Seek/
├── main.py                 # Entry point - run this to start scraping
├── base_crawler.py         # Base crawler class with common functionality
├── jora_crawler.py         # Jora.com specific crawler
├── seek_crawler.py         # Seek.com.au specific crawler
├── job_lists.csv           # Combined output file (generated)
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

## Installation

1. Install Python dependencies:

```bash
uv pip install -r requirements.txt
```

2. Ensure Chrome browser is installed (required for Selenium)

## Usage

Run the main scraper:

```bash
python main.py
```

This will:

1. Scrape Jora.com for sponsorship available jobs
2. Scrape Seek.com.au for sponsorship available jobs
3. Combine all data into `job_lists.csv`
4. Display summary statistics

## Output Format

The `job_lists.csv` file contains the following columns:

| Column      | Description                       |
| ----------- | --------------------------------- |
| source      | Portal name (Jora or Seek)        |
| title       | Job title                         |
| company     | Company name                      |
| location    | Job location                      |
| salary      | Salary information (if available) |
| description | Job description                   |
| job_url     | Direct link to the job posting    |

## Architecture

### BaseCrawler Class

- Contains common Selenium setup and utility methods
- Defines abstract methods that child classes must implement
- Handles common scraping workflow

### Portal-Specific Crawlers

- **JoraCrawler**: Implements Jora.com specific selectors and logic
- **SeekCrawler**: Implements Seek.com.au specific selectors and logic

### Main Entry Point

- Orchestrates both crawlers
- Combines and saves data
- Provides progress feedback

## Adding New Portals

To add a new job portal:

1. Create a new crawler class inheriting from `BaseCrawler`
2. Implement the required abstract methods:
   - `extract_job_details()`
   - `get_job_cards()`
   - `extract_job_url()`
   - `navigate_to_next_page()`
3. Add the new crawler to `main.py`

## Configuration

You can modify the number of pages to scrape by changing the `max_pages` parameter in `main.py`:

```python
jora_jobs = jora_crawler.scrape_jobs(max_pages=5)  # Scrape 5 pages
seek_jobs = seek_crawler.scrape_jobs(max_pages=5)  # Scrape 5 pages
```

## Error Handling

The system is designed to be robust:

- If one portal fails, the other continues
- Individual job scraping errors don't stop the entire process
- Detailed error messages help with debugging

## Requirements

- Python 3.7+
- Chrome browser
- Internet connection
- See `requirements.txt` for Python packages

## Notes

- The scrapers run in headless mode (no browser window)
- Random delays are included to avoid being blocked
- All data is saved with UTF-8 encoding
- The system automatically handles pagination for both portals
