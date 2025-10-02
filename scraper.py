#!/usr/bin/python3
import sqlite3
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

my_tz = timezone(timedelta(hours=-7))  # MST

#target_url = 'https://yukonenergy.ca/consumption/chart.php?chart=hourly&width=500&height=600'
target_url = 'https://yukonenergy.ca/energy-in-yukon/electricity-101/electricity-generation'
target_xpath = '/html/body/div[2]/div/div[1]/div/div/table'

# Define the queries
qryCreateTemp = '''CREATE TABLE TEMP (id INTEGER PRIMARY KEY, timestamp TIMESTAMP UNIQUE NOT NULL, hydro REAL NOT NULL, thermal REAL NOT NULL);'''
qryInsertTemp = '''INSERT INTO TEMP (timestamp, hydro, thermal) VALUES (?, ?, ?);'''
qryTransfer =   '''INSERT OR IGNORE INTO DATA (timestamp, hydro, thermal) SELECT timestamp, hydro, thermal FROM TEMP;'''
qryDropTemp =   '''DROP TABLE IF EXISTS TEMP;'''
qryCountData =  '''SELECT COUNT(*) FROM DATA;'''


'''
Make a datetime object out of the two strings from the website
'''
def datetimeOf(strDate, strTime):
    # concatenate the two strings
    s = f'{strTime.upper()} {strDate}'
    # Accept this format: 9:00 PM Tuesday, November 1, 2022
    format = '%I:%M %p %A, %B %d, %Y'
    dt = datetime.strptime(s, format)
    return dt
    


'''
Make a datetime object out of the timestamp string and the current datetime
'''
def dataDatetime(time_str, dt):
    # Make a string out of the date part of the datetime object, dt
    dateStr = datetime.datetime.strftime(dt, '%A, %B %d, %Y')
    # create a new datetime, using the provided time_str
    t = datetimeOf(dateStr, time_str)
    # Compare time_str to dt. Is the hour later than the current hour?
    offsetTime = dt - datetime.timedelta(hours=1)
    if (t > offsetTime):
        t = t - datetime.timedelta(days=1)
    return t


'''
Make an array of dictionaries. Each dictionary represents one sample
'''
def getChartData(url):
    firefoxOptions = webdriver.FirefoxOptions()
    firefoxOptions.add_argument("--headless")
    firefoxOptions.add_argument("--no-sandbox")
    firefoxOptions.add_argument("--disable-dev-shm-usage")
    #service = Service("/app/geckodriver")
    service = Service("./geckodriver")
    #driver = webdriver.Firefox(options=firefoxOptions, service=Service('/snap/bin/geckodriver'))
    driver = webdriver.Firefox(options=firefoxOptions, service=service)
    driver.implicitly_wait(0.5)
    driver.get(url)
    # Get the current date/time
    eleTime = driver.find_element(By.CLASS_NAME, 'current_time')
    eleDate = driver.find_element(By.CLASS_NAME, 'current_date')
    # If we couldnt find the time/date, just give up now
    if eleTime is None or eleDate is None:
        print('Failed to find current date/time on page')
        return None
    # Parse the text into a datetime object
    cur_dt = datetimeOf(eleDate.get_attribute('innerText'), eleTime.get_attribute('innerText'))
    print(f'The current datetime is: {cur_dt}')

    # Get the table data
    table = driver.find_element(By.XPATH, target_xpath)
    rows = table.find_elements(By.TAG_NAME, 'tr')
    data = []
    # Read the table data into an array of dictionaries
    for row in rows:
        tds = row.find_elements(By.TAG_NAME, 'td')
        if (len(tds) >= 3):
            data.append({
                'timestr': tds[0].get_attribute('innerText'), 
                'hydro':tds[1].get_attribute('innerText'), 
                'thermal':tds[2].get_attribute('innerText')
            })
    data.pop(0) # ignore the first datum
    for d in data:
        d['timestamp'] = dataDatetime(d['timestr'], cur_dt)
    driver.quit()
    return (cur_dt, data)



def getChartData2(url):
    xpaths = {
        'hydro': '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[1]/ul/li[1]/p',
        'wind': '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[1]/ul/li[2]/p',
        'solar': '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[1]/ul/li[3]/p',
        'thermal': '/html/body/div[1]/div[2]/div[2]/div[2]/div[1]/div[1]/ul/li[4]/p'
    }
    

'''
Update the database with the data collected. Some of the data may have already been recorded. 
Do this by writing the data into a temp table, then transfering the temp table into the main table
See these queries:
 - qryDropTemp
 - qryCreateTemp
 - qryInsertTemp
 - qryTransfer
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
            tup = (d['timestamp'], d['hydro'], d['thermal'])
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
        current_utc_time = datetime.datetime.now(datetime.timezone.utc)
        formatted_time = current_utc_time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            f.write(f'[{formatted_time} UTC] Added {update_count} entries, reported at "{reported_current_time}"\n')
        except Exception as e:
            print(f'An error occurred while writing the log file:\n{e}')


'''
Single function to collect data and update the database
'''
def scrapeAndUpdate():
    (t, data) = getChartData(target_url)
    #update_count = updateDB(data)
    logPrint('./data/scrape.log', t, update_count)


if __name__ == '__main__':
    print(f'Running scraper on {target_url}')
    db = sqlite3.connect('./data/sql.db')
    (t, data) = getChartData(target_url)
    update_count = updateDB(data, db)
