#!/usr/bin/python3

import scraper
import sqlite3
import sys
import csv
from http.server import HTTPServer, SimpleHTTPRequestHandler
import time
import threading

target_url = 'https://yukonenergy.ca/consumption/chart.php?chart=hourly&width=500&height=600'

HOSTNAME = "localhost"
PORT = 8080
SCRAPER_INTERVAL = 60 * 60 * 3 # 3 hours, in seconds.

if (len(sys.argv) > 1 and int(sys.argv[1]) > 0):
    PORT = sys.argv[1]

class MyServer(SimpleHTTPRequestHandler):

    def read_html(self, filepath):
        try:
            with open(filepath, 'r') as f:
                contents = f.read()
        except Exception as e:
            contents = "File read error"
        return contents

    # def do_POST(self):
    #     if (self.path == '/login'):
    #         length = int(self.headers['Content-Length'])
    #         postData = urllib.parse.parse_qs(self.rfile.read(length).decode('utf-8'))
    #         print(f'Login attempted: ( {postData["username"][0]} : {postData["password"][0]} )')
    #         self.send_response(403, 'Forbidden')
    #         self.end_headers()
    #         self.wfile.write(b'No access! Go away!')
    #     else:
    #         self.send_response(404, "Not Found")
    #         self.end_headers()
    #         self.wfile.write(b'Invalid URL')
    
    def render_table(self, data):
        #rows = [f(x) for x in y if c]
        rows = [ f'<tr> <td>{x[1]}</td> <td>{x[2]}</td> <td>{x[3]}</td> </tr>' for x in data ]
        return f'<table> <tr> <th>Timestamp</th> <th>Hydro</th> <th>Thermal</th> </tr> {" ".join(rows)} </table>'

    def dump_csv(self, data):
        with open('data.csv', 'w', newline='') as csvfile:
            fields = ['timestamp', 'hydro', 'thermal']
            writer = csv.DictWriter(csvfile, fieldnames=fields)
            # Write the header
            writer.writeheader()
            # Write the rows
            for x in data:
                writer.writerow({'timestamp':x[1], 'hydro':x[2], 'thermal':x[3]}) 
    
    def do_GET(self):
        if (self.path == '/' or self.path.lower() == '/index.html'):
            html = self.read_html('index.html')
            q = db.cursor()
            q.execute('SELECT * FROM DATA')
            res = q.fetchall()
            table = self.render_table(res)
            html = html.replace('[##CONTENT##]', table, 1)
            self.send_response(200, 'OK')
            self.end_headers()
            self.wfile.write(bytes(html, 'utf-8'))
        elif (self.path.lower() == '/csv'):
            q = db.cursor()
            q.execute('SELECT * FROM DATA')
            res = q.fetchall()
            self.dump_csv(res)
            self.send_response(302, 'Found')
            self.send_header('Location', '/data.csv')
            self.end_headers()
            self.wfile.write(bytes('Redirecting you to the csv file...', 'utf-8'))
        elif (self.path.lower() == '/data.csv'):
            csv = bytes(self.read_html('data.csv'), 'utf-8')
            self.send_response(200, 'OK')
            self.send_header('Content-Type', 'text/csv')
            self.send_header('Content-Length', len(csv))
            self.end_headers()
            self.wfile.write(csv)
        else:
            self.send_response(404, 'Not found')
            self.end_headers()
            self.wfile.write(bytes('The requested page was not found.', 'utf-8'))

def scraper_worker(interval_seconds):
    thread_db_conn = sqlite3.connect('sql.db')
    while True:
        print(f'Scraping target: {target_url}')
        data = scraper.getChartData(target_url)
        scraper.updateDB(data, thread_db_conn)
        time.sleep(interval_seconds)

if __name__ == '__main__':
    print('Initializing server...')
    global db
    db = sqlite3.connect('sql.db')
    srv = HTTPServer( (HOSTNAME,PORT), MyServer)
    scraperThread = threading.Thread(target=scraper_worker, args=(SCRAPER_INTERVAL,), daemon=True)
    try:
        print(f'Server listening on port {PORT}')
        scraperThread.start()
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nClosing server.')
        srv.server_close()
        sys.exit(0)
