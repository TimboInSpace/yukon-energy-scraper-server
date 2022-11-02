# yukon-energy-scraper-server
Gets data from an applet on a certain website, collects data into sqlite db, then serves data via http

## Instructions
Download repository into a directory
Install dependencies:
```
pip install selenium
pip install sqlite3
```
Then run `server.py`. The program will scrape the current data from the target page, and record it in the database. 

Once it is done, the data will be displayed from the local webserver. To view the data collected, visit the webserver using a browser: [http://localhost:8080](http://localhost:8080)
