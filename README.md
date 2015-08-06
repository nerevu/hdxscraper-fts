## UN Habitat urbaninfo API Collector

Collector for the [urbaninfo API](http://www.devinfo.org/urbaninfo/libraries/aspx/RegDataQuery.aspx).

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
