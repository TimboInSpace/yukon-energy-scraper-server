import scraper
import sqlite3
import sys
#import cgi
#import urllib
from http.server import HTTPServer, SimpleHTTPRequestHandler

target_url = 'https://yukonenergy.ca/consumption/chart.php?chart=hourly&width=500&height=600'

HOSTNAME = "localhost"
PORT = 8080

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
    
    def do_GET(self):
        html = self.read_html('index.html')
        q = db.cursor()
        q.execute('SELECT * FROM DATA')
        res = q.fetchall()
        table = self.render_table(res)
        html = html.replace('[##CONTENT##]', table, 1)
        self.send_response(200, 'OK')
        self.end_headers()
        self.wfile.write(bytes(html, 'utf-8'))

if __name__ == '__main__':
    print('Initializing server...')
    global db
    db = sqlite3.connect('sql.db')
    data = scraper.getChartData(target_url)
    scraper.updateDB(data, db)
    srv = HTTPServer( (HOSTNAME,PORT), MyServer)
    try:
        print(f'Server listening on port {PORT}')
        srv.serve_forever()
    except KeyboardInterrupt:
        print('\nClosing server.')
        srv.server_close()
        sys.exit(0)
