## UN OCHA FTS API Collector

[HDX](https://data.hdx.rwlabs.org/) collector for the [Financial Tracking Service (FTS) API](https://fts.unocha.org/).

## Introduction

hdxscraper-fts operates in the following way:

- Downloads json data from the fts API for each country
- Extracts and normalizes the data
- Places the resulting data into the following database tables: `appeal`, `emergency`, and `cluster`

[View the live data](https://data.hdx.rwlabs.org/organization/ocha-fts)

## Setup

*local*

(You are using a [virtualenv](http://www.virtualenv.org/en/latest/index.html), right?)

    sudo pip install -r requirements.txt
    manage setup
    manage init

*ScraperWiki Box*

    make setup
    manage -m Scraper init

## Usage

*local*

    manage run

*ScraperWiki Box*

    manage -m Scraper run

The results will be stored in a SQLite database `scraperwiki.sqlite`.
