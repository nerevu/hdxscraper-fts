## UN OCHA FTS API Collector

Collector for the [Financial Tracking Service (FTS) API](https://fts.unocha.org/).

## Setup

    pip install -r requirements.txt

*local*

    manage setup
    manage init

*ScraperWiki Box*

    manage -m Scraper setup
    manage -m Scraper init

## Usage

*local*

    manage run

*ScraperWiki Box*

    manage -m Scraper run

The results will be stored in a SQLite database `scraperwiki.sqlite`.
