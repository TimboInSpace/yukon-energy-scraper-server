from flask import Flask, request, send_file, render_template
import sqlite3
import csv
import os
import uuid
import time
import threading
from scraper import scrapeAndUpdate


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
        fields = ['timestamp', 'hydro', 'thermal']
        writer = csv.DictWriter(csvfile, fieldnames=fields)
        # Write the header
        writer.writeheader()
        # Write the rows
        for x in data:
            writer.writerow({'timestamp':x[1], 'hydro':x[2], 'thermal':x[3]})
            

def recursive_scrape_data():
    scrapeAndUpdate()
    Timer(60*60*3, recursive_scrape_data).start()


@app.route('/', methods=['GET'])
def index():
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    try:
        # Query the data table
        cursor.execute("SELECT timestamp, hydro, thermal FROM data ORDER BY timestamp DESC LIMIT 3000")
        table_data = cursor.fetchall()
        chart_data = {
            "timestamps": [row[0] for row in table_data],
            "hydro": [row[1] for row in table_data],
            "thermal": [row[2] for row in table_data],
        }
    finally:
        # Close the database connection
        conn.close()

    return render_template('index.html', table_data=table_data, chart_data=chart_data)


@app.route('/generate-csv', methods=['POST'])
def generate_csv():
    # Generate a unique UUID
    file_uuid = str(uuid.uuid4())
    file_path = f"csv/{file_uuid}.csv"
    conn = sqlite3.connect('sql.db')
    cursor = conn.cursor()
    try:
        # Query the data table
        cursor.execute("SELECT * FROM data")
        rows = cursor.fetchall()
        fields = [description[0] for description in cursor.description]
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
    app.run(debug=False)

