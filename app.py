from flask import Flask, request, send_file, render_template
import sqlite3
import csv
import os
import uuid
import time
import threading
from light_scraper import scrapeAndUpdate


app = Flask(__name__)


def delete_csv_files(directory='./csv'):
    if not os.path.exists(directory):
        print(f"The directory '{directory}' does not exist.")
        return
    for f in os.listdir(directory):
        fp = os.path.join(directory, f)
        if f.endswith('.csv') and os.path.isfile(fp):
            try:
                os.remove(fp)
                print(f"Deleted: {fp}")
            except OSError as e:
                print(f"Error deleting file {fp}: {e}")


def dump_csv(data, file_path):
    with open(file_path, 'w', newline='') as csvfile:
        fields = ['timestamp', 'hydro', 'thermal', 'wind', 'solar']
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        # Write the header
        writer.writeheader()
        # Write the rows
        for x in data:
            writer.writerow({'timestamp':x[1], 'hydro':x[2], 'thermal':x[3], 'wind':x[4], 'solar':x[5]})
            

def recursive_scrape_data():
    scrapeAndUpdate()
    threading.Timer(60*60*12, recursive_scrape_data).start()


@app.route('/', methods=['GET'])
def index():
    conn = sqlite3.connect('./data/sql.db')
    cursor = conn.cursor()
    try:
        # Query the data table
        cursor.execute("SELECT * FROM (SELECT timestamp, hydro, thermal, wind, solar FROM data ORDER BY timestamp DESC LIMIT 2232) ORDER BY timestamp ASC")
        table_data = cursor.fetchall()
        chart_data = {
            "timestamps": [row[0] for row in table_data],
            "hydro": [row[1] for row in table_data],
            "thermal": [row[2] for row in table_data],
            "wind": [row[3] for row in table_data],
            "solar": [row[4] for row in table_data],
        }
    finally:
        # Close the database connection
        conn.close()
    log_file = ['Failed to read scraper log. Please contact your administrator.']
    try:
        with open('./data/scrape.log', 'r') as f:
            log_file = f.readlines()
    except Exception as e:
        print(f'Filed to read scrape.log!')
    return render_template('index.html', table_data=table_data, chart_data=chart_data, log_file=log_file)


@app.route('/generate-csv', methods=['POST'])
def generate_csv():
    # Generate a unique UUID
    file_uuid = str(uuid.uuid4())
    file_path = f"csv/{file_uuid}.csv"
    conn = sqlite3.connect('./data/sql.db')
    cursor = conn.cursor()
    try:
        # Query the data table
        cursor.execute("SELECT * FROM data")
        rows = cursor.fetchall()
        fields = [description[0] for description in cursor.description]
        delete_csv_files('./csv')
        dump_csv(rows, file_path)
        return send_file(file_path, as_attachment=True), 201
    finally:
        # Close the database connection
        conn.close()
    
    return {"uuid": file_uuid}, 201


@app.route('/<uuid:file_uuid>', methods=['GET'])
def download_csv(file_uuid):
    file_path = f"csv/{file_uuid}.csv"
    if os.path.exists(file_path):
        return send_file(file_path, as_attachment=True)
    else:
        return {"error": "File not found"}, 404


if __name__ == '__main__':
    # Make sure the ./csv directory exists, at least when the server starts...
    os.makedirs("csv", exist_ok=True)
    # Scrape the data immediately. After that, it's on an "every 3 hours" schedule
    recursive_scrape_data()
    # Start up the http server
    app.run(debug=False, host="yukon-energy", port=5000)

