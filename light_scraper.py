import requests
import re
import ast
import sqlite3
from datetime import datetime, timezone

URL = "https://yukonenergy.ca/energy-in-yukon/electricity-101/electricity-generation"

# Define the queries
qryCreateTemp = '''CREATE TABLE TEMP (id INTEGER PRIMARY KEY, timestamp TIMESTAMP UNIQUE NOT NULL, hydro REAL NOT NULL, thermal REAL NOT NULL, wind REAL NOT NULL, solar REAL NOT NULL);'''
qryInsertTemp = '''INSERT INTO TEMP (timestamp, hydro, thermal, wind, solar) VALUES (?, ?, ?, ?, ?);'''
qryTransfer =   '''INSERT OR IGNORE INTO DATA (timestamp, hydro, thermal, wind, solar) SELECT timestamp, hydro, thermal, wind, solar FROM TEMP;'''
qryDropTemp =   '''DROP TABLE IF EXISTS TEMP;'''
qryCountData =  '''SELECT COUNT(*) FROM DATA;'''

def fetch_generation_data():
    # Fetch the data and read javascript straight from the HTTP body
    response = requests.get(URL)
    response.raise_for_status()
    html = response.text

    # Locate the tag "var rows_char_past_day = parseDates([ ... ])", which spans many lines!
    pattern = re.compile(
        r"var\s+rows_chart_past_day\s*=\s*parseDates\(\s*(\[[\s\S]*?\])\s*\);",
        re.MULTILINE,
    )
    match = pattern.search(html)
    if not match:
        #raise ValueError("Could not find rows_chart_past_day data")
        print("Couldnt find the data from the website! Skipping this one...")
        return []

    # Extract the list of js objects
    array_text = match.group(1)

    # ast.literal_eval does NOT accept functions, attributes, or other dangerous injectibles!
    # Therefore we can take advantage of similarity of Python and Javascript syntax *safely*
    data = ast.literal_eval(array_text)

    # Convert list of lists into list of dicts
    keys = ["timestamp", "hydro", "wind", "solar", "thermal"]
    parsed = [dict(zip(keys, row)) for row in data]
    return parsed

'''
Write the already-parsed data into the DB
Input: list of dicts with keys timestamp, hydro, thermal, wind, solar
Returns the number of new records added to the db
'''
def updateDB(data):
    with sqlite3.connect('./data/sql.db') as conn:
        beforeCount = countData(conn)
        # Get cursor from connection
        q = conn.cursor()
        # Drop the temp table (if it exists)
        q.execute(qryDropTemp)
        # Create the temp table
        q.execute(qryCreateTemp)
        # For each dictionary in data, insert another entry into the temp table
        for d in data:
            tup = (d['timestamp'], d['hydro'], d['thermal'], d['wind'], d['solar'])
            q.execute(qryInsertTemp, tup)
        conn.commit()
        # Start the second transaction
        q.execute(qryTransfer)
        # Drop the temp table
        q.execute(qryDropTemp)
        conn.commit()
        afterCount = countData(conn)
        print(f'Updated database: added {afterCount - beforeCount} records ({afterCount} total)')
        return (afterCount - beforeCount)


'''
Return a count of the records in the database
'''
def countData(conn):
    q = conn.cursor()
    q.execute(qryCountData)
    (count,) = q.fetchone()
    return count
    
    
'''
Add a line to the log file
'''
def logPrint(log_file_path, reported_current_time, update_count):
    with open(log_file_path, 'a') as f:
        current_utc_time = datetime.now(timezone.utc)
        formatted_time = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            f.write(f'[{formatted_time} UTC] Added {update_count} entries, reported at "{reported_current_time}"\n')
        except Exception as e:
            print(f'An error occurred while writing the log file:\n{e}')
    
    
'''
Return a datetime object of the current time, rounded to the last hour
'''
def lastHour():
    utc_now = datetime.now(timezone.utc)
    return utc_now.replace(minute=0, second=0, microsecond=0)
    
    
def scrapeAndUpdate():
    generation_data = fetch_generation_data()
    numrows = updateDB(generation_data)
    t = lastHour()
    logPrint('./data/scrape.log', t, numrows)
    

if __name__ == "__main__":
    scrapeAndUpdate()
