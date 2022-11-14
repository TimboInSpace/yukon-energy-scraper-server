#!/usr/bin/python3
import sqlite3
import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

target_url = 'https://yukonenergy.ca/consumption/chart.php?chart=hourly&width=500&height=600'
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
    dt = datetime.datetime.strptime(s, format)
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
    fireFoxOptions = webdriver.FirefoxOptions()
    fireFoxOptions.add_argument('--headless')
    fireFoxOptions.add_argument('--window-size=1920x1080')
    driver = webdriver.Firefox(options=fireFoxOptions)
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
    return data

'''
Update the database with the data collected. Some of the data may have already been recorded. 
'''
def updateDB(data, conn):
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
    # Transfer the TEMP table to the main table
    # INSERT INTO DATA (timestamp, hydro, thermal) 
    # SELECT * FROM TEMP LEFT OUTER JOIN DATA ON DATA.timestamp = TEMP.timestamp WHERE TEMP.timestamp IS NULL
    # OR
    # INSERT OR IGNORE INTO DATA (timestamp, hydro, thermal) SELECT timestamp, hydro, thermal FROM TEMP
    q.execute(qryTransfer)
    # Drop the temp table
    q.execute(qryDropTemp)
    conn.commit()
    afterCount = countData(conn)
    print(f'Updated database: added {afterCount - beforeCount} records ({afterCount} total)')
    

'''
Return a count of the records in the database
'''
def countData(conn):
    q = conn.cursor()
    q.execute(qryCountData)
    (count,) = q.fetchone()
    return count

if __name__ == '__main__':
    print(f'Running scraper on {target_url}')
    db = sqlite3.connect('sql.db')
    data = getChartData(target_url)
    updateDB(data, db)