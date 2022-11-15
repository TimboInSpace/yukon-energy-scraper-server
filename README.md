# yukon-energy-scraper-server

## Installation
Install sqlite3
```
pip install sqlite3
```
Install selenium with firefox webdriver
```
pip install selenium
```
Obtain the firefox (Gecko) [webdriver](https://github.com/mozilla/geckodriver/releases). 
Follow the installation instructions to ensure the geckodriver is in your PATH.

## Usage
Gets data from an applet on a certain website, collects data into sqlite db, then serves data via http

## To-Do
- [x] Output scraped data to CSV format
- [x] Use headless web driver to reduce memory usage
- [x] Make server perform scraping periodically, without starting a new process